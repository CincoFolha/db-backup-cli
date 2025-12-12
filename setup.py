from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="db-backup-cli",
    version="1.0.0",
    author="Pedro Henrique",
    description="A comprehensive CLI utility for database backups",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Database",
        "Topic :: System :: Archiving :: Backup",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.1.7",
        "rich>=13.7.0",
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0",
        "loguru>=0.7.2",
        "APScheduler>=3.10.4",
        "pymysql>=1.1.0",
        "psycopg2-binary>=2.9.9",
        "pymongo>=4.6.1",
        "boto3>=1.34.34",
        "google-cloud-storage>=2.14.0",
        "azure-storage-blob>=12.19.0",
        "slack-sdk>=3.26.2",
        "python-dateutil>=2.8.2",
        "requests>=2.31.0",
        "tqdm>=4.66.1",
    ],
    entry_points={
        "console_scripts": [
            "dbbackup=src.main:cli",
        ],
    },
)
