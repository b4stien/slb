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
<<<<<<< HEAD
firefox.implicitly_wait(5)
=======
firefox.implicitly_wait(3)
>>>>>>> db574dbf12309a775a7d880e759fc36a153da071
firefox.get(myUrl)


area = firefox.find_element_by_xpath("//area[contains(@alt, 'Query Performed Tests')]")

test = ActionChains(firefox)
test.click(area)
test.perform()

<<<<<<< HEAD
listTakenIDRecherche = [3401783, 3401784, 3401787, 3401790, 3401803]


firefox.find_element_by_name('test_taken_id').send_keys(listTakenIDRecherche)

firefox.implicitly_wait(5)

t = firefox.find_element_by_name('sabutton')
t.click()
t.click() # Click twice in case the first click just re-focused the window.
    
=======
t = firefox.find_element_by_name("sabutton")
>>>>>>> db574dbf12309a775a7d880e759fc36a153da071
t.submit()

