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


class S3UploadForm(FileFormMixin, forms.Form):
    """
    Same fields as ``SimpleUploadForm``, but the files go straight to S3.

    Setting ``s3_upload_dir`` switches the widget from tus to S3 multipart
    uploads. Files land in the bucket under
    ``FILE_FORM_UPLOAD_DIR/<s3_upload_dir>/`` and the bound form gets
    ``S3UploadedFileWithId`` objects (django-storages files) for them.
    """

    s3_upload_dir = "s3_example"

    description = forms.CharField(max_length=200)
    input_file = UploadedFileField(help_text="A single file.")
    other_files = MultipleUploadedFileField(
        required=False, help_text="Optional; several files."
    )

    def save(self):
        """
        Return what was uploaded. Each file is already in the bucket; ``size``
        is read from S3. ``delete_temporary_files()`` only removes tus uploads,
        so the objects stay under the temporary prefix: in a real project, move
        them to their final key or expire the prefix with a lifecycle rule.
        """
        files = [
            self.cleaned_data["input_file"],
            *(self.cleaned_data["other_files"] or []),
        ]
        return {
            "description": self.cleaned_data["description"],
            "files": [
                {"name": f.original_name, "key": f.name, "size": f.size} for f in files
            ],
        }


class AccessibilityDemoForm(FileFormMixin, forms.Form):
    documents = MultipleUploadedFileField(help_text="One or more files.")

    def save(self):
        names = [f.name for f in self.cleaned_data["documents"]]
        self.delete_temporary_files()
        return names
