from datetime import datetime

# ----- Logging helper -----
def log_line(log_output, message, level="INFO"):
    """Write timestamped, human-readable log messages."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {level}: {message}\n"
    log_output.write(line)
    print(line, end="")  # optional: also print to console