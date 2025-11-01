from pathlib import Path

# Directories
LOG_DIR = "logs"

for path in [LOG_DIR]:
    Path(path).mkdir(parents=True, exist_ok=True)


# AI MODEL
GEMINI_MODEL = "gemini-2.0-flash"
