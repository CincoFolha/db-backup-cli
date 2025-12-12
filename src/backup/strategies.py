from abc import ABC, absractmethod
from typing import Optional
import os
import hashlib

class BackupStrategy(ABC):
    
    @abstractmethod
    def execute_backup(self, database, output_path: str) -> BackupMetadata:
        pass

    def calculate_checksum(self, file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


class FullBackupStrategy(BackupStrategy):

    def execute_backup(self, database, output_path: str) -> BackupMetadata:
        from datetime import datetime

        database.create_backup(BackupType.FULL, output_path)

        file_size = os.path.getsize(output_size)
        checksum = self.calculate_checksum(output_path)

        return BackupMetadata(
            database_name=database.config.database,
            backup_type=BackupType.FULL,
            timestamp=datetime.utcnow().isoformat(),
            size_bytes=file_size,
            checksum=checksum,
            compressed=False,
            compression_type=None,
            storage_location=output_path
        )


class IncrementalBackupStrategy(BackupStrategy):
    def __init__(self, last_backup_path: Optional[str] = None):
        self.last_backup_path = last_backup_path

    def execute_backup(self, database, output_path: str) -> BackupMetadata:
        raise NotImplementedError("Incremental backup depende do DBMS específico")


class DifferentialBackupStrategy(BackupStrategy):
    def __init__(self, base_backup_path: str):
        self.base_backup_path = base_backup_path

    def execute_backup(self, database, output_path: str) -> BackupMetadata:
        raise NotImplementedError("Differential backup depende do DBMS específico")
