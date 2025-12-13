from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from typing import Any, Optional
import time

from src.core.config import ConfigManager
from src.backup.manager import BackupManager
from src.core.logger import BackupLogger

class BackupScheduler:

    def __init__(self, config_file: Optional[str] = None):
        self.config_manager = ConfigManager()
        self.scheduler = BackgroundScheduler()
        self.logger = BackupLogger()

        self.schedules = self.config_manager.get_schedules()
        self._setup_jobs()

    def _setup_jobs(self):
        for schedule in self.schedules:
            if not schedule.get('enabled', True):
                continue

            cron_expr = schedule['cron']
            trigger = CronTrigger.from_crontab(cron_expr)

            self.scheduler.add_job(
                func=self._execute_backup,
                trigger=trigger,
                args=[schedule],
                id=schedule['name'],
                name=schedule['name'],
                replace_existing=True
            )

            self.logger.info(
                f"Agendamento configurado: {schedule['name']} - {cron_expr}"
            )

    def _execute_backup(self, schedule: dict):
        try:
            self.logger.info(f"Iniciando backup agendado: {schedule['name']}")

            db_config = self.config_manager.get_database_config(schedule['database'])

            backup_manager = BackupManager(
                db_config,
                storage_type=schedule.get('storage', 'local'),
                compression=schedule.get('compression', 'gzip')
            )

            result = backup_manager.execute_backup(
                backup_type=schedule.get('type', 'full')
            )

            self.logger.info(
                f"Backup agendado concluído: {schedule['name']} - "
                f"{result.storage_location}"
            )

            self._send_notification(schedule, result, success=True)

        except Exception as e:
            self.logger.error(
                f"Erro no backup agendado '{schedule['name']}': {str(e)}"
            )
            self._send_notification(schedule, None, success=False, error=str(e))

    def _send_notification(self, schedule: dict, result: Optional[Any], success: bool, error: Optional[str] = None):
        
        notification_config = self.config_manager.get_notification_config()

        if not notification_config.get('enabled', False):
            return

        notify_on = notification_config.get('notify_on', ['failure'])

        if success and 'success' not in notify_on:
            return
        if not success and 'failure' not in notify_on:
            return
        
        # Implementar notificação Slack aqui
        # from src.notifications.slack import SlackNotifier
        # notifier = SlackNotifier(notification_config['slack'])
        # notifier.send(schedule, result, success, error)
    
    def start_daemon(self):
        """Inicia scheduler em modo daemon"""
        self.scheduler.start()
        self.logger.info("Scheduler iniciado em mode daemon")

        try:
            while True:
                time.sleep(60)
        except (KeyboardInterrupt, SystemExit):
            self.scheduler.shutdown()
            self.logger.info("Scheduler encerrado")

    def print_schedule(self):
        """Imprime agendamentos configurados"""
        print("\n📅 Agendamentos Configurados:\n")
        print(f"{'Nome':<30} {'Cron':<15} {'Database':<20} {'Tipo':<12} {'Status'}")
        print("-" * 90)

        for schedule in self.schedules:
            status = "✅ Ativo" if schedule.get('enabled', True) else "❌ Inativo"
            print(
                f"{schedule['name']:<30} "
                f"{schedule['cron']:<15} "
                f"{schedule['database']:<20} "
                f"{schedule['type']:<12} "
                f"{status}"
            )

    def print_next_runs(self, limit: int = 5):
        """Imprime próximas execuções"""
        jobs = self.scheduler.get_jobs()

        if not jobs:
            print("Nenhum agendamento ativo")
            return

        print(f"\n⏰ Próximas {limit} Execuções:\n")

        jobs_with_next_run = [
            (job, job.next_run_time) 
            for job in jobs 
            if getattr(job, "next_run_time", None) is not None
        ]

        if not jobs_with_next_run:
            print("Nenhuma execução futura calculada ainda")
            return

        jobs_with_next_run.sort(key=lambda x: x[1])

        for job, next_run in jobs_with_next_run[:limit]:
            if next_run.tzinfo:
                now = datetime.now(next_run.tzinfo)
            else:
                now = datetime.now()

            time_diff = next_run - now
            total_seconds = int(time_diff.total_seconds())

            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60

            print(f"  • {job.name}")
            print(f"    {next_run.strftime('%Y-%m-%d %H:%M:%S')} "
                  f"(em {hours}h {minutes}m)")
            print()
