from dataclasses import dataclass
from typing import Optional


@dataclass
class StorageItem:
    path: str
    name: str
    type: str
    size: Optional[int] = None