from pathlib import Path

from django.core.management.base import BaseCommand
from django.core.files import File
from django.core.files.storage import default_storage
from django.conf import settings


class Command(BaseCommand):
    help = "Quick smoke test for Supabase S3 upload"

    def add_arguments(self, parser):
        parser.add_argument(
            '--local-file',
            default='/home/nagy/Pictures/3.jpeg',
            help='Absolute local file path to upload.',
        )
        parser.add_argument(
            '--remote-prefix',
            default='test_uploads',
            help='Remote folder/prefix in storage backend.',
        )

    def handle(self, *args, **options):
        local_file = Path(options['local_file'])
        remote_prefix = options['remote_prefix'].strip('/')
        backend_name = f"{default_storage.__class__.__module__}.{default_storage.__class__.__name__}"

        self.stdout.write(f"Storage backend: {backend_name}")
        if 's3' in backend_name.lower():
            self.stdout.write(
                f"S3 bucket: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'N/A')}"
            )
            self.stdout.write(
                f"S3 endpoint: {getattr(settings, 'AWS_S3_ENDPOINT_URL', 'N/A')}"
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    'WARNING: You are using local FileSystemStorage, not S3.'
                )
            )

        if not local_file.exists() or not local_file.is_file():
            raise FileNotFoundError(f'Local file not found: {local_file}')

        file_name = f"{remote_prefix}/{local_file.name}" if remote_prefix else local_file.name

        self.stdout.write(f"⏳ Uploading local file: {local_file}")
        try:
            with local_file.open('rb') as source:
                saved_path = default_storage.save(file_name, File(source, name=local_file.name))
            self.stdout.write(self.style.SUCCESS(f"✅ Uploaded: {saved_path}"))

            url = default_storage.url(saved_path)
            self.stdout.write(self.style.SUCCESS(f"✅ Public URL: {url}"))

            # Verify the file exists
            exists = default_storage.exists(saved_path)
            self.stdout.write(
                self.style.SUCCESS(f"✅ Exists check: {exists}")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Upload failed: {e}"))
            self.stdout.write(
                self.style.WARNING(
                    "Check your AWS_* / S3 environment variables."
                )
            )
            raise
