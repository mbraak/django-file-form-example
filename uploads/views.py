from django.contrib import messages
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, FormView, ListView

from .forms import AccessibilityDemoForm, DocumentForm, S3UploadForm, SimpleUploadForm
from .models import Document
from .s3 import s3_uploads_enabled


class SimpleUploadView(FormView):
    template_name = "uploads/simple_form.html"
    form_class = SimpleUploadForm
    success_url = reverse_lazy("simple_upload")

    def form_valid(self, form):
        summary = form.save()
        names = ", ".join([summary["input_file"], *summary["other_files"]])
        messages.success(
            self.request, f"Received '{summary['description']}' with files: {names}"
        )
        return super().form_valid(form)


class DocumentCreateView(CreateView):
    template_name = "uploads/document_form.html"
    form_class = DocumentForm

    def get_success_url(self):
        return reverse_lazy("document_detail", kwargs={"pk": self.object.pk})


class DocumentListView(ListView):
    model = Document
    template_name = "uploads/document_list.html"


class DocumentDetailView(DetailView):
    model = Document
    template_name = "uploads/document_detail.html"


class S3UploadView(FormView):
    template_name = "uploads/s3_form.html"
    form_class = S3UploadForm
    success_url = reverse_lazy("s3_demo")

    def dispatch(self, request, *args, **kwargs):
        if not s3_uploads_enabled():
            # Explain how to turn the demo on instead of failing on upload.
            return render(request, "uploads/s3_disabled.html")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        summary = form.save()
        files = ", ".join(
            f"{f['name']} ({f['size']} bytes, s3 key {f['key']})"
            for f in summary["files"]
        )
        messages.success(
            self.request, f"Received '{summary['description']}' with files: {files}"
        )
        return super().form_valid(form)


class AccessibilityDemoView(FormView):
    template_name = "uploads/accessibility.html"
    form_class = AccessibilityDemoForm
    success_url = reverse_lazy("accessibility")

    def form_valid(self, form):
        names = form.save()
        messages.success(self.request, f"Received files: {', '.join(names)}")
        return super().form_valid(form)
