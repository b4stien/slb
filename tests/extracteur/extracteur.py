# Extracteur 

"""  
Some explanations of this script :

1. output the file csv with 
   cols = 'takenID','verifiedDate', 'serialNo', 'testID', 'Status', 'failLogLink'

2. use of TimeStamp


3. able to turn pages


"""

from collections import defaultdict
import json
import csv
from HTMLParser import HTMLParser
import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
import time
import os

""" Controller to parse MATS, inherits the HTMLParser Python class. """

class matsHTMLParser(HTMLParser):
    def __init__(self, dbTakenID= [] ):
        HTMLParser.__init__(self)
        
        """ localization attributes """
        self.table = False
        self.tr = False
        self.td = False
        self.b = False
        self.a = False

        self.resultsByTakenID = dbTakenID
        self.init()

        # self.cols = 'takenID', 'testID', 'testVersion', 'takenDate',\
        #     'site', 'tryNo', 'status', 'woID', 'po', 'line', 'testName',\
        #     'category', 'technician', 'wo', 'wc', 'operation', 'partNo',\
        #     'partDesc', 'rev', 'department', 'qaproc', 'prodLine', 'plDesc',\
        #     'project', 'serialNo', 'parentSN', 'supplierNo', 'supplierName',\
        #     'performedDate', 'modifiedDate', 'verifiedBy', 'verifiedDate',\
        #     'remarks','testEditLink', 'failLogLink'

        ###############
        # self.cols = 'takenID','verifiedDate', 'serialNo', 'testID', 'Status', 'failLogLink'
        # In order to note the places of part, serialNo, testId, failLogLink 
        # in the table of webpage

        """identification of the interesting columns, change here in case of change in eQuality. """
        self.takenIDCol = 0
        self.modifiedDateCol = 29
        self.serialNoCol = 24
        self.testIDCol = 1
        self.statusCol = 6
        self.failLogLinkCol = 34

        self.listCol = [ self.takenIDCol, self.modifiedDateCol, self.serialNoCol, \
                    self.testIDCol, self.statusCol, self.failLogLinkCol]
        
        """total number of columns in the MATS page"""
        self.lengthResultCol = 35

        """buffer some html data into the MatsHTMLParser"""
    def feed(self, html):
        self.init()
        HTMLParser.feed(self, html)

    """ reset counters and result """
    def init(self):

        """ temporary row result, to be appended to the global result at the end of the line """
        self.result = ['']* 6
        
        self.pagesNb = 0
        self.currentPageNo = 0
        self.pageRowStart = 0
        self.pageRowEnd = 0
        self.resultsNb = 0

        """counters"""
        self.tablei = 0 
        self.tdi = 0 
        self.bi = 0 
        self.tri = 0 

    def handle_starttag(self, tag, attrs):
        """incrementing tables counter at start tag"""
        if tag == 'table':
            self.table = True
            self.tablei += 1 
            # if self.tablei == 3:
            #     g_c.inc()
        """rows and cells counters will be incremented at end tag"""
        if tag == 'tr' and self.table:
            self.tr = True
        elif tag == 'td' and self.tr:
            self.td = True

        elif (tag == 'b' or tag == 'strong') and self.td:
            self.b = True
            self.bi += 1

            """ adding 'true' at the last position of the current row result in case of link to a TFL in the row"""
        elif tag == 'a' and self.td and self.tdi == self.failLogLinkCol:
            self.result[self.listCol.index(self.failLogLinkCol)] = str(True)
            

    def handle_endtag(self, tag):
        
        if tag == 'table':
            self.table = False
            self.tr = False
            self.td = False
            self.b = False

            self.tri = 0
            # if self.tablei == 3:
            #     g_c.dec()
            
            """incrementation of rows and cells counters here"""    
        elif tag == 'tr':
            self.tr = False
            self.td = False
            self.b = False

            self.tri += 1
            """call on endOfTr to let it add the current row result to the global result"""
            self.endOfTr()

            
            self.tdi = 0
            self.result = [''] * 6
        
        elif tag == 'td':
            self.td = False
            self.b = False

            """add 'false' at the last position of the current row result in case of no link to a TFL in the row"""
            if ( self.tdi == self.failLogLinkCol
                and self.result[self.listCol.index(self.failLogLinkCol)] != 'True'
                ):
                self.result[self.listCol.index(self.failLogLinkCol)] = str(False)


            self.tdi += 1 
            self.bi = 0 

        elif tag == 'b' or tag == 'strong':
            self.b = False

    def handle_data(self, data):

        """table 1 countains some valuable infos ... """
        if self.tablei == 1 and self.b:
            """ ... total number of pages in the third bold balise"""
            if self.bi == 3:
                self.pagesNb = int(data)
                if self.pagesNb == 1:
                    self.bi += 1 # If only one page, no page links (which else countains one bold balise) are displayed.
                    self.currentPageNo = 1
            elif self.bi == 4 and self.pagesNb > 1:
                """ ... current page number in the fourth one"""
                self.currentPageNo = int(data)
                # if self.currentPageNo == 1:
                #     pstepi("Found {0} page(s).", self.pagesNb)
            elif self.bi == 5:
                """ ... pageRowStart in the fifth one"""
                self.pageRowStart = int(data.lstrip('Rows '))
            elif self.bi == 6:
                """ ... pageRowEnd in the sixth one"""
                self.pageRowEnd = int(data)

            """table 2 countains the number of results"""
        elif self.tablei == 2 and self.b:
            self.resultsNb = int(data)
            # if self.currentPageNo == 1:
            #     pstepi("Found {0} result(s) in total.", data)
            # if self.pagesNb > 1:
            #     pstepi("Getting results #{0} to #{1}", self.pageRowStart,
            #            self.pageRowEnd)

            """table 3 countains the actual datas to get"""
        elif self.tablei == 3 :
            if  self.td and self.tdi in self.listCol:
                indexCol = self.listCol.index(self.tdi)
                if self.tdi != self.failLogLinkCol:
                    """if the column is among the interesting ones except for the TFL one, write the data at the right position of the current row result, replacing insecable spaces by usual spaces"""
                    if self.result[indexCol] == '':
                        self.result[indexCol] = data.replace("\xc2\xa0", " ")
                    else:
                        self.result[indexCol] += ' ' + data.replace("\xc2\xa0", " ")

    """appends current row result to global result and converts the MATS date into a timestamp"""            
    def endOfTr(self):
        if self.tablei == 3 and self.tdi == self.lengthResultCol :            
            r = self.result
            """turn matsTime into matsTimeStamp"""
            r[1] = matsTimeStamp(r[1])            
                          
            # woID = getDictKey(r, 'woID', 'None')
            # serialNo = getDictKey(r, 'serialNo', 'None')
            # takenID = getDictKey(r, 'takenID', 'None')

            # Print some progress comments.
            # pstepi("Recording test taken {0}, for S/N {1}, in WO {2}.", \
            #       takenID, serialNo, woID)

            # Insert the test taken dict into:
            # takenID > testData.
            self.resultsByTakenID.append(r)

            # Initialize the dicts if necessary.
            # The first dict does not need initialization thanks to
            # defaultdict. For some reason, a defaultdict of defaultdict
            # does not work.
            # initDict(self.resultsByWoIDSerialNoTakenID[woID], serialNo)

            # # Insert the test taken dict into:
            # # woID > serialNo > takenID > testData.
            # self.resultsByWoIDSerialNoTakenID[woID][serialNo][takenID] = r

    """gets global result"""
    def getResultByTakenID(self):
        return self.resultsByTakenID

    # def getResultByWoIDSerialNoTakenID(self):
    #     return self.resultsByWoIDSerialNoTakenID

