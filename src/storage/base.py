from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from dataclasses import dataclass

@dataclass
class StorageConfig:
    storage_type: str
    config: Dict[str, Any]

@dataclass
class StoredFile:
    name: str
    path: str
    size_bytes: int
    created_at: str
    checksum: Optional[str] = None


class StorageBase(ABC):
    def __init__(self, config: StorageConfig):
        self.config = config

    @abstractmethod
    def upload(self, local_path: str, remote_path: str) -> bool:
        pass

    @abstractmethod
    def download(self, remote_path: str, local_path: str) -> bool:
        pass

    @abstractmethod
    def delete(self, remote_path: str) -> bool:
        pass

    @abstractmethod
    def list_files(self, prefix: Optional[str] = None) -> List[StoredFile]:
        pass

    @abstractmethod
    def exists(self, remote_path: str) -> bool:
        pass

    @abstractmethod
    def get_file_info(self, remote_path: str) -> Optional[StoredFile]:
        pass
