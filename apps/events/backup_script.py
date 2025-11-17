import os
import subprocess
from datetime import datetime
import django
from dotenv import load_dotenv
from pathlib import Path
from io import StringIO
from apps.events.models import BackupHistory
from apps.events.upload_to_cloud import upload_backup_to_cloud
from apps.events.utils.log_line import log_line

# Initialize Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

# Load .env
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

# Database credentials
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
PG_DUMP_PATH = os.getenv("PG_DUMP_PATH", "pg_dump")

# Local folders
BASE_DIR = Path(__file__).resolve().parent
BACKUP_DIR = BASE_DIR / "temp_files"
LOG_DIR = BASE_DIR / "temp_logs"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

def backup_database():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"Backup_{timestamp}"
    backup_filename = f"db_backup_{timestamp}.sql"
    log_filename = f"backup_log_{timestamp}.txt"

    backup_path = BACKUP_DIR / backup_filename
    log_path = LOG_DIR / log_filename

    log_output = StringIO()
    log_line(log_output, "Starting DATA-ONLY database backup...")

    backup_s3_key = None
    log_s3_key = None

    try:
        # Build correct PG URL (NO PASSWORD HERE)
        db_url = f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"

        log_line(log_output, "Creating Supabase-safe DATA-ONLY backup file...")

        # DATA ONLY + exclude Supabase system tables
        result = subprocess.run(
            [
                PG_DUMP_PATH,
                db_url,
                "--data-only",
                "--inserts",
                "--exclude-table=schema_migrations",
                "--exclude-table=django_migrations",
                "--exclude-table=django_session",
                "--exclude-table=pg_*",
                "--exclude-table=information_schema.*",
                "--exclude-table=auth.*",
                "--exclude-table=storage.*",
                "--exclude-table=realtime.*",
                "-f", str(backup_path),
                "--verbose"
            ],
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "PGPASSWORD": DB_PASSWORD}  # FIX: this is the correct way
        )

        if result.returncode != 0:
            log_line(log_output, f"Backup failed:\n{result.stderr}", level="ERROR")
            log_line(log_output, f"Command stdout:\n{result.stdout}")

            with open(log_path, "w") as f:
                f.write(log_output.getvalue())
            log_s3_key = upload_backup_to_cloud(str(log_path), log_output, folder="logs")

            BackupHistory.objects.create(
                BackupName=backup_name,
                BackupStatus="failed",
                BackupSize="0 MB",
                BackupFile=None,
                BackupLogFile=log_s3_key
            )
            return

        log_line(log_output, f"Backup created successfully: {backup_filename}")

        # Upload backup file
        log_line(log_output, "Uploading backup file to cloud…")
        backup_s3_key = upload_backup_to_cloud(str(backup_path), log_output, folder="backups")

        # Save log locally then upload
        with open(log_path, "w") as f:
            f.write(log_output.getvalue())
        log_s3_key = upload_backup_to_cloud(str(log_path), log_output, folder="logs")

        status = "completed" if backup_s3_key and log_s3_key else "failed"

        BackupHistory.objects.create(
            BackupName=backup_name,
            BackupStatus=status,
            BackupSize=f"{os.path.getsize(backup_path) / (1024 * 1024):.2f} MB",
            BackupFile=backup_s3_key,
            BackupLogFile=log_s3_key
        )

        log_line(log_output, "Backup record saved.")

    except subprocess.TimeoutExpired:
        log_line(log_output, "Backup timed out after 60 seconds", level="ERROR")

        with open(log_path, "w") as f:
            f.write(log_output.getvalue())
        log_s3_key = upload_backup_to_cloud(str(log_path), log_output, folder="logs")

        BackupHistory.objects.create(
            BackupName=backup_name,
            BackupStatus="failed",
            BackupSize="0 MB",
            BackupFile=None,
            BackupLogFile=log_s3_key
        )

    except Exception as e:
        log_line(log_output, f"Backup error: {str(e)}", level="ERROR")

        with open(log_path, "w") as f:
            f.write(log_output.getvalue())
        log_s3_key = upload_backup_to_cloud(str(log_path), log_output, folder="logs")

        BackupHistory.objects.create(
            BackupName=backup_name,
            BackupStatus="failed",
            BackupSize="0 MB",
            BackupFile=None,
            BackupLogFile=log_s3_key
        )

    finally:
        if backup_path.exists():
            backup_path.unlink()
        if log_path.exists():
            log_path.unlink()

        print(log_output.getvalue())