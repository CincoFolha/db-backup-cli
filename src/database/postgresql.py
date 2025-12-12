import psycopg2
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import os

from src.database.base import (
    DatabaseBackupBase,
    DatabaseConfig,
    BackupMetadata,
    BackupType,
)

class PostgreSQLBackup(DatabaseBackupBase):

    def connect(self) -> bool:
        try:
            self.connection = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password,
                database=self.config.database,
                **(self.config.additional_params or {})
            )
            return True
        except Exception as e:
            raise ConnectionError(f"Falha ao conectar ao PostgreSQL: {str(e)}")

    def test_connection(self) -> Dict[str, Any]:
        try:
            self.connect()

            with self.connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0].split(',')[0]

                cursor.execute(f"""
                    SELECT pg_database_size('{self.config.database}')
                """)
                size_bytes = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """)
                table_count = cursor.fetchone()[0]

            return {
                'success': True,
                'version': version,
                'size_mb': size_bytes / (1024 * 1024),
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
        try:
            env = os.environ.copy()
            env[PGPASSWORD] =  self.config.password

            cmd = [
                "pg_dump",
                f"--host={self.config.host}",
                f"--port={self.config.port}",
                f"--username={self.config.username}",
                "--format=custom",
                "--verbose",
                "--no-owner",
                "--no-acl",
            ]

            if backup_type == BackupType.FULL:
                cmd.extend(["--create", "--clean"])

            cmd.extend([
                f"--file={output_path}",
                self.config.database
            ])

            result = subprocess.run(
                cmd,
                env=env,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                raise RuntimeError(f"pg_dump falhou: {result.stderr}")
            
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
                compressed=True,
                compression_type="pg_dump_custom",
                storage_location=output_path
            )

        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise RuntimeError(f"Erro ao criar backup PostgreSQL: {str(e)}")

    def restore_backup(self, backup_path: str, target_database: Optional[str] = None) -> bool:
        try:
            target_db = target_database or self.config.database

            env = os.environ.copy()
            env["PGPASSWORD"] = self.config.password

            cmd = [
                "pg_restore",
                f"--host={self.config.host}",
                f"--port={self.config.port}",
                f"--username={self.config.username}",
                f"--dbname={target_db}",
                "--verbose",
                "--clean",
                "--if-exists",
                backup_path
            ]

            result = subprocess.run(
                cmd,
                env=env,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                raise RuntimeError(f"pg_restore falhou: {result.stderr}")

            return True

        except Exception as e:
            raise RuntimeError(f"Erro ao restaurar backup: {str(e)}")

    def get_database_size(self) -> int:
        try:
            self.connect()
            with self.connection.cursor() as cursor:
                cursor.execute(f"SELECT pg_database_size('{self.config.database}')")
                size_bytes = cursor.fetchone()[0]
            return int(size_bytes)
        finally:
            self.disconnect()

    def list_tables(self) -> List[str]:
        try:
            self.connect()
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                """)
                tables = [row[0] for row in cursor.fetchall()]
            return tables
        finally:
            self.disconnect()