# Get the value of the dict[key]. If the key is not defined yet, initialize
# it with the given default value.
# def getDictKey(myDict, key, initValue=None):
#     if key not in myDict:
#         myDict[key] = initValue
#     return myDict[key]

# # Initialize a key as dict within a parent dict.
# def initDict(parentDict, newKeyDict):
#     if newKeyDict not in parentDict:
#         parentDict[newKeyDict] = {}

""" 2 convenience - functions"""

def listToCsv ( csvFileName, listName):
    with open(csvFileName, 'wb') as f:
        writer = csv.writer(f, delimiter=',')
        # writer.writerows(csvHead)
        writer.writerows(listName)

def matsTimeStamp (matsTime):

    thisMatsDateTime = datetime.datetime.strptime(matsTime, \
                                                 '%d-%b-%Y %I:%M %p')

    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = thisMatsDateTime - epoch
    thisMatsTimeStamp = int(delta.total_seconds())
    return str(thisMatsTimeStamp)

def matsReadPage():

    pageWebSource = browser.page_source.encode('utf8')

    
    # parser.feed return pageRowStart(type int)
    rowStart = parser.feed(pageWebSource) 

    # Go to the next pages if any.
    pageNbTotal = parser.pagesNb
    if pageNbTotal > 1:
        newRowStart = rowStart # In order to check that we parse new results.
        i = 2 # Page 1 is already parsed.
        while i <= pageNbTotal:
            while newRowStart == rowStart:
                link = browser.find_elements_by_link_text(str(i))
                link = link[0].find_elements_by_tag_name('font')[0]
                # link = browser.find_elements_by_link_text(str(i))                ]
                # if len(link) == 0:

                #     # Try to find a "More pages" link.
                #     # eQ displays page links by group of 10 only.

                #     #  .... code to write ...

                #     # link = browser.find_elements_by_link_text( \
                #     #     g_eq['linkTextMorePages'])[0]
                # else:
                #     link = link[0].find_elements_by_tag_name('font')[0]

                # Before any mouse action, re-focus on the window in case the
                # user has clicked away.
                browser.switch_to_active_element()
                link.click()
                # pstepii("Page {0}/{1}", i, t)
                newRowStart = parser.feed(browser.page_source.encode('utf8'))
                # g_c.dec()
            rowStart = newRowStart
            i += 1


