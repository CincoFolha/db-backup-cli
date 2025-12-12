import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from loguru import logger

class BackupLogger:

    def __init__(self, log_file: str = 'logs/backup.log'):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            self.log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            rotation="10 MB",
            retention="30 days",
            compression="zip"
        )

    def log_backup(self, metadata: Optional[Any], duration: float, status: str, error: Optional[str] = None):

        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'operation': 'backup',
            'status': status,
            'duration_seconds': round(duration, 2)
        }

        if metadata:
            log_entry.update({
                'database': metadata.database_name,
                'type': metadata.backup_type.value,
                'size_mb': round(metadata.size_bytes / (1024 * 1024), 2),
                'storage': metadata.storage_location,
                'checksum': metadata.checksum[:16]
            })

        if error:
            log_entry['error'] = error

        log_msg = json.dumps(log_entry)

        if status == 'success':
            logger.success(log_msg)
        else:
            logger.error(log_msg)

    def log_restore(self, database: str, backup_file: str, duration: float, status: str, error: Optional[str] = None):

        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'operation': 'restore',
            'database': database,
            'backup_file': backup_file,
            'duration_seconds': round(duration, 2),
            'status': status
        }

        if error:
            log_entry['error'] = error

        log_msg = json.dumps(log_entry)
        
        if status == 'success':
            logger.success(log_msg)
        else:
            logger.error(log_msg)

    def info(self, message: str, **kwargs):
        logger.info(message, **kwargs)

    def error(self, message: str, **kwargs):
        logger.error(message, **kwargs)

    def warning(self, message: str, **kwargs):
        logger.warning(message, **kwargs)


def get_recent_logs(log_file: str = 'logs/backup.log', limit: int = 10) -> List[Dict[str, Any]]:
    
    log_path = Path(log_file)

    if not log_path.exists():
        return []

    logs = []
    with open(log_path, 'r') as f:
        lines = f.readlines()

        for line in reversed(lines[-limit*2:]):
            try:
                if '{' in line and '}' in line:
                    json_str = line[line.index('{'):line.rindex('}')+1]
                    log_entry = json.loads(json_str)
                    logs.append(log_entry)

                    if len(logs) >= limit:
                        break
            except:
                continue
    return logs
