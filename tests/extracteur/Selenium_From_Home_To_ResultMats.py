# goal : opening eQuality home page and clicking on MatsQuery to access search page

# Selenium WebDriver modules
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
import os

myUrl = "file:///" + os.path.dirname(os.path.abspath(__file__)) + "/home.htm"

firefox = webdriver.Firefox()
firefox.implicitly_wait(3)
firefox.get(myUrl)


area = firefox.find_element_by_xpath("//area[contains(@alt, 'Query Performed Tests')]")

test = ActionChains(firefox)
test.click(area)
test.perform()

t = firefox.find_element_by_name("sabutton")
t.submit()

