# -*- coding: utf-8 -*-
import os

from selenium import webdriver

tests_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

md = webdriver.Firefox()
md.get('file:///' + os.path.join(tests_folder, 'to_scrap/TFL/resultat/menu.htm'))
source = md.page_source.encode('utf-8')


os.chdir(os.path.join(tests_folder, 'extracteur'))

myFile = open("test.txt", "w")
myFile.write(source)
myFile.close()
