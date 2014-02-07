from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains


myDriver = webdriver.Firefox()
myDriver.get('file:///C:/Users/Benjamin/Documents/Etudes/Centrale/Projet_Option/docs%20Boris/decembre/eQuality_files/menu.htm')

img = myDriver.find_element_by_xpath("//img[contains(@src, 'menu_data/mats_perform_test_HV.jpg')]")

test = ActionChains(myDriver)

test.move_to_element_with_offset(img, 168, 10).click().perform()
test.click().perform()
test.click().perform()

test.click().perform()

test.click().perform()
