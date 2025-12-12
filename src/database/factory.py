from typing import Dict, Type
from src.database.base import DatabaseBackupBase, DatabaseConfig
from src.database.mysql import MySQLBackup
from src.database.postgresql import PostgreSQLBackup

class DatabaseFactory:

    _registry: Dict[str, Type[DatabaseBackupBase]] = {
        "mysql": MySQLBackup,
        "postgresql": PostgreSQLBackup,
    }

    @classmethod
    def create(cls, config: DatabaseConfig) -> DatabaseBackupBase:
        db_type = config.db_type.lower()

        if db_type not in cls._registry:
            raise ValueError(
                f"Tipo de banco '{db_type}' não suportado."
                f"Tipos disponiveis: {', '.join(cls._registry.keys())}"
            )
        return cls._registry[db_type](config)

    @classmethod
    def register(cls, db_type: str, backup_class: Type[DatabaseBackupBase]):
        cls._registry[db_type] = backup_class

    @classmethod
    def supported_databases(cls) -> list:
        return list(cls._registry.keys())
