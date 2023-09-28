import os.path
import platform

from selenium.common import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.wait import WebDriverWait

from config import constants


def get_service_for_selenium_driver():
    system_name = platform.system()
    system_machine = platform.machine()

    if system_machine == "Windows":
        if system_machine == "x86_64":
            service = Service(executable_path=os.path.join(constants.DRIVER_DIR, "win64", "geckodriver.exe"))
        else:
            service = Service(executable_path=os.path.join(constants.DRIVER_DIR, "win32", "geckodriver.exe"))
    elif system_name == "Linux":
        if system_machine == "x86_64":
            service = Service(executable_path=os.path.join(constants.DRIVER_DIR, "linux64", "geckodriver"))
        else:
            service = Service(executable_path=os.path.join(constants.DRIVER_DIR, "linux32", "geckodriver"))
    else:
        service = None

    return service


def start_run():
    options = Options()
    options.headless = True
    options.add_argument("--headless")

    options.binary_location = os.path.join(constants.DRIVER_DIR, "firefox", "firefox")

    service = get_service_for_selenium_driver()

    driver = webdriver.Firefox(options=options, service=service)
    driver.get("https://www.torrentleech.org/user/account/login/")
    driver.find_element(By.NAME, 'username').send_keys(constants.USERNAME)
    driver.find_element(By.NAME, 'password').send_keys(constants.PASSWORD)
    driver.find_element(By.NAME, 'password').send_keys(Keys.ENTER)
    timeout = 5
    try:
        element_present = EC.presence_of_element_located((By.ID, 'top-app'))
        WebDriverWait(driver, timeout).until(element_present)
    except TimeoutException:
        print("Timed out waiting for page to load")

    driver.quit()


if __name__ == "__main__":
    start_run()
