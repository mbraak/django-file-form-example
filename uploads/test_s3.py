"""
Tests for the direct-to-S3 demo, against moto's in-process S3 mock.

They drive django-file-form's /s3upload/ endpoints the way file_form.js does.
Only the part upload itself is done with boto3 here: in the browser that is a
PUT to the presigned URL straight to the bucket, which never reaches Django.

Skipped unless ``requirements-s3.txt`` is installed.
"""

import json
import unittest
from importlib.util import find_spec
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.html import escape

from .s3 import DEFAULT_CORS_ORIGINS

HAS_S3_EXTRAS = all(find_spec(n) for n in ("boto3", "storages", "moto"))

if HAS_S3_EXTRAS:
    import boto3
    from moto import mock_aws

BUCKET = "test-bucket"
S3_SETTINGS = {
    "AWS_STORAGE_BUCKET_NAME": BUCKET,
    "AWS_S3_ENDPOINT_URL": None,
    "AWS_S3_REGION_NAME": "us-east-1",
    "AWS_ACCESS_KEY_ID": "testing",
    "AWS_SECRET_ACCESS_KEY": "testing",
}


@unittest.skipUnless(HAS_S3_EXTRAS, "requirements-s3.txt is not installed")
@override_settings(**S3_SETTINGS)
class S3UploadTests(TestCase):
    def setUp(self):
        mock = mock_aws()
        mock.start()
        self.addCleanup(mock.stop)

        self.s3 = boto3.client("s3", region_name="us-east-1")
        call_command("setup_s3_bucket", stdout=StringIO())

    def s3_upload(self, filename: str, content: bytes) -> dict:
        """Upload ``content`` like file_form.js does; return its ``-uploads`` entry."""
        response = self.client.post(
            reverse("s3_upload"),
            {
                "filename": filename,
                "contentType": "text/plain",
                "s3UploadDir": "s3_example",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        key, upload_id = response.json()["key"], response.json()["uploadId"]
        self.assertEqual(key, f"temp_uploads/s3_example/{filename}")

        response = self.client.get(
            reverse("sign_part_upload", args=[upload_id, 1]), {"key": key}
        )
        self.assertIn(upload_id, response.json()["url"])

        # The browser PUTs the part to the presigned URL; do it with boto3.
        part = self.s3.upload_part(
            Bucket=BUCKET, Key=key, UploadId=upload_id, PartNumber=1, Body=content
        )

        response = self.client.post(
            reverse("complete_multipart_upload", args=[upload_id]) + f"?key={key}",
            {"parts": [{"ETag": part["ETag"], "PartNumber": 1}]},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)

        return {
            "id": upload_id,
            "name": key,
            "original_name": filename,
            "size": len(content),
            "type": "s3",
        }

    def test_page_uses_s3_endpoint(self):
        response = self.client.get(reverse("s3_demo"))
        self.assertContains(response, 'name="s3_upload_dir" value="s3_example"')
        self.assertContains(
            response, f'name="upload_url" value="{reverse("s3_upload")}"'
        )

    def test_setup_command_sets_cors(self):
        rule = self.s3.get_bucket_cors(Bucket=BUCKET)["CORSRules"][0]
        self.assertEqual(rule["AllowedOrigins"], DEFAULT_CORS_ORIGINS)
        self.assertEqual(rule["ExposeHeaders"], ["ETag"])

        # Running it again (as after a moto restart) is fine.
        call_command(
            "setup_s3_bucket", "--origin=http://example.test", stdout=StringIO()
        )
        rule = self.s3.get_bucket_cors(Bucket=BUCKET)["CORSRules"][0]
        self.assertEqual(rule["AllowedOrigins"], ["http://example.test"])

    def test_form_with_s3_uploads(self):
        main = self.s3_upload("main.txt", b"main")
        others = [self.s3_upload("a.txt", b"aa"), self.s3_upload("b.txt", b"bbb")]

        response = self.client.post(
            reverse("s3_demo"),
            {
                "description": "hello",
                "form_id": "33333333-3333-3333-3333-333333333333",
                "input_file-uploads": json.dumps([main]),
                "other_files-uploads": json.dumps(others),
            },
            follow=True,
        )
        self.assertContains(
            response, "main.txt (4 bytes, s3 key temp_uploads/s3_example/main.txt)"
        )
        self.assertContains(response, "a.txt (2 bytes")
        self.assertContains(response, "b.txt (3 bytes")

        body = self.s3.get_object(Bucket=BUCKET, Key="temp_uploads/s3_example/a.txt")
        self.assertEqual(body["Body"].read(), b"aa")

    def test_same_filename_gets_a_new_key(self):
        first = self.s3_upload("same.txt", b"1")
        response = self.client.post(
            reverse("s3_upload"),
            {"filename": "same.txt", "contentType": "", "s3UploadDir": "s3_example"},
            content_type="application/json",
        )
        self.assertNotEqual(response.json()["key"], first["name"])

    def test_missing_required_file_shows_error(self):
        response = self.client.post(reverse("s3_demo"), {"description": "x"})
        self.assertFormError(
            response.context["form"], "input_file", "This field is required."
        )

    def test_file_list_is_empty_at_first(self):
        response = self.client.get(reverse("s3_demo"))
        self.assertContains(response, "No files uploaded yet.")

    def test_file_list_shows_uploads_with_presigned_links(self):
        self.s3_upload("old.txt", b"old")
        self.s3_upload("new.txt", b"newer")
        # Objects outside the demo's prefix are not listed.
        self.s3.put_object(Bucket=BUCKET, Key="elsewhere/other.txt", Body=b"x")

        response = self.client.get(reverse("s3_demo"))
        files = response.context["s3_files"]
        self.assertEqual({f["name"] for f in files}, {"old.txt", "new.txt"})
        self.assertEqual(
            [f["last_modified"] for f in files],
            sorted((f["last_modified"] for f in files), reverse=True),
        )
        self.assertContains(response, "temp_uploads/s3_example/")
        self.assertContains(response, "5\xa0bytes")
        self.assertNotContains(response, "other.txt")

        new = next(f for f in files if f["name"] == "new.txt")
        self.assertIn("/temp_uploads/s3_example/new.txt?", new["url"])
        self.assertRegex(new["url"], r"[?&](X-Amz-)?Signature=")
        self.assertContains(response, f'href="{escape(new["url"])}"')

    def test_file_list_reports_s3_errors(self):
        self.s3.delete_bucket_cors(Bucket=BUCKET)
        self.s3.delete_bucket(Bucket=BUCKET)

        response = self.client.get(reverse("s3_demo"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Could not list the bucket")
        self.assertContains(response, "NoSuchBucket")


@override_settings(AWS_STORAGE_BUCKET_NAME="")
class S3DisabledTests(TestCase):
    def test_page_explains_how_to_enable(self):
        response = self.client.get(reverse("s3_demo"))
        self.assertContains(response, "S3 uploads are turned off")
        self.assertNotContains(response, "initUploadFields")
