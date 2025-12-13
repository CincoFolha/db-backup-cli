import os
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from src.storage.base import (
        StorageBase, 
        StorageConfig, 
        StoredFile
)

class LocalStorage(StorageBase):

    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.base_path = Path(config.config.get('base_path', '/backups'))
        self.base_path.mkdir(parents=True, exist_ok=True)

    def upload(self, local_path: str, remote_path: str) -> bool:
        try:
            dest_path = self.base_path / remote_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(local_path, dest_path)
            return True
        except Exception as e:
            raise RuntimeError(f"Erro ao fazer upload local: {str(e)}")

    def download(self, remote_path: str, local_path: str) -> bool:
        try:
            source_path = self.base_path / remote_path

            if not source_path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {remote_path}")

            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, local_path)
            return True
        except Exception as e:
            raise RuntimeError(f"Erro ao fazer download: {str(e)}")

    def delete(self, remote_path: str) -> bool:
        try:
            file_path = self.base_path / remote_path

            if file_path.exists():
                file_path.unlink()
                return True

            return False
        except Exception as e:
            raise RuntimeError(f"Erro ao deletar arquivo: {str(e)}")

    def list_files(self, prefix: Optional[str] = None) -> List[StoredFile]:
        try:
            search_path = self.base_path / prefix if prefix else self.base_path
            files = []

            if search_path.exists():
                for file_path in search_path.rglop('*'):
                    if file_path.is_file():
                        stat = file_path.stat()
                        relative_path = file_path.relative_to(self.base_path)

                        files.append(StoredFile(
                            name=file_path.name,
                            path=str(relative_path),
                            size_bytes=stat.st_size,
                            created_at=datetime.fromtimestamp(stat.st_ctime).isoformat()
                        ))
            return files
        except Exception as e:
            raise RuntimeError(f"Erro ao listar arquivos: {str(e)}")

    def exists(self, remote_path: str) -> bool:
        return (self.base_path / remote_path).exists()

    def get_file_info(self, remote_path: str) -> Optional[StoredFile]:
        file_path = self.base_path / remote_path

        if not file_path.exists():
            return None

        stat = file_path.stat()
        return StoredFile(
            name=file_path.name,
            path=remote_path,
            size_bytes=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime).isoformat()
        )
