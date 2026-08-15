import os.path
import platform
import shutil
import signal
import subprocess
import logging
import tempfile
import time
from time import sleep

from selenium.common import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.wait import WebDriverWait

from config import constants

PROFILE_PREFIX = "rust_mozprofile"
STALE_PROFILE_AGE_SECONDS = 60 * 60
PAGE_LOAD_TIMEOUT_SECONDS = 60


def get_system_details():
    system_name = platform.system()
    system_machine = platform.machine()

    logging.info(f"System: {system_name}, Machine: {system_machine}")
    return system_name, system_machine


def get_service_for_selenium_driver():
    system_name, system_machine = get_system_details()

    service = None
    # Distro-provided geckodriver (Alpine's musl build, for instance) takes
    # precedence over the binaries bundled in drivers/.
    driver_path = os.environ.get("GECKODRIVER_PATH")
    if driver_path:
        service = Service(executable_path=driver_path)
    elif system_name == "Windows":
        if system_machine in ["x86_64", "AMD64"]:
            service = Service(executable_path=os.path.join(constants.DRIVER_DIR, "win64", "geckodriver.exe"))
        elif system_machine in ["x86"]:
            service = Service(executable_path=os.path.join(constants.DRIVER_DIR, "win32", "geckodriver.exe"))
        elif system_machine in ["aarch64"]:
            service = Service(executable_path=os.path.join(constants.DRIVER_DIR, "winaarch64", "geckodriver.exe"))
    elif system_name == "Linux":
        if system_machine in ["x86_64", "AMD64"]:
            service = Service(executable_path=os.path.join(constants.DRIVER_DIR, "linux64", "geckodriver"))
        elif system_machine in ["x86"]:
            service = Service(executable_path=os.path.join(constants.DRIVER_DIR, "linux32", "geckodriver"))
        elif system_machine in ["aarch64"]:
            service = Service(executable_path=os.path.join(constants.DRIVER_DIR, "linuxaarch64", "geckodriver"))

    if service is None:
        raise RuntimeError(
            f"No geckodriver bundled for this platform: system={system_name}, machine={system_machine}"
        )

    logging.info(f"Driver location: {service.path}")
    return service


def get_firefox_path():
    system_name, system_machine = get_system_details()

    if system_name == "Windows":
        default_path = r'C:\Program Files\Mozilla Firefox\firefox.exe'
        if os.path.exists(default_path):
            firefox_path = default_path
        else:
            # If not, try to find the path using the Windows registry
            import winreg

            try:
                # Open the registry key for Firefox
                key = r'SOFTWARE\Mozilla\Mozilla Firefox'
                hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key)

                # Query the registry for the installed Version
                firefox_ver, _ = winreg.QueryValueEx(hkey, 'CurrentVersion')

                hkey = winreg.OpenKey(hkey, f"{firefox_ver}\\Main")
                firefox_path, _ = winreg.QueryValueEx(hkey, 'PathToExe')

                # Close the registry key
                winreg.CloseKey(hkey)

            except Exception as e:
                print(f"Error: {e}")
                firefox_path = None

        return firefox_path
    elif system_name == "Linux":
        command = "which firefox"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        if error:
            print("Error:")
            print(error.decode())
            return None

        return output.decode().strip()


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def sweep_stale_profiles():
    """Delete geckodriver profile directories left behind by earlier runs.

    driver.quit() is not sufficient on its own: geckodriver orphans profiles on
    some clean exits too, so anything older than an hour is fair game.
    """
    temp_dir = tempfile.gettempdir()
    cutoff = time.time() - STALE_PROFILE_AGE_SECONDS

    try:
        entries = os.listdir(temp_dir)
    except OSError as e:
        logging.warning(f"Could not scan {temp_dir} for stale profiles: {e}")
        return

    removed = 0
    for entry in entries:
        if not entry.startswith(PROFILE_PREFIX):
            continue

        path = os.path.join(temp_dir, entry)
        try:
            if not os.path.isdir(path) or os.path.getmtime(path) > cutoff:
                continue
        except OSError:
            # Vanished or unreadable between listing and stat; nothing to do.
            continue

        shutil.rmtree(path, ignore_errors=True)
        removed += 1

    if removed:
        logging.info(f"Swept {removed} stale profile directories from {temp_dir}")


def handle_sigterm(signum, frame):
    logging.info(f"Received signal {signum}, shutting down")
    raise SystemExit(0)


def start_run():
    options = Options()
    options.add_argument("--headless")
    if "FIREFOX_PATH" in os.environ:
        binary_path = os.environ["FIREFOX_PATH"]
    else:
        binary_path = get_firefox_path()
    options.binary_location = binary_path
    service = get_service_for_selenium_driver()

    driver = None
    try:
        driver = webdriver.Firefox(options=options, service=service)
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT_SECONDS)

        logging.info(f"Gecko driver initialized successfully. Trying login...")
        driver.get("https://www.torrentleech.org/user/account/login/")
        driver.find_element(By.NAME, 'username').send_keys(constants.USERNAME)
        driver.find_element(By.NAME, 'password').send_keys(constants.PASSWORD)
        driver.find_element(By.NAME, 'password').send_keys(Keys.ENTER)
        timeout = 5
        try:
            element_present = EC.presence_of_element_located((By.ID, 'top-app'))
            WebDriverWait(driver, timeout).until(element_present)
            logging.info(f"Login successful!")
        except TimeoutException:
            # The login page states the actual reason (bad credentials, rate
            # limiting, and so on). Without it every failure looks identical.
            reason = ""
            try:
                for line in driver.find_element(By.TAG_NAME, 'body').text.splitlines():
                    if line.strip().startswith("Error:"):
                        reason = f" Site says: {line.strip()}"
                        break
            except Exception:
                pass
            logging.error(f"Login unsuccessful!{reason}")
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                # Never let a teardown failure mask the exception that caused it.
                logging.warning("driver.quit() failed", exc_info=True)


if __name__ == "__main__":
    setup_logging()
    signal.signal(signal.SIGTERM, handle_sigterm)
    sleep_hours = os.environ.get('SLEEP_HOURS', 6)

    while True:
        sweep_stale_profiles()
        logging.info(f"Starting run")
        try:
            start_run()
        except Exception:
            logging.exception("Run failed; continuing to next cycle")
        logging.info(f"Sleeping for {sleep_hours} hours...")
        sleep(int(sleep_hours) * 60 * 60)
