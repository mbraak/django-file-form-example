from django.apps import AppConfig


class UploadsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "uploads"

    def ready(self):
        # django-file-form writes tus chunks to MEDIA_ROOT/FILE_FORM_UPLOAD_DIR
        # but does not create that directory itself; make sure it exists.
        from django_file_form.django_util import get_upload_path

        get_upload_path().mkdir(parents=True, exist_ok=True)
