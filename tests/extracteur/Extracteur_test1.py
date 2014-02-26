# goal : opening eQuality home page and clicking on MatsQuery to access search page

# Selenium WebDriver modules
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait

firefox = webdriver.Firefox()
firefox.get("http://www.google.ca")
test = actionChains( firefox)
element = firefox.find_element_by_id("gb_23")
test.click(element)
