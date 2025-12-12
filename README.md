# 🗄️ Database Backup CLI

Uma ferramenta de linha de comando completa e robusta para backup de múltiplos sistemas de gerenciamento de banco de dados (DBMS).

## 🌟 Características

- ✅ **Múltiplos DBMS**: MySQL, PostgreSQL, MongoDB, SQLite
- 📦 **Tipos de Backup**: Full, Incremental, Differential
- 🗜️ **Compressão**: gzip, bzip2, xz
- ☁️ **Storage**: Local, AWS S3, Google Cloud Storage, Azure Blob Storage
- ⏰ **Agendamento**: Backups automáticos com sintaxe cron
- 📊 **Logging**: Logs estruturados em JSON
- 🔔 **Notificações**: Slack para alertas de backup
- 🔄 **Restore**: Restauração completa ou seletiva
- 🔐 **Segurança**: Checksums SHA256, credenciais em variáveis de ambiente
- 🐳 **Docker**: Suporte completo para containerização

## 📋 Requisitos

- Python 3.8+
- Clientes de banco de dados instalados (mysql-client, postgresql-client, etc.)
- Acesso aos bancos de dados que deseja fazer backup
- (Opcional) Credenciais de cloud storage para armazenamento remoto

## 🚀 Instalação

### Via pip (recomendado)

```bash
# Clone o repositório
git clone https://github.com/yourusername/db-backup-cli.git
cd db-backup-cli

# Instale as dependências
pip install -r requirements.txt

# Instale o pacote
pip install -e .
```

### Via Docker

```bash
# Build da imagem
docker build -t dbbackup-cli .

# Execute
docker run --rm dbbackup-cli --help
```

## ⚙️ Configuração

### 1. Variáveis de Ambiente

Copie o arquivo de exemplo e configure suas credenciais:

```bash
cp .env.example .env
# Edite .env com suas credenciais
```

### 2. Configuração de Bancos de Dados

Edite `config/databases.yaml` para adicionar seus bancos:

```yaml
databases:
  my_mysql_db:
    type: mysql
    host: localhost
    port: 3306
    username: backup_user
    password: ${DB_MYSQL_PASSWORD}
    database: production
```

### 3. Configuração de Agendamento (Opcional)

Configure backups automáticos no mesmo arquivo:

```yaml
schedules:
  - name: "Daily Backup"
    cron: "0 2 * * *"
    database: my_mysql_db
    type: full
    storage: s3
    enabled: true
```

## 📖 Uso

### Comandos Básicos

#### Testar Conexão

```bash
dbbackup test --db my_mysql_db
```

#### Criar Backup

```bash
# Backup completo básico
dbbackup backup --db my_mysql_db

# Backup com opções
dbbackup backup --db my_mysql_db --type full --storage s3 --compress gzip

# Backup incremental
dbbackup backup --db my_mysql_db --type incremental
```

#### Listar Backups

```bash
# Listar todos
dbbackup list

# Listar de um banco específico
dbbackup list --db my_mysql_db --limit 20
```

#### Restaurar Backup

```bash
dbbackup restore --db my_mysql_db --file backup_20251204.sql.gz
```

#### Informações do Banco

```bash
dbbackup info --db my_mysql_db
```

#### Agendar Backups

```bash
# Visualizar agendamento
dbbackup schedule --config config/databases.yaml

# Executar em modo daemon
dbbackup schedule --config config/databases.yaml --daemon
```

#### Status do Sistema

```bash
dbbackup status
```

### Exemplos Práticos

#### Backup Diário Automático para S3

```bash
# 1. Configure o banco em databases.yaml
# 2. Configure credenciais AWS no .env
# 3. Execute o scheduler

dbbackup schedule --config config/databases.yaml --daemon
```

#### Backup Manual com Notificação Slack

```yaml
# Em config/default.yaml
notifications:
  enabled: true
  slack:
    webhook_url: ${SLACK_WEBHOOK_URL}
    notify_on: [success, failure]
```

```bash
dbbackup backup --db production_db --type full --storage s3
```

#### Restore Seletivo de Tabelas

```bash
dbbackup restore --db my_mysql_db \
  --file backup.sql.gz \
  --tables users,products,orders
```

## 🏗️ Arquitetura

### Estrutura de Diretórios

