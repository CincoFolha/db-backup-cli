import re
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
                filename  = f"{self.db_config.database}-{backup_type}-{timestamp}.sql"
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
        logger = BackupLogger()        
        logger.info(f"Iniciando listagem de backups (database='{database or 'todos'}', limit={limit})")

        search_path = Path("./backups")
        if database:
            search_path = search_path / database
        backups = []

        if not search_path.exists():
            logger.warning(f"Diretório de backups não encontrado: {search_path}")
            return backups

        pattern = re.compile(
            r"^([^-]+)-([^-]+)-(\d{8})_(\d{6})\.([^.]+)(\.gz|\.zip)?$"
        )

        for file_path in search_path.iterdir():
            if not file_path.is_file():
                continue

            match = pattern.match(file_path.name)
            if not match:
                continue

            db_name, backup_type_str, date_str, _, _, compression_ext = match.groups()
            
            if database and db_name != database:
                continue

            try:
                timestamp = datetime.strptime(date_str, "%Y%m%d").strftime("%d/%m/%Y")
            except ValueError:
                continue

            compressed = bool(compression_ext)

            backups.append(BackupMetadata(
                database_name=db_name,
                backup_type=BackupType(backup_type_str),
                timestamp=timestamp,
                size_bytes=file_path.stat().st_size,
                checksum="",
                compressed=compressed,
                compression_type=compression_ext.lstrip(".") if compressed else "",
                storage_location=str(file_path.parent)
            ))

        backups.sort(key=lambda b: datetime.strptime(b.timestamp, "%d/%m/%Y"), reverse=True)
        logger.info(f"Listagem concluida: {len(backups)} backup(s) encontrado(s)")

        return backups[:limit]
