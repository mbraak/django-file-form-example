from django.core.management.base import BaseCommand, CommandError

from uploads.s3 import DEFAULT_CORS_ORIGINS, cors_configuration, s3_uploads_enabled


class Command(BaseCommand):
    help = (
        "Create the AWS_STORAGE_BUCKET_NAME bucket if needed and give it the CORS "
        "rule that browser uploads need. Run it again after restarting moto, "
        "which keeps everything in memory."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--origin",
            action="append",
            dest="origins",
            help=(
                "Browser origin allowed to upload; repeat for several. "
                f"Default: {', '.join(DEFAULT_CORS_ORIGINS)}."
            ),
        )

    def handle(self, *args, origins=None, **options):
        if not s3_uploads_enabled():
            raise CommandError(
                "Install requirements-s3.txt and set AWS_STORAGE_BUCKET_NAME first."
            )

        from django.conf import settings
        from django_file_form.s3_multipart.utils import get_bucket_name, get_client

        client = get_client()
        bucket = get_bucket_name()
        existing = {b["Name"] for b in client.list_buckets().get("Buckets", [])}

        if bucket in existing:
            self.stdout.write(f"Bucket '{bucket}' already exists.")
        else:
            kwargs = {"Bucket": bucket}
            region = settings.AWS_S3_REGION_NAME
            if region and region != "us-east-1":
                kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}
            client.create_bucket(**kwargs)
            self.stdout.write(f"Created bucket '{bucket}'.")

        origins = origins or DEFAULT_CORS_ORIGINS
        client.put_bucket_cors(
            Bucket=bucket, CORSConfiguration=cors_configuration(origins)
        )
        self.stdout.write(
            self.style.SUCCESS(f"Allowed uploads from: {', '.join(origins)}")
        )
