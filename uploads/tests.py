"""
End-to-end tests that drive the tus upload endpoint the way file_form.js does,
then submit the form with the resulting form_id.
"""

import base64
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django_file_form.django_util import get_upload_path
from django_file_form.models import TemporaryUploadedFile

from .models import Document

TEMP_MEDIA_ROOT = tempfile.mkdtemp(prefix="dff-example-test-")


def tus_upload(client: Client, form_id: str, field_name: str, filename: str, content: bytes):
    """Upload ``content`` via the tus protocol, as the JavaScript widget does."""

    def b64(value: str) -> str:
        return base64.b64encode(value.encode()).decode()

    metadata = ",".join(
        [
            f"filename {b64(filename)}",
            f"fieldName {b64(field_name)}",
            f"formId {b64(form_id)}",
        ]
    )
    response = client.post(
        reverse("tus_upload"),
        headers={
            "Tus-Resumable": "1.0.0",
            "Upload-Length": str(len(content)),
            "Upload-Metadata": metadata,
        },
    )
    assert response.status_code == 201, response.content
    location = response["Location"]

    response = client.patch(
        location,
        data=content,
        content_type="application/offset+octet-stream",
        headers={"Tus-Resumable": "1.0.0", "Upload-Offset": "0"},
    )
    assert response.status_code == 204, response.content


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TusFlowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The overridden MEDIA_ROOT is empty; the tus endpoint needs the
        # temp upload directory to exist (see UploadsConfig.ready).
        get_upload_path().mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_render(self):
        for name in ["document_list", "document_create", "simple_upload"]:
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("document_create"))
        self.assertContains(response, 'name="form_id"')
        self.assertContains(response, "initUploadFields")
        self.assertContains(response, "file_form/file_form.js")

    def test_simple_form_with_tus_uploads(self):
        form_id = "11111111-1111-1111-1111-111111111111"
        tus_upload(self.client, form_id, "input_file", "main.txt", b"main")
        tus_upload(self.client, form_id, "other_files", "a.pdf", b"a")
        tus_upload(self.client, form_id, "other_files", "b.pdf", b"b")
        self.assertEqual(TemporaryUploadedFile.objects.count(), 3)

        response = self.client.post(
            reverse("simple_upload"),
            {"description": "hello", "form_id": form_id},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "main.txt")
        self.assertContains(response, "a.pdf")
        self.assertContains(response, "b.pdf")
        # delete_temporary_files() removed the temporary copies.
        self.assertEqual(TemporaryUploadedFile.objects.count(), 0)

    def test_model_form_with_tus_uploads(self):
        form_id = "22222222-2222-2222-2222-222222222222"
        tus_upload(self.client, form_id, "main_file", "report.txt", b"report")
        tus_upload(self.client, form_id, "attachments", "one.txt", b"1")
        tus_upload(self.client, form_id, "attachments", "two.txt", b"2")

        response = self.client.post(
            reverse("document_create"), {"title": "Report", "form_id": form_id}
        )
        document = Document.objects.get()
        self.assertRedirects(response, reverse("document_detail", args=[document.pk]))
        self.assertEqual(document.title, "Report")
        self.assertTrue(document.main_file.name.startswith("documents/report"))
        self.assertEqual(document.main_file.read(), b"report")
        self.assertCountEqual(
            [a.file.read() for a in document.attachments.all()], [b"1", b"2"]
        )
        self.assertEqual(TemporaryUploadedFile.objects.count(), 0)

    def test_model_form_without_javascript(self):
        """A regular multipart post (no tus) still works."""
        response = self.client.post(
            reverse("document_create"),
            {
                "title": "Plain",
                "main_file": SimpleUploadedFile("plain.txt", b"plain"),
                "attachments": [
                    SimpleUploadedFile("x.txt", b"x"),
                    SimpleUploadedFile("y.txt", b"y"),
                ],
            },
        )
        document = Document.objects.get()
        self.assertRedirects(response, reverse("document_detail", args=[document.pk]))
        self.assertEqual(document.attachments.count(), 2)

    def test_missing_required_file_shows_error(self):
        response = self.client.post(reverse("document_create"), {"title": "No file"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Document.objects.exists())
        self.assertFormError(response.context["form"], "main_file", "This field is required.")
