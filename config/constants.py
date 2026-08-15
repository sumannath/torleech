import os.path

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVER_DIR = os.path.join(APP_DIR, "drivers")
DRIVER_FILE_NAME = "geckodriver.exe"


def _require_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


USERNAME = _require_env('TORLEECH_USERNAME')
PASSWORD = _require_env('TORLEECH_PASSWORD')
