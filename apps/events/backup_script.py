import os
import subprocess
from datetime import datetime
from pathlib import Path
from io import StringIO
import django
from dotenv import load_dotenv
from apps.events.models import BackupHistory
from apps.events.upload_to_cloud import upload_backup_to_cloud
from apps.events.utils.log_line import log_line

# Initialize Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

# Load .env for local dev
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

# Database credentials
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
PG_DUMP_PATH = os.getenv("PG_DUMP_PATH", "pg_dump")  # Make sure pg_dump exists in Render container

BACKUP_DIR = Path("/tmp/backups")
LOG_DIR = Path("/tmp/logs")
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
    log_line(log_output, "Starting backup...")

    try:
        #  Run data-only backup
        log_line(log_output, f"Creating backup file: {backup_filename}")

        env = os.environ.copy()
        env["PGPASSWORD"] = DB_PASSWORD

        result = subprocess.run(
            [
                PG_DUMP_PATH,
                "-h", DB_HOST,
                "-p", DB_PORT,
                "-U", DB_USER,
                "-d", DB_NAME,
                "--data-only",            # Only dump data
                "--column-inserts",       # Optional: safer INSERT statements
                "-f", str(backup_path),
                "--no-password"
            ],
            env=env,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            log_line(log_output, f"Backup failed:\n{result.stderr}", level="ERROR")
            BackupHistory.objects.create(
                BackupName=backup_name,
                BackupStatus="failed",
                BackupSize="0 MB",
                BackupFile=None,
                BackupLogFile=None
            )
            return {"status": "error", "message": result.stderr}

        log_line(log_output, f"Data backup completed successfully: {backup_filename}")

        # Upload backup file to cloud
        log_line(log_output, "Uploading backup file to cloud...")
        backup_s3_key = upload_backup_to_cloud(str(backup_path), log_output, folder="backups")

        # Save log locally
        with open(log_path, "w") as f:
            f.write(log_output.getvalue())

        # Upload log file to cloud
        log_s3_key = upload_backup_to_cloud(str(log_path), log_output, folder="logs")

        # Record backup in database
        status = "completed" if backup_s3_key and log_s3_key else "failed"
        BackupHistory.objects.create(
            BackupName=backup_name,
            BackupStatus=status,
            BackupSize=f"{os.path.getsize(backup_path) / (1024*1024):.2f} MB",
            BackupFile=backup_s3_key,
            BackupLogFile=log_s3_key
        )

        log_line(log_output, "Backup record saved in the database.")
        return {"status": "success", "message": f"{backup_name} completed!"}

    except Exception as e:
        log_line(log_output, f"An error occurred during backup: {str(e)}", level="ERROR")
        BackupHistory.objects.create(
            BackupName=backup_name,
            BackupStatus="failed",
            BackupSize="0 MB",
            BackupFile=None,
            BackupLogFile=None
        )
        return {"status": "error", "message": str(e)}

    finally:
        if backup_path.exists():
            backup_path.unlink()
        if log_path.exists():
            log_path.unlink()

        print(log_output.getvalue())
