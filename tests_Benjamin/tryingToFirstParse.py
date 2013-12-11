import os
import pickle
import urlparse, urllib
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0


# Create a new instance of the Firefox driver
driver = webdriver.Firefox()

# Get current path
currentDirectory = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(currentDirectory, "SLBTest.html")
url = urlparse.urljoin("file:", urllib.pathname2url(path))
print url

### go to the local testSLB page
driver.get(url)

# find the text in the cell "00"
dataToGet = driver.find_element_by_id("00").text

print dataToGet

myFile = open(os.path.join(currentDirectory, "parsingTry.txt"), "w")
myFile.write(dataToGet)
myFile.close()

driver.quit()
