import click
from typing import Optional
from pathlib import Path
import sys

@click.group()
@click.version_option(version='1.0.0')
def cli():
    pass

@cli.command()
@click.option('--db', required=True, help="Nome da configuração do banco de dados")
@click.option('--type', 'backup_type', type=click.Choice(['full', 'incremental', 'differential']),
        default='full', help='Tipo de backup')
@click.option('--storage', type=click.Choice(['local', 's3', 'gcs', 'azure']), 
        default='local', help='Provedor de armazenamento')
@click.option('--compress', type=click.Choice(['gzip', 'bz2', 'xz', 'none']), 
        default='gzip', help='Tipo de compressão')
@click.option('--output', help='Caminho de saida customizado')
def backup(db: str, backup_type: str, storage: str, compress: str, output: Optional[str]):
    click.echo(f"🔄 Iniciando backup {backup_type} do banco: {db}")

    try:
        from src.core.config import ConfigManager
        from src.backup.manager import BackupManager

        config_manager = ConfigManager()
        db_config = config_manager.get_database_config(db)

        backup_manager = BackupManager(db_config, storage, compress)

        result = backup_manager.execute_backup(backup_type, output)

        click.echo(f"✅ Backup concluído com sucesso!")
        click.echo(f"📁 Arquivo: {result.storage_location}")
        click.echo(f"📊 Tamanho: {result.size_bytes / (1024*1024):.2f} MB")
        click.echo(f"🔐 Checksum: {result.checksum[:16]}...")
    except Exception as e:
        click.echo(f"❌ Erro ao criar backup: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--db', required=True, help='Nome da configuração do banco de dados')
@click.option('--file', 'backup_file', required=True, help='Arquivo de backup')
@click.option('--target-db', help='Nome do banco de dados alvo (opcional)')
@click.option('--tables', help='Tabelas específicas (separadas por vírgula)')
@click.confirmation_option(prompt='⚠️  Esta operação irá sobrescrever dados. Continuar?')
def restore(db: str, backup_file: str, target_db: Optional[str], tables: Optional[str]):
    """Restaura um backup do banco de dados"""
    click.echo(f"🔄 Iniciando restore do backup: {backup_file}")
    
    try:
        from src.core.config import ConfigManager
        from src.restore.manager import RestoreManager
        
        config_manager = ConfigManager()
        db_config = config_manager.get_database_config(db)
        
        restore_manager = RestoreManager(db_config)
        
        table_list = tables.split(',') if tables else None
        success = restore_manager.execute_restore(backup_file, target_db, table_list)
        
        if success:
            click.echo(f"✅ Restore concluído com sucesso!")
        else:
            click.echo(f"❌ Falha no restore", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Erro ao restaurar backup: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--db', help='Banco de dados específico')
@click.option('--limit', default=10, help='Número de backups a listar')
def list_backups(db: Optional[str], limit: int):
    """Lista backups disponíveis"""
    click.echo("📋 Listando backups disponíveis...")
    
    try:
        from src.backup.manager import BackupManager
        
        backups = BackupManager.list_backups(db, limit)
        
        if not backups:
            click.echo("Nenhum backup encontrado.")
            return
        
        click.echo(f"\n{'Database':<15} {'Data':<20} {'Tipo':<12} {'Tamanho':<10} {'Storage'}")
        click.echo("-" * 80)
        
        for backup in backups:
            size_mb = backup.size_bytes / (1024*1024)
            click.echo(f"{backup.database_name:<15} {backup.timestamp:<20} "
                      f"{backup.backup_type.value:<12} {size_mb:>8.2f}MB {backup.storage_location}")
                      
    except Exception as e:
        click.echo(f"❌ Erro ao listar backups: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--db', required=True, help='Nome da configuração do banco de dados')
def test(db: str):
    """Testa a conexão com o banco de dados"""
    click.echo(f"🔍 Testando conexão com: {db}")
    
    try:
        from src.core.config import ConfigManager
        from src.database.factory import DatabaseFactory
        
        config_manager = ConfigManager()
        db_config = config_manager.get_database_config(db)
        
        database = DatabaseFactory.create(db_config)
        result = database.test_connection()
        
        if result['success']:
            click.echo(f"✅ Conexão bem-sucedida!")
            click.echo(f"   Versão: {result.get('version', 'N/A')}")
            click.echo(f"   Tamanho DB: {result.get('size_mb', 0):.2f} MB")
        else:
            click.echo(f"❌ Falha na conexão: {result.get('error')}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Erro: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--config', required=True, help='Arquivo de configuração de agendamento')
@click.option('--daemon', is_flag=True, help='Executar em modo daemon')
def schedule(config: str, daemon: bool):
    """Agenda backups automáticos"""
    click.echo(f"⏰ Configurando agendamento de backups...")
    
    try:
        from src.core.scheduler import BackupScheduler
        
        scheduler = BackupScheduler(config)
        
        if daemon:
            click.echo("🔄 Iniciando scheduler em modo daemon...")
            scheduler.start_daemon()
        else:
            click.echo("📋 Tarefas agendadas:")
            scheduler.print_schedule()
            
    except Exception as e:
        click.echo(f"❌ Erro ao configurar agendamento: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
def status():
    """Mostra status dos backups e agendamentos"""
    click.echo("📊 Status do Sistema de Backup\n")
    
    try:
        from src.core.logger import get_recent_logs
        from src.core.scheduler import BackupScheduler
        
        # Últimos backups
        click.echo("🕒 Últimos backups executados:")
        logs = get_recent_logs(limit=5)
        for log in logs:
            status_icon = "✅" if log['status'] == 'success' else "❌"
            click.echo(f"  {status_icon} {log['timestamp']} - {log['database']} - {log['type']}")
        
        # Próximos agendamentos
        click.echo("\n📅 Próximos backups agendados:")
        scheduler = BackupScheduler()
        scheduler.print_next_runs(limit=5)
        
    except Exception as e:
        click.echo(f"❌ Erro ao obter status: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--db', required=True, help='Nome da configuração do banco de dados')
def info(db: str):
    """Mostra informações detalhadas do banco de dados"""
    try:
        from src.core.config import ConfigManager
        from src.database.factory import DatabaseFactory
        
        config_manager = ConfigManager()
        db_config = config_manager.get_database_config(db)
        
        database = DatabaseFactory.create(db_config)
        database.connect()
        
        click.echo(f"\n📊 Informações do Banco: {db}")
        click.echo(f"{'='*50}")
        click.echo(f"Tipo: {db_config.db_type}")
        click.echo(f"Host: {db_config.host}:{db_config.port}")
        click.echo(f"Database: {db_config.database}")
        click.echo(f"Tamanho: {database.get_database_size() / (1024*1024):.2f} MB")
        
        tables = database.list_tables()
        click.echo(f"\n📋 Tabelas/Collections ({len(tables)}):")
        for table in tables[:20]:  # Mostra até 20
            click.echo(f"  - {table}")
        
        if len(tables) > 20:
            click.echo(f"  ... e mais {len(tables) - 20} tabelas")
        
        database.disconnect()
        
    except Exception as e:
        click.echo(f"❌ Erro: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
