from functools import wraps
from botocore.exceptions import ClientError

from storage.exceptions import ResourceNotFoundError, StorageServiceError


def handle_s3_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ClientError as error:
            if error.response['Error']['Code'] in ("404", "NoSuchKey"):
                raise ResourceNotFoundError
            raise StorageServiceError(f"Ошибка S3: {error}")
    return wrapper