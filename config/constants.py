import os.path

from config import credentials

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVER_DIR = os.path.join(APP_DIR, "drivers")
DRIVER_FILE_NAME = "geckodriver.exe"

USERNAME = credentials.USERNAME
PASSWORD = credentials.PASSWORD
