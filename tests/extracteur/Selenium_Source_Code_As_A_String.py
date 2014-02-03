# -*- coding: cp1252 -*-

import os
from selenium import webdriver

md = webdriver.Firefox()
md.get("file:///C:/Users/Benjamin/Documents/Etudes/Centrale/Projet_Option/Schlumberger/tests/to_scrap/TFL/resultat/menu.htm")
source = md.page_source.encode('utf-8')


os.chdir("C:/Users/Benjamin/Documents/Etudes/Centrale/Projet_Option/Schlumberger/tests/extracteur")

myFile = open("test.txt", "w") 
myFile.write(source)
myFile.close()

    




