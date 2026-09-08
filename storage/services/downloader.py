import io
import zipfile

from .base import BaseS3Service
from .decorators import handle_s3_errors
from storage.utils import build_s3_key

class S3DownloadService(BaseS3Service):

    @handle_s3_errors
    def download_resource(self, user_id: int, path: str):
        is_dir = path.endswith("/")
        normal_path = build_s3_key(user_id, path, is_dir=is_dir)

        if is_dir:
            return self._download_directory_as_zip(normal_path, path)
        return self._download_single_file(normal_path, path)

    def _download_single_file(self, normal_path: str, raw_path: str):
        filename = raw_path.split("/")[-1]
        response = self.client.get_object(Bucket=self.bucket, Key=normal_path)
        return (response["Body"], filename)

    def _download_directory_as_zip(self, normal_path: str, raw_path: str):
        folder_name = raw_path.rstrip("/").split("/")[-1]
        filename = f"{folder_name}.zip"

        paginator = self.client.get_paginator("list_objects_v2")
        files = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=normal_path):
            files.extend(page.get("Contents", []))

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file in files:
                arcname = file["Key"].removeprefix(normal_path)
                if not arcname or file["Key"].endswith("/"):
                    continue
                obj_response = self.client.get_object(Bucket=self.bucket, Key=file["Key"])
                file_data = obj_response["Body"].read()
                zip_file.writestr(arcname, file_data)

        buffer.seek(0)
        return (buffer, filename)
