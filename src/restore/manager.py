from pathlib import Path
from typing import Optional, List
from datetime import datetime
import tempfile
import os

from src.database.base import DatabaseConfig
from src.database.factory import DatabaseFactory
from src.backup.compression import CompressionManager
from src.core.logger import BackupLogger

class RestoreManager:

    def __init__(self, db_config: DatabaseConfig):
        self.db_config = db_config
        self.database = DatabaseFactory.create(db_config)
        self.compression_manager = CompressionManager()
        self.logger = BackupLogger()

    def execute_restore(self, backup_path: str, 
            target_database: Optional[str] = None, 
            tables: Optional[List[str]] = None) -> bool:

        start_time = datetime.utcnow()
        temp_file = None

        try:
            if not Path(backup_path).exists():
                raise FileNotFoundError(f"Backup não encontrado: {backup_path}")

            self.logger.info(f"Iniciando restore de {backup_path}")

            if backup_path.endswith(('.gz', '.bz2', '.xz')):
                self.logger.info("Descomprimindo backup...")
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.sql')
                temp_file.close()

                self.compression_manager.decompress(backup_path, temp_file.name)
                restore_file = temp_file.name
            else:
                restore_file = backup_path

            self.database.connect()

            self.logger.info("Executando restore...")
            success = self.database.restore_backup(restore_file, target_database)

            if not success:
                raise RuntimeError("Restore falhou")

            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.log_restore(
                database=target_database or self.db_config.database,
                backup_file=backup_path,
                duration=duration,
                status='success'
            )

            return True
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.log_restore(
                database=target_database or self.db_config.database,
                backup_file=backup_path,
                duration=duration,
                status='failed',
                error=str(e)
            )
            raise
        finally:
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            self.database.disconnect()

