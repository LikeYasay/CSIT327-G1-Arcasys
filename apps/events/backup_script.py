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

# Local folders for temporary backups and logs
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
    log_line(log_output, "Starting database backup...")

    try:
        # Step 1: Run database backup
        log_line(log_output, "Creating backup file...")
        result = subprocess.run(
            [
                PG_DUMP_PATH,
                "-h", DB_HOST,
                "-p", DB_PORT,
                "-U", DB_USER,
                "-d", DB_NAME,
                "-f", str(backup_path),
                "--no-password"
            ],
            env={"PGPASSWORD": DB_PASSWORD},
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
            return

        log_line(log_output, f"Database backup completed successfully! Saved as {backup_filename}")

        # Step 2: Upload backup file to S3
        log_line(log_output, "Uploading backup file to cloud...")
        backup_s3_key = upload_backup_to_cloud(str(backup_path), log_output, folder="backups")

        # Step 3: Save log locally
        with open(log_path, "w") as f:
            f.write(log_output.getvalue())

        # Step 4: Upload log file to S3
        log_s3_key = upload_backup_to_cloud(str(log_path), log_output, folder="logs")

        # Step 5: Record backup in database
        status = "completed" if backup_s3_key and log_s3_key else "failed"
        BackupHistory.objects.create(
            BackupName=backup_name,
            BackupStatus=status,
            BackupSize=f"{os.path.getsize(backup_path) / (1024*1024):.2f} MB",
            BackupFile=backup_s3_key,
            BackupLogFile=log_s3_key
        )

        log_line(log_output, "Backup record saved in the database.")

    except Exception as e:
        log_line(log_output, f"An error occurred during backup: {str(e)}", level="ERROR")
        BackupHistory.objects.create(
            BackupName=backup_name,
            BackupStatus="failed",
            BackupSize="0 MB",
            BackupFile=None,
            BackupLogFile=None
        )

    finally:
        # Step 6: Cleanup temporary files
        if backup_path.exists():
            backup_path.unlink()
        if log_path.exists():
            log_path.unlink()

        # Step 7: Final log output
        print(log_output.getvalue())


if __name__ == "__main__":
    backup_database()


