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
| `/accessibility/` | Demo of the keyboard and screen reader support               |
| `/s3/`            | Direct browser-to-S3 uploads (optional, see below)           |
| `/admin/`         | Django admin (`manage.py createsuperuser` first)             |

Run the tests with `python manage.py test`. The S3 tests are skipped unless
`requirements-s3.txt` is installed.

## Optional: direct uploads to S3

With `s3_upload_dir` set on a form, the widget sends files straight from the
browser to an S3 bucket as multipart uploads. Django only signs each part URL
at `/s3upload/`; the file data never passes through it. See `S3UploadForm` in
`uploads/forms.py`.

You don't need an AWS account to try it.
[moto](https://docs.getmoto.org/en/latest/docs/server_mode.html) runs a local
S3 server:

```sh
pip install -r requirements-s3.txt
moto_server -p 9000
```

In another shell:

```sh
export AWS_STORAGE_BUCKET_NAME=example
export AWS_S3_ENDPOINT_URL=http://127.0.0.1:9000
export AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test
python manage.py setup_s3_bucket
python manage.py runserver
```

Then open <http://127.0.0.1:8000/s3/>. Without `AWS_STORAGE_BUCKET_NAME` the
page explains how to turn the demo on.

Things to know:

- **CORS.** The browser uploads to a different origin (the bucket), and it has
  to read each part's `ETag` response header. `setup_s3_bucket` sets a CORS
  rule that allows the runserver origins and exposes `ETag`. Pass
  `--origin https://your.site` (repeatable) for other origins. A missing
  `ETag` exposure is the usual cause of failing uploads.
- **moto keeps everything in memory.** After restarting `moto_server`, run
  `setup_s3_bucket` again. Uploaded files are gone.
- **Uploaded objects are not cleaned up.** They stay under
  `temp_uploads/s3_example/` in the bucket. `delete_temporary_files()` and
  `delete_unused_files` only handle tus uploads. In a real project, copy them
  to their final key when saving the form, and expire the temporary prefix
  with a bucket lifecycle rule.
- **A real bucket** works the same way. Leave `AWS_S3_ENDPOINT_URL` unset,
  set `AWS_S3_REGION_NAME`, and use real credentials. Run `setup_s3_bucket`
  once, or add the same CORS rule yourself.

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
