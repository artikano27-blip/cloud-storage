from botocore.exceptions import ClientError
from django.conf import settings
import boto3

def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

class BaseS3Service:

    def __init__(self):
        self.bucket = settings.AWS_STORAGE_BUCKET_NAME
        self.client = get_s3_client()

    @staticmethod
    def _is_precondition_failed(error: ClientError) -> bool:
        code = error.response.get("Error", {}).get("Code")
        status = error.response.get("ResponseMetadata", {}).get(
            "HTTPStatusCode"
        )
        return code in ("PreconditionFailed", "412") or status == 412

    def _delete_objects_batch(self, keys: list[dict]) -> None:
        delete_list = [{"Key": k["Key"]} for k in keys if "Key" in k]
        for i in range(0, len(delete_list), 1000):
            batch = delete_list[i: i + 1000]
            self.client.delete_objects(
                Bucket=self.bucket,
                Delete={"Objects": batch},
            )

    def _file_exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
                return False
            raise

    def _folder_exists(self, key: str) -> bool:
        if not key.endswith("/"):
            key = f"{key}/"
        response = self.client.list_objects_v2(
            Bucket=self.bucket, Prefix=key, MaxKeys=1
        )
        return response.get("KeyCount", 0) > 0