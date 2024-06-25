import os.path
import platform
import subprocess
import logging

from selenium.common import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.wait import WebDriverWait

from config import constants


def get_system_details():
    system_name = platform.system()
    system_machine = platform.machine()

    logging.info(f"System: {system_name}, Machine: {system_machine}")
    return system_name, system_machine


def get_service_for_selenium_driver():
    system_name, system_machine = get_system_details()

    if system_name == "Windows":
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
    else:
        service = None

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
        level=logging.DEBUG,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def start_run():
    options = Options()
    options.headless = True
    options.add_argument("--headless")
    options.binary_location = get_firefox_path()
    service = get_service_for_selenium_driver()

    driver = webdriver.Firefox(options=options, service=service)

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
        logging.error(f"Login unsuccessful!")

    driver.quit()


if __name__ == "__main__":
    setup_logging()

    logging.info(f"Starting run")
    start_run()
