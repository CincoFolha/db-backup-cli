import pymysql
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.database.base import (
        DatabaseBackupBase,
        DatabaseConfig,
        BackupMetadata,
        BackupType,
)

class MySQLBackup(DatabaseBackupBase):

    def connect(self) -> bool:
        try:
            self.connection = pymysql.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.consig.password,
                database=self.config.database,
                charset="utf8mb4",
                **(self.config.additional_params or {})
            )
            return True
        except Exception as e:
            raise ConnectionError(f"Falha ao conectar ao MySQL: {str(e)}")

    def test_connection(self) -> Dict[str, Any]:
        try:
            self.connect()

            with self.connection.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]

                cursor.execute(f"""
                    SELECT
                        SUM(data_length + index_length) / 1024 / 1024 as size_mb
                    FROM information_schema.TABLES
                    WHERE table_schema = '{self.config.database}'
                """)
                size_mb = cursor.fetchone()[0] or 0

                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM information_schema.TABLES
                    WHERE table_schema = '{self.config.database}'
                """)
                table_count = cursor.fetchone()[0]

            return {
                'success': True,
                'version': version,
                'size_mb': float(size_mb),
                'table_count': table_count,
                'database': self.config.database
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            self.disconnect()

    def disconnect(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None

    def create_backup(self, backup_type: BackupType, output_path: str) -> BackupMetadata:
        import hashlib
        import os

        try:
            cmd = [
                "mysqldump",
                f"--host={self.config.host}",
                f"--port={self.config.port}",
                f"--user={self.config.username}",
                f"--password={self.config.password}",
                "--single-transaction",
                "--routines",
                "--triggers",
                "--events",
            ]

            if backup_type == BackupType.FULL:
                cmd.append("--complete-insert")
                cmd.append("--extended-insert")
            elif backup_type == BackupType.INCREMENTAL:
                # MySQL não suporta incremental nativo via mysqldump
                # Requer binary logs - implementação futura
                raise NotImplementedError("Backup incremental requer configuração de binary logs")

            cmd.append(self.config.database)

            with open(output_path, 'w') as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True
                )

            if result.returncode != 0:
                raise RuntimeError(f"mysqldump falhou: {result.stderr}")

            sha256_hash = hashlib.sha256()
            with open(output_path, 'rb') as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            checksum = sha256_hash.hexdigest()

            return BackupMetadata(
                database_name=self.config.database,
                backup_type=backup_type,
                timestamp=datetime.utcnow().isoformat(),
                size_bytes=os.path.getsize(output_path),
                checksum=checksum,
                compressed=False,
                compression_type=None,
                storage_location=output_path
            )

        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise RuntimeError(f"Erro ao criar backup MySQL: {str(e)}")

    def restore_backup(self, backup_path: str, target_database: Optional[str] = None) -> bool:
        try:
            target_db = target_database or self.config.database

            cmd = [
                "mysql",
                f"--host={self.config.host}",
                f"--port={self.config.port}",
                f"--user={self.config.username}",
                f"--password={self.config.password}",
                target_db
            ]

            with open(backup_path, 'r') as f:
                result = subprocess.run(
                    cmd,
                    stdin=f,
                    stderr=subprocess.PIPE,
                    text=True
                )

            if result.returncode != 0:
                raise RuntimeError(f"Restore falhou: {result.stderr}")
            
            return True
        except Exception as e:
            raise RuntimeError(f"Erro ao restaurar backup: {str(e)}")

    def get_database_size(self) -> int:
        try:
            self.connect()
            with self.connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT SUM(data_length + index_length)
                    FROM information_schema.TABLES
                    WHERE table_schema = '{self.config.database}'
                """)
                size_bytes = cursor.fetchone()[0] or 0
            return int(size_bytes)
        finally:
            self.disconnect()

    def list_tables(self) -> List[str]:
        try:
            self.connect()
            with self.connection.cursor() as cursor:
                cursor.execute(f"SHOW TABLES FROM {self.config.database}")
                tables = [row[0] for row in cursor.fetchall()]
            return tables
        finally:
            self.disconnect()
