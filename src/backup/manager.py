from typing import Optional, List
from pathlib import Path
import os
from datetime import datetime

from src.database.base import DatabaseConfig, BackupMetadata, BackupType
from src.database.factory import DatabaseFactory
from src.backup.compression import CompressionManager
from src.storage.factory import StorageFactory
from src.core.logger import BackupLogger

class BackupManager:

    def __init__(self, db_config: DatabaseConfig, storage_type: str = 'local',
            compression: str = 'gzip'):
        self.db_config = db_config
        self.database = DatabaseFactory.create(db_config)
        self.storage = StorageFactory.create(storage_type)
        self.compression_manager = CompressionManager(compression)
        self.logger = BackupLogger()

    def execute_backup(self, backup_type: str, output_path: Optional[str] = None) -> BackupMetadata:

        start_time = datetime.utcnow()

        try:
            self.logger.info(f"Conectando ao banco {self.db_config.database}...")
            self.database.connect()

            if not output_path:
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                filename  = f"{self.db_config.database}_{backup_type}_{timestamp}.sql"
                output_path = Path("backups") / filename
                output_path.parent.mkdir(exist_ok=True)

            self.logger.info(f"Criando backup {backup_type}...")
            backup_type_enum = BackupType[backup_type.upper()]
            metadata = self.database.create_backup(backup_type_enum, str(output_path))

            if self.compression_manager.compression_type != 'none':
                self.logger.info("Comprimindo arquivo...")
                compressed_path = self.compression_manager.compress(str(output_path))
                os.remove(output_path)
                metadata.compressed = True
                metadata.compression_type = self.compression_manager.compression_type
                metadata.storage_location = compressed_path

            self.logger.info(f"Enviando para storage ({self.storage.config.storage_type})...")
            remote_path = Path(self.db_config.database) / Path(metadata.storage_location).name
            self.storage.upload(metadata.storage_location, str(remote_path))

            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.log_backup(metadata, duration, 'success')

            return metadata

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.log_backup(None, duration, 'failed', error=str(e))
            raise
        finally:
            self.database.disconnect()

    @staticmethod
    def list_backups(database: Optional[str] = None, limit: int = 10) -> List[BackupMetadata]:
        """Lista backups disponíveis"""
        # Implementação para listar backups do storage/logs
        pass
