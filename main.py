import os.path

from selenium.common import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.wait import WebDriverWait

from config import constants


def start_run():
    options = Options()
    options.headless = True
    options.add_argument("--headless")

    service = Service(executable_path=os.path.join(constants.APP_DIR, "drivers", constants.DRIVER_FILE_NAME))

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
