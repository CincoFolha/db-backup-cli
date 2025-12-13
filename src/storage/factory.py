from typing import Dict, Type
from src.storage.base import StorageBase, StorageConfig
from src.storage.local import LocalStorage
from src.storage.s3 import S3Storage
from src.core.config import ConfigManager

class StorageFactory:

    _registry: Dict[str, Type[StorageBase]] = {
        'local': LocalStorage,
        's3': S3Storage,
        # 'gcs': GCSStorage,
        # 'azure': AzureStorage,
    }

    @classmethod
    def create(cls, storage_type: str) -> StorageBase:
        
        storage_type = storage_type.lower()

        if storage_type not in cls._registry:
            raise ValueError(
                f"Tipo de storage '{storage_type}' não suportado. "
                f"Tipos disponiveis: {', '.join(cls._registry.keys())}"
            )

        config_manager = ConfigManager()
        storage_config = config_manager.get_storage_config(storage_type)

        return cls._registry[storage_type](storage_config)

    @classmethod
    def register(cls, storage_type: str, storage_class: Type[StorageBase]):
        cls._registry[storage_type] = storage_class

    @classmethod
    def supported_storages(cls) -> list:
        return list(cls._registry.keys())