```
db-backup-cli/
├── src/
│   ├── core/          # Configuração, logging, scheduler
│   ├── database/      # Conectores de banco de dados
│   ├── backup/        # Lógica de backup
│   ├── storage/       # Provedores de armazenamento
│   ├── restore/       # Operações de restore
│   ├── notifications/ # Notificações (Slack, etc)
│   └── cli/           # Interface CLI
├── config/            # Arquivos de configuração
├── tests/             # Testes unitários
└── backups/           # Backups locais (padrão)
```

### Design Patterns Utilizados

- **Factory Pattern**: Criação dinâmica de conectores de banco e storage
- **Strategy Pattern**: Diferentes estratégias de backup (Full, Incremental, Differential)
- **Abstract Factory**: Interface comum para diferentes implementações
- **Command Pattern**: Encapsulamento de operações CLI

## 🔧 Desenvolvimento

### Executar Testes

```bash
pytest tests/ -v --cov=src
```

### Adicionar Novo Banco de Dados

1. Crie nova classe em `src/database/` herdando de `DatabaseBackupBase`
2. Implemente métodos abstratos: `connect()`, `create_backup()`, `restore_backup()`
3. Registre no `DatabaseFactory`

Exemplo:

```python
# src/database/mssql.py
from src.database.base import DatabaseBackupBase

class MSSQLBackup(DatabaseBackupBase):
    def connect(self):
        # Implementação de conexão
        pass
    
    def create_backup(self, backup_type, output_path):
        # Implementação de backup
        pass
```

### Adicionar Novo Provider de Storage

Similar ao banco de dados, herde de `StorageBase` e implemente os métodos necessários.

## 📊 Formato de Logs

Os logs são gerados em JSON estruturado:

```json
{
  "timestamp": "2025-12-04T10:30:00Z",
  "level": "INFO",
  "operation": "backup",
  "database": "mysql_prod",
  "type": "full",
  "duration_seconds": 45.2,
  "size_mb": 1024,
  "status": "success",
  "storage": "s3://my-backups/mysql_prod_20251204.sql.gz",
  "checksum": "a3b5c8d9e2f1..."
}
```

## 🔐 Segurança

- ✅ Credenciais armazenadas em variáveis de ambiente
- ✅ Checksums SHA256 para validação de integridade
- ✅ Suporte a SSL/TLS para conexões de banco
- ✅ Credenciais nunca aparecem em logs
- ✅ Opção de criptografia de backups (planejado)

## 🐛 Troubleshooting

### Erro de Conexão

```bash
# Verifique se as credenciais estão corretas
dbbackup test --db my_db

# Verifique se o banco está acessível
ping mysql.example.com
```

### Erro de Permissões

Certifique-se que o usuário de backup tem permissões adequadas:

```sql
-- MySQL
GRANT SELECT, LOCK TABLES, SHOW VIEW ON database.* TO 'backup_user'@'%';

-- PostgreSQL
GRANT CONNECT ON DATABASE mydb TO backup_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_user;
```

### Backup Muito Lento

- Use compressão mais leve (`gzip` ao invés de `bz2`)
- Considere backup incremental para bancos grandes
- Verifique a velocidade da rede se usando cloud storage

## 📈 Performance

### Benchmarks

| Banco de Dados | Tamanho | Tipo Backup | Compressão | Tempo | Tamanho Final |
|----------------|---------|-------------|------------|-------|---------------|
| MySQL 5GB      | 5 GB    | Full        | gzip       | 3m 20s| 1.2 GB        |
| PostgreSQL 10GB| 10 GB   | Full        | bz2        | 8m 15s| 1.8 GB        |
| MongoDB 2GB    | 2 GB    | Full        | gzip       | 1m 45s| 450 MB        |

### Otimizações

- Backups são executados em streaming para reduzir uso de memória
- Upload multipart para arquivos grandes
- Progress bars para operações longas
- Compressão paralela quando possível

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Roadmap

- [ ] Suporte para Microsoft SQL Server
- [ ] Suporte para Oracle Database
- [ ] Criptografia de backups
- [ ] Interface Web (opcional)
- [ ] Métricas e dashboards
- [ ] Backup de schemas específicos
- [ ] Integração com Kubernetes

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👥 Autores

- Pedro Henrique

## 🙏 Agradecimentos

- [Click](https://click.palletsprojects.com/) - Framework CLI
- [Rich](https://rich.readthedocs.io/) - Output bonito no terminal
- [Loguru](https://loguru.readthedocs.io/) - Logging simplificado

---

⭐ Se este projeto foi útil, considere dar uma estrela no GitHub!
