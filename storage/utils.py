import posixpath
from rest_framework.exceptions import ValidationError


def make_parent_dir(path: str) -> tuple[str, str]:
    """Разбивает путь на родительский каталог со слэшем и чистое имя сущности."""
    is_dir = path.endswith("/")
    clean_path = path.rstrip("/")

    parent_dir, name = posixpath.split(clean_path)
    normalized_parent = f"{parent_dir}/" if parent_dir else ""

    return (normalized_parent, name)


def _get_s3_key(user_id: int, path: str, file_path: str) -> str:
    """Формирует S3-ключ, сохраняя вложенные подпапки (например, при загрузке папок),

    но защищая от Path Traversal (../).
    """
    clean_file_path = str(file_path).replace("\\", "/").strip("/")

    normalized = posixpath.normpath(clean_file_path)

    parts = [p for p in normalized.split("/") if p and p != "."]
    if any(p == ".." for p in parts):
        raise ValidationError(
            detail={"message": "Недопустимый путь к файлу"}
        )

    safe_relative_file_path = "/".join(parts)
    if not safe_relative_file_path:
        raise ValidationError(detail={"message": "Некорректное имя файла"})

    clean_target_path = path.strip("/")
    if clean_target_path:
        full_relative_path = posixpath.join(
            clean_target_path, safe_relative_file_path
        )
    else:
        full_relative_path = safe_relative_file_path

    return build_s3_key(user_id, full_relative_path)

def build_s3_key(user_id: int, path: str, is_dir: bool = False) -> str:
    if is_dir:
        if path and not path.endswith("/"):
            path += "/"

    if path:
        return f"user-{user_id}-files/{path.lstrip('/')}"
    return f"user-{user_id}-files/"

def get_relative_path(s3_key: str, user_id: int) -> str:
    return s3_key.removeprefix(f"user-{user_id}-files/")