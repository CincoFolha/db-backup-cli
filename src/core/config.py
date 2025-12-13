import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from src.database.base import DatabaseConfig
from src.storage.base import StorageConfig


class ConfigManager:

    def __init__(self, config_dir: str = 'config'):
        self.config_dir = Path(config_dir)

        load_dotenv()

        self.default_config = self._load_yaml(self.config_dir / 'default.yaml')
        self.databases_config = self._load_yaml(self.config_dir / 'databases.yaml')

    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        if not file_path.exists():
            return {}

        with open(file_path, 'r') as f:
            content = f.read()

            content = self._replace_env_vars(content)
            return yaml.safe_load(content)

    def _replace_env_vars(self, content: str) -> str:
        import re

        pattern = r'\$\{([^}]+)\}'

        def replacer(match):
            var_name = match.group(1)
            return os.getenv(var_name, '')

        return re.sub(pattern, replacer, content)

    def get_database_config(self, db_name: str) -> DatabaseConfig:
        if 'databases' not in self.databases_config:
            raise ValueError("Nenhum banco de dados configurado")

        if db_name not in self.databases_config['databases']:
            available = ', '.join(self.databases_config['databases'].keys())
            raise ValueError(
                f"Banco '{db_name}' não encontrado. "
                f"Disponiveis: {available}"
            )

        db_config = self.databases_config['databases'][db_name]

        return DatabaseConfig(
            db_type=db_config['type'],
            host=db_config['host'],
            port=int(db_config['port']),
            username=db_config['username'],
            password=db_config['password'],
            database=db_config['database'],
            additional_params=db_config.get('additional_params', {})
        )

    def get_storage_config(self, storage_type: str) -> StorageConfig:
        storage_configs = self.default_config.get('storage', {})

        if storage_type not in storage_configs:
            raise ValueError(f"Storage '{storage_type}' não configurado")

        return StorageConfig(
            storage_type=storage_type,
            config=storage_configs[storage_type]
        )

    def get_backup_config(self) -> Dict[str, Any]:
        return self.default_config.get('backup', {})

    def get_notification_config(self) -> Dict[str, Any]:
        return self.default_config.get('notifications', {})

    def get_schedules(self) -> list:
        return self.databases_config.get('schedules', [])

    def list_databases(self) -> list:
        if 'databases' not in self.databases_config:
            return []
        return list(self.databases_config['databases'].keys())
