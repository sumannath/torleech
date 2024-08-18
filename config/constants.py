import os.path

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVER_DIR = os.path.join(APP_DIR, "drivers")
DRIVER_FILE_NAME = "geckodriver.exe"

USERNAME = os.environ['TORLEECH_USERNAME']
PASSWORD = os.environ['TORLEECH_PASSSWORD']
