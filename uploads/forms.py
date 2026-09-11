"""
Two ways of using django-file-form:

* ``SimpleUploadForm`` is a plain ``forms.Form``. The view decides what to do
  with the uploaded files.
* ``DocumentForm`` is a ``ModelForm``. Its ``save`` stores the main file on
  the model and creates an ``Attachment`` per extra file.

In both cases the form must:

1. Mix in ``FileFormMixin``. It adds the hidden ``form_id`` and ``upload_url``
   inputs the JavaScript widget needs and looks up files that were already
   uploaded via tus when the form is bound.
2. Use ``UploadedFileField`` / ``MultipleUploadedFileField`` instead of
   Django's ``FileField``.
3. Call ``delete_temporary_files()`` after a successful save, so the temporary
   copies in ``MEDIA_ROOT/temp_uploads`` are removed.
"""

from django import forms
from django_file_form.forms import (
    FileFormMixin,
    MultipleUploadedFileField,
    UploadedFileField,
)

from .models import Attachment, Document


class SimpleUploadForm(FileFormMixin, forms.Form):
    description = forms.CharField(max_length=200)
    input_file = UploadedFileField(help_text="A single file.")
    other_files = MultipleUploadedFileField(
        required=False,
        accept="image/*,.pdf",
        help_text="Optional; several files, images or PDFs only.",
    )

    def save(self):
        """Return a summary of what was uploaded, then clean up."""
        summary = {
            "description": self.cleaned_data["description"],
            "input_file": self.cleaned_data["input_file"].name,
            "other_files": [f.name for f in self.cleaned_data["other_files"] or []],
        }
        self.delete_temporary_files()
        return summary


class DocumentForm(FileFormMixin, forms.ModelForm):
    attachments = MultipleUploadedFileField(required=False)

    class Meta:
        model = Document
        fields = ["title", "main_file"]
        field_classes = {"main_file": UploadedFileField}

    def save(self, commit=True):
        document = super().save(commit=commit)

        if commit:
            for uploaded_file in self.cleaned_data["attachments"] or []:
                Attachment.objects.create(document=document, file=uploaded_file)

            self.delete_temporary_files()

        return document
