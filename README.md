# django-file-form example

A minimal Django project showing how to use
[django-file-form](https://github.com/mbraak/django-file-form): ajax (tus)
uploads with drag & drop, resumable chunked transfer and a fallback to plain
multipart posts when JavaScript is off.

## Run it

```sh
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Then open <http://127.0.0.1:8000/>.

| URL               | What it shows                                                |
| ----------------- | ------------------------------------------------------------ |
| `/simple/`        | Plain `forms.Form` with a single and a multiple upload field |
| `/documents/new/` | `ModelForm` that saves a `Document` plus `Attachment` rows   |
| `/`               | List of saved documents                                      |
| `/admin/`         | Django admin (`manage.py createsuperuser` first)             |

Run the tests with `python manage.py test`.

## Linting

The project uses [Ruff](https://docs.astral.sh/ruff/) for linting and
formatting, configured in `pyproject.toml`.

```sh
pip install -r requirements-dev.txt
ruff check .          # lint (add --fix to auto-fix)
ruff format .         # format
```

The GitHub Actions workflow in `.github/workflows/tests.yml` runs both Ruff
and the test suite on every push and pull request.

## How django-file-form is wired in

1. **`example_project/settings.py`**: add `django_file_form` to
   `INSTALLED_APPS`, set `MEDIA_ROOT`, optionally tune the `FILE_FORM_*`
   settings.
2. **`example_project/urls.py`**: `path("", include("django_file_form.urls"))`
   mounts the tus endpoint at `/upload/`.
3. **`uploads/forms.py`**: mix `FileFormMixin` into the form, use
   `UploadedFileField` / `MultipleUploadedFileField`, and call
   `delete_temporary_files()` after a successful save.
4. **`uploads/templates/uploads/base.html`** loads
   `file_form/file_form.css` and `file_form/file_form.js`;
   **`_upload_form.html`** calls `initUploadFields(formElement, options)`.
5. **`python manage.py migrate`** creates the `TemporaryUploadedFile` table.
6. **`uploads/apps.py`** creates `MEDIA_ROOT/temp_uploads/` on startup. The
   tus endpoint writes chunks there but does not create the directory itself.

Files uploaded through the widget land in `MEDIA_ROOT/temp_uploads/` until the
form is saved. Run `python manage.py delete_unused_files` periodically to clean
up uploads from abandoned forms.
