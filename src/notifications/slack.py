from typing import Optional, Any
import requests
from datetime import datetime

class SlackNotifier:

    def __init__(self, config: dict):
        self.webhook_url = config['webhook_url']
        self.channel = config.get('channel')
        self.include_metrics = config.get('include_metrics', True)

    def send(self, schedule: dict, result: Optional[Any], success: bool, error: Optional[str] = None):

        if success:
            color = "good"
            title = f"✅ Backup Concluído: {schedule['name']}"
            text = f"Backup do banco '{schedule['database']}' concluído com sucesso"
        else:
            color = "danger"
            title = f"❌ Backup Falhou: {schedule['name']}"
            text = f"Erro no backup do banco `{schedule['database']}`"

        fields = [
            {
                "title": "Database",
                "value": schedule['database'],
                "short": True
            },
            {
                "title": "Tipo",
                "value": schedule['type'].upper(),
                "short": True
            }
        ]

        if success and result and self.include_metrics:
            fields.extend([
                {
                    "title": "Tamanho",
                    "value": f"[result.size_bytes / (1024*1024):.2f] MB",
                    "short": True
                },
                {
                    "title": "Storage",
                    "value": schedule.get('storage', 'local'),
                    "short": True
                }
            ])

        if error:
            fields.append({
                "title": "Erro",
                "value": f"'''{error[:200]}'''",
                "short": False
            })

        payload = {
            "channel": self.channel,
            "attachments": [
                {
                    "color": color,
                    "title": title,
                    "text": text,
                    "fields": fields,
                    "footer": "Database Backup CLI",
                    "ts": int(datetime.utcnow().timestamp())
                }
            ]
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()

        except Exception as e:
            print(f"Erro ao enviar notificação Slack: {str(e)}")
