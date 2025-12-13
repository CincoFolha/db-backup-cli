from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

class BackupType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"

@dataclass
class DatabaseConfig:
    db_type: str
    host: str
    port: str
    username: str
    password: str
    database: str
    additional_params: Dict[str, Any] = None

@dataclass
class BackupMetadata:
    database_name: str
    backup_type: BackupType
    timestamp: str
    size_bytes: int
    checksum: str
    compressed: bool
    compression_type: Optional[str]
    storage_location: str


class DatabaseBackupBase(ABC):
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection = None

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def create_backup(self, backup_type: BackupType, output_path: str) -> BackupMetadata:
        pass

    @abstractmethod
    def restore_backup(self, backup_path: str, target_database: Optional[str] = None) -> bool:
        pass

    @abstractmethod
    def get_database_size(self) -> int:
        pass

    @abstractmethod
    def list_tables(self) -> List[str]:
        pass

    def validate_backup(self, backup_path: str) -> bool:
        import os
        return os.path.exists(backup_path) and os.path.getsize(backup_path) > 0
