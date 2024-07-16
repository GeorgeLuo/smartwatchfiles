import time
from typing import List, Tuple
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager


class WebScraper:
    def __init__(self):
        self.driver = self._init_driver()

    def _init_driver(self):
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-infobars")

        driver = uc.Chrome(
            executable_path=ChromeDriverManager().install(), options=chrome_options)
        return driver

    def fetch_page_source(self, url):
        try:
            print(f"Navigating to URL: {url}")
            self.driver.get(url)

            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            time.sleep(3)  # Adjust this based on the website's load time

            page_source = self.driver.page_source

            with open('page_source.html', 'w', encoding='utf-8') as file:
                file.write(page_source)

            return page_source

        except Exception as e:
            print(f"Error while waiting for the page to load: {e}")
            return None

    def close(self):
        self.driver.quit()


global_scraper = WebScraper()


def download_and_parse(url: str):
    page_source = global_scraper.fetch_page_source(url)

    if not page_source:
        return None

    soup = BeautifulSoup(page_source, 'html.parser')

    for unwanted in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
        unwanted.decompose()

    body_text = soup.get_text(separator="\n", strip=True)

    return body_text
