import os
import urlparse
import urllib

from selenium import webdriver


# Create a new instance of the Firefox driver
driver = webdriver.Firefox()

# Get current path
current_directory = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(current_directory, "SLBTest.html")
url = urlparse.urljoin("file:", urllib.pathname2url(path))

# go to the local testSLB page
driver.get(url)

# find the text in the cell "00"
data_to_get = driver.find_element_by_id("00").text

my_file = open(os.path.join(current_directory, "parsingTry.txt"), "w")
my_file.write(data_to_get)
my_file.close()

driver.quit()
