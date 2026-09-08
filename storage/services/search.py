from .base import BaseS3Service
from .decorators import handle_s3_errors
from ..dto import StorageItem
from ..utils import build_s3_key, get_relative_path, make_parent_dir


class S3SearchService(BaseS3Service):

    @handle_s3_errors
    def search_resource(self, user_id: int, query: str):
        user_prefix = build_s3_key(user_id, "", is_dir=True)
        paginator = self.client.get_paginator("list_objects_v2")

        raw_data = []
        for page in paginator.paginate(
                Bucket=self.bucket, Prefix=user_prefix
        ):
            raw_data.extend(page.get("Contents", []))

        return self._filter_objects(raw_data, query, user_id)

    @staticmethod
    def _filter_objects(keys: list[dict], query: str, user_id: int ) -> list[StorageItem]:
            filtered_items = []
            normalized_query = query.lower()
            root_prefix = build_s3_key(user_id, "", is_dir=True)

            for key in keys:
                raw_key = key.get("Key", "")
                # Пропускаем корневую папку пользователя
                if not raw_key or raw_key == root_prefix:
                    continue

                relative_path = get_relative_path(raw_key, user_id)
                parent_dir, file_name = make_parent_dir(relative_path)

                if file_name and normalized_query in file_name.lower():
                    is_directory = raw_key.endswith("/")
                    item = StorageItem(
                        path=parent_dir,
                        name=file_name,
                        size=None if is_directory else key.get("Size"),
                        type="DIRECTORY" if is_directory else "FILE",
                    )
                    filtered_items.append(item)

            return filtered_items