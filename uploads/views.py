from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, FormView, ListView

from .forms import DocumentForm, SimpleUploadForm
from .models import Document


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
