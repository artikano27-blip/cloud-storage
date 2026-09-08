def is_valid_path(path: str, allow_empty: bool = False) -> bool:
    if allow_empty:
        return bool(".." not in path)
    return bool(path and path.strip() and ".." not in path)
