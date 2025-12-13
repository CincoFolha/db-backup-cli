import boto3
from botocore.exceptions import ClientError
from typing import List, Optional
from datetime import datetime

from src.storage.base import StorageBase, StorageConfig, StoredFile

class S3Storage(StorageBase):

    def __init__(self, config: StorageConfig):
        super().__init__(config)

        self.bucket_name = config.config['bucket']
        self.prefix = config.config.get('prefix', '')

        self.s3_client = boto3.client(
            's3',
            region_name=config.config.get('region', 'us-east-1')
        )

    def upload(self, local_path: str, remote_path: str) -> bool:
        try:
            s3_key = f"{self.prefix}{remote_path}".lstrip('/')

            self.s3_client.upload_file(
                local_path,
                self.bucket_name,
                s3_kye,
                ExtraArgs={
                    'StorageClass': self.config.config.get('storage_class', 'STANDARD')
                }
            )

            return True
        except ClientError as e:
            raise RuntimeError(f"Erro ao fazer upload S3: {str(e)}")

    def download(self, remote_path: str, local_path: str) -> bool:
        try:
            s3_key = f"{self.prefix}{remote_path}".lstrip('/')

            self.s3_client.download_file(
                self.bucket_name,
                s3_key,
                local_path
            )

            return True
        except ClientError as e:
            raise RuntimeError(f"Erro ao fazer download S3: {str(e)}")

    def delete(self, remote_path: str) -> bool:
        try:
            s3_key = f"{self.prefix}{remote_path}".lstrip('/')

            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )

            return True
        except ClientError as e:
            raise RuntimeError(f"Erro ao deletar do S3: {str(e)}")

    def list_files(self, prefix: Optional[str] = None) -> List[StoredFile]:
        try:
            list_prefix = f"{self.prefix}{prefix or ''}".lstrip('/')

            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=list_prefix
            )

            files = []
            for obj in response.get('Contents', []):
                files.append(StoredFile(
                    name=obj['Key'].split('/')[-1],
                    path=obj['Key'].replace(self.prefix, '', 1),
                    size_bytes=obj['Size'],
                    created_at=obj['LastModified'].isoformat()
                ))

            return files
        except ClientError as e:
            raise RuntimeError(f"Erro ao listar arquivos S3: {str(e)}")

    def exists(self, remote_path: str) -> bool:
        try:
            s3_key = f"{self.prefix}{remote_path}".lstrip('/')

            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError:
            return False

    def get_file_info(self, remote_path: str) -> Optional[StoredFile]:
        try:
            s3_key = f"{self.prefix}{remote_path}".lstrip('/')

            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )

            return StoredFile(
                name=s3_key.split('/')[-1],
                path=remote_path,
                size_bytes=response['ContentLength'],
                created_at=response['LastModified'].isoformat()
            )
        except ClientError:
            return None