# def switchToFrameMainMenu():
#        # Loop to access SLB Domain.
#         # If not in SLB Domain, eQ prompts a basic HTTP authentication (modal
#         # dialog) that cannot be handled by Selenium. The user must enter his
#         # LDAP credentials.
#         machineInSlbDomain = False
#         while not machineInSlbDomain:
#             try:
#                 myDriver.focusDefaultContent()
#                 #myDriver.switch_to_default_content()
#                 t = myDriver.find_element_by_name("main_menu")
#                 myDriver.switch_to_frame(t)
#                 machineInSlbDomain = True
#             # except:
#             #     p_("Cannot access the frame.")
#             #     p_("eQuality may be prompting for login.")
#             #     p_("Refreshing the page to reload the login prompt.")
#             #     myDriver.get(g_eq['url'])
#             #     p_("Please login within the next {0} second(s).",
#             #        g_param['waitLogin'])
#             #     time.sleep(g_param['waitLogin'])


# def goToMatsPerformQuery():
#         # Try to find "Return to search page" link.
#         t = myDriver.find_elements_by_link_text('Return')
#         if len(t) > 0:
#             myDriver.focusActiveElement()
#             t[0].click()
#             time.sleep(g_param['waitMainMenu']/2)
#             return

#         # Otherwise, assume we are on the main menu and try to click on
#         # MATS Perform Query image.
#         else:
#             imgs = myDriver.find_elements_by_tag_name('img')
#             i=1
#             for img in imgs:
#                 if (img.get_attribute('src').find(g_mats['imageLinkPerform'])\
#                     >= 0
#                     ):
#                     test = ActionChains(myDriver)
#                     test.move_to_element_with_offset(img, 158, 1)
#                     test.click()
#                     self.focusActiveElement()
#                     test.perform()
#                     # Give some time for the click to take effect.
#                     time.sleep(g_param['waitMainMenu'])
#                     return

#             # If no appropriate image/link has been found, go back to eQ home
#             # and try again.
#             goToHome()
#             return goToMatsPerformQuery()

# def goToHome():
#     myDriver.switchToFrameToolbar()
#     imgs = myDriver.find_elements_by_tag_name('img')
#     for img in imgs:
#         if (img.get_attribute('src').find(g_eq['imageLinkHome'])\
#             >= 0
#             ):
#             myDriver.focusActiveElement()
#             img.click()
#                 # Give some time for the click to take effect.
#             time.sleep(g_param['waitMainMenu'])
#             myDriver.switchToFrameMainMenu()
#             return
# def switchToFrameToolbar():
#     myDriver.focusDefaultContent()
#     t = myDriver.find_element_by_name(g_eq['frameToolbar'])
#     myDriver.switch_to_frame(t)

#     # Re-focus on the window before any mouse action.
# def focusActiveElement():
#     myDriver.switch_to_active_element()

# def focusDefaultContent():
#     myDriver.switch_to_default_content()


########## Test with resultMats.htm #######################################

# with open ('resultMats.htm', 'r') as source:
#   pageWebSource = source.read()

myUrl = "file:///" + os.path.dirname(os.path.abspath(__file__)) + "/home.htm"
browser = webdriver.Firefox()
browser.implicitly_wait(5)
browser.get(myUrl)

area = browser.find_element_by_xpath("//area[contains(@alt, 'Query Performed Tests')]")

"""clicks on it"""
test = ActionChains(browser)
test.click(area)
test.perform()

listTakenIDRecherche = [3401783, 3401784, 3401787, 3401790, 3401803]

"""finds the test_taken_id input and writes the list that we are looking for"""
browser.find_element_by_name('test_taken_id').send_keys(listTakenIDRecherche)

"""finds the submit button"""
t = browser.find_element_by_name('sabutton')
"""clicks on it"""
t.click()
t.click() # Click twice in case the first click just re-focused the window.
t.submit()

parser = matsHTMLParser()
"""feeds this page to parser"""

matsReadPage()

"""gets global result"""

listResultByTakenID = parser.getResultByTakenID()

print listResultByTakenID

# stringResultByTakenID = json.dumps(dictResultByTakenID)
# with open('resultMats_ByTakenID_v2.txt' , 'wb') as f1:
#   f1.write(stringResultByTakenID


#writeHead doesn't work now!
# csvHead = (['takenID'] + ['verifiedDate'] + ['serialNo'] + ['testID'] + ['Status'] + ['failLogLink'])
listToCsv( 'Result_v3.csv', listResultByTakenID )


 
  



