from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def test_hello_world():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.get("http://www.example.com")
    assert "Example Domain" in driver.title
    driver.quit()

if __name__ == "__main__":
    test_hello_world()
    