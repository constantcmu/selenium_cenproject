from selenium import webdriver

def test_hello_world():
    driver = webdriver.Chrome()
    driver.get("http://www.example.com")
    assert "Example Domain" in driver.title
    driver.quit()