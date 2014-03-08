# -*- coding: utf8 -*-
# Extracteur 

"""  
Some explanations about this script :

1. input : 1 list of serial numbers (listTakenIDRecherche). Input is made at line 797.

1. output : 2 CSV files showing the infos we need about those MATs. Output are made at lines 798 and 802 : 
       - Mats.csv : columns = timestamp, takenID, serialNo, testID, status, failLogLink link when it exists
       - Relative_TFLs.csv  : columns = timestamp, takenID, serialNo, testID, remarks, repeat Operations

2. process ( in MAIN, starting line 783 ) :
       1 - We log onto eQuality HomePage with an emulated selenium webbrowser
       2 - We go to the MatsResult Page that matches our input list, using selenium API.
       3 - We parse it and save what we need into Mats.csv.
       4 - We go to the TFLResult Page that sums up the TFLs we found while parsing the MatsResult Page parsing.
       5 - We parse it and save what we need into Relative_TFLs.csv.

3. classes : We implemented 2 classes based on python HTMLParser, adapting it to the MatsResult pages and to the TFLResult pages :
       - MatsParser ( line 60 ):
           Methods : - initTemporaryResultsAndCounters ( self ) : resets current result and counters
                     - feed ( self, html )                      : feeds one page
                     - feedEveryPage ( self, browser )          : feeds all of the MatsResult pages
                     - timeStamp ( self, matsTime )             : converts the Mats Verified Date into a timeStamp
                     - handle_starttag ( self, tag, attrs )     : handles html starttag
                     - handle_endtag ( self, tag )              : handles html endtag
                     - handle_data ( self, data )               : handles data
                     - endOfTr ( self )                         : appends current result to global result
                     - getResultByTakenID ( self )              : gets global result
       - TFLParser ( line 314 ):
           Methods : - initTemporaryResultsAndCounters ( self ) : resets current result and counters
                     - feed ( self, html )                      : feeds one page
                     - feedEveryPage ( self, browser )          : feeds all of the MatsResult pages
                     - timeStamp ( self, matsTime )             : converts the Mats Verified Date into a timeStamp
                     - handle_starttag ( self, tag, attrs )     : handles html starttag
                     - handle_endtag ( self, tag )              : handles html endtag
                     - handle_data ( self, data )               : handles data
                     - endOfTr ( self )                         : appends current result to global result
                     - getResultByTakenID ( self )              : gets global result

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


"""""""""""""""""""""""""""      CLASSES      """""""""""""""""""""""""""


""" MatsParser definition, to create a controller that will help us to parse a MatsResult Page """
class MatsParser(HTMLParser):
    
    def __init__(self, dbTakenID= [] ):
        HTMLParser.__init__(self)

        self.table = False
        self.tr = False
        self.td = False
        self.b = False
        self.a = False

        self.resultsByTakenID = dbTakenID
        self.initTemporaryResultsAndCounters()

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

        self.takenIDCol = 0
        self.modifiedDateCol = 29
        self.serialNoCol = 24
        self.testIDCol = 1
        self.statusCol = 6
        self.failLogLinkCol = 34

        self.listCol = [ self.modifiedDateCol, self.takenIDCol, self.serialNoCol, \
                    self.testIDCol, self.statusCol, self.failLogLinkCol]

        self.lengthResultCol = 35
    
    def initTemporaryResultsAndCounters(self):
        """ result is the temporary 'one row' result. It's appended to resultsByTakenID (which is the real result)
        and then deleted in endOfTR, called at the end of each html table row """
        self.result = ['']* 6 
        self.pagesNb = 0
        self.currentPageNo = 0
        self.pageRowStart = 0
        self.pageRowEnd = 0
        self.resultsNb = 0

        """ counters """
        self.tablei = 0 
        self.tdi = 0 
        self.bi = 0 
        self.tri = 0 

    """ feeds one html page """
    def feed(self, html):
        self.initTemporaryResultsAndCounters()
        HTMLParser.feed(self, html)
        # In order to check that we have parsed new values (from a new page).
        return self.pageRowStart

    """ if several, feeds all of the MatsResult pages """
    def feedEveryPage(self, browser):
        pageWebSource = browser.page_source.encode('utf8')        
        # parser.feed return pageRowStart(type int)
        rowStart = self.feed(pageWebSource) 
        # Go to the next pages if any.
        pageNbTotal = self.pagesNb
        if pageNbTotal > 1:
            newRowStart = rowStart # In order to check that we parse new results.
            i = 2 # Page 1 is already parsed.
            while i <= pageNbTotal:
                while newRowStart == rowStart:
                    #link = browser.find_elements_by_link_text(str(i))
                    #link = link[0].find_elements_by_tag_name('font')[0]
                    link = browser.find_elements_by_link_text(str(i))                
                    if len(link) == 0:

                        # Try to find a "More pages" link.
                        # eQ displays page links by group of 10 only.

                        #  .... code to write ...

                        link = browser.find_elements_by_link_text("More->>")[0]
                    else:
                        link = link[0].find_elements_by_tag_name('font')[0]

                    # Before any mouse action, re-focus on the window in case the
                    # user has clicked away.
                    browser.switch_to_active_element()
                    link.click()
                    # pstepii("Page {0}/{1}", i, t)
                    newRowStart = self.feed(browser.page_source.encode('utf8'))
                    # g_c.dec()
                rowStart = newRowStart
                i += 1

    """turns the Mats Verified Date into a timestamp"""
    def timeStamp (self, matsTime):

        thisMatsDateTime = datetime.datetime.strptime(matsTime, \
                                                     '%d-%b-%Y %I:%M %p')

        #thisMatsDateTime = datetime.datetime.strptime(matsTime, \
        #                                             '%d-%b-%Y\xc2\xa0%I:%M %p')
        epoch = datetime.datetime.utcfromtimestamp(0)
        delta = thisMatsDateTime - epoch
        thisMatsTimeStamp = int(delta.total_seconds())
        return str(thisMatsTimeStamp)

    def handle_starttag(self, tag, attrs):
        """ tables counter is incremented at start tag """ 
        if tag == 'table':
            self.table = True
            self.tablei += 1 
            # if self.tablei == 3:
            #     g_c.inc()
        """ rows and cells counters will be at end tag """
        if tag == 'tr' and self.table:
            self.tr = True

        elif tag == 'td' and self.tr:
            self.td = True
        
        elif (tag == 'b' or tag == 'strong') and self.td:
            """bold tags also need to be counted, especially for the feedEveryPage method """
            self.b = True
            self.bi += 1
            
        elif (tag == 'a') and self.td and self.tdi == self.failLogLinkCol:
            """ in case of link to a TFL in the row, adds 'true' at the right position of result """
            for name, value in attrs :
                if name == "href" :
                    self.result[self.listCol.index(self.failLogLinkCol)] = value
            
    def handle_endtag(self, tag):
        
        if tag == 'table':
            self.table = False
            self.tr = False
            self.td = False
            self.b = False

            self.tri = 0

            """ incrementation of rows and cells counters, as promised """
        elif tag == 'tr':
            self.tr = False
            self.td = False
            self.b = False

            self.tri += 1

            self.endOfTr()

            """ Re-initialization of cells counter and temporary result."""
            self.tdi = 0
            self.result = [''] * 6
        
        elif tag == 'td':
            self.td = False
            self.b = False


            self.tdi += 1 
            self.bi = 0 

        elif tag == 'b' or tag == 'strong':
            self.b = False

    def handle_data(self, data):
        """ Table 1 contains infos about the current page and the total number
        of pages to parse, valuable for the feedEveryPage method """
        if self.tablei == 1 and self.b:
            if self.bi == 3:
                self.pagesNb = int(data)
                if self.pagesNb == 1:
                    self.bi += 1 # only 1 page => no page link (in which there would else be one bold balise) 
                    self.currentPageNo = 1
            elif self.bi == 4 and self.pagesNb > 1:
                self.currentPageNo = int(data)
                # if self.currentPageNo == 1:
                #     pstepi("Found {0} page(s).", self.pagesNb)
            elif self.bi == 5:
                self.pageRowStart = int(data.lstrip('Rows '))
            elif self.bi == 6:
                self.pageRowEnd = int(data)

            """table 2 contains infos about the total number of rows to parse """
        elif self.tablei == 2 and self.b:
            self.resultsNb = int(data)
            # if self.currentPageNo == 1:
            #     pstepi("Found {0} result(s) in total.", data)
            # if self.pagesNb > 1:
            #     pstepi("Getting results #{0} to #{1}", self.pageRowStart,
            #            self.pageRowEnd)

            """table 3 contains the actual datas that we want """
        elif self.tablei == 3 :
            """ we check wether we are in one of the interesting columns. If we do, we store the datas in result"""
            if self.tdi < self.lengthResultCol and self.td and self.tdi in self.listCol:
                indexCol = self.listCol.index(self.tdi)
                if self.tdi != self.failLogLinkCol:   
                    if self.result[indexCol] == '':
                        self.result[indexCol] = data.replace("\xc2\xa0", " ")
                    else:
                        self.result[indexCol] += ' ' + data.replace("\xc2\xa0", " ")        

    """ called at the end of each html table row, endOfTr appends the current result to resultsByTakenID """            
    def endOfTr(self):
        # If we have found all cells (td), then transfer temporary result
        # into classified result.
        if self.tablei == 3 and self.tdi == self.lengthResultCol :            
            r = self.result
            # transform matsTime to matsTimeStamp
            r[self.listCol.index(self.modifiedDateCol)] = self.timeStamp(r[self.listCol.index(self.modifiedDateCol)])            
                          
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

    """ gets the global result : the list of lists showing the datas we need """
    def getResultByTakenID(self):
        return self.resultsByTakenID

    # def getResultByWoIDSerialNoTakenID(self):
    #     return self.resultsByWoIDSerialNoTakenID



""" TFLParser definition, to create a controller that will help us to parse a MatsResult Page """
class TFLParser(HTMLParser):
    
    def __init__(self, dbTakenID= [] ):
        HTMLParser.__init__(self)

        self.table = False
        self.tr = False
        self.td = False
        self.b = False
        self.a = False

        self.resultsByTakenID = dbTakenID
        self.initTemporaryResultsAndCounters()

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

        self.takenIDCol = 0
        self.testIDCol = 1
        self.DateCol = 3        
        self.RemarksCol = 17
        self.RepeatOperationsCol = 21
        self.serialNumberCol = 29

        self.listCol = [ self.DateCol, self.takenIDCol, self.serialNumberCol, self.testIDCol, self.RemarksCol, self.RepeatOperationsCol]

        self.lengthResultCol = 39

    def initTemporaryResultsAndCounters(self):
        """ result is the temporary 'one row' result. It's appended to resultsByTakenID (which is the real result)
        and then deleted in endOfTR, called at the end of each html table row """
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

    """ feeds one html page """
    def feed(self, html):
        self.initTemporaryResultsAndCounters()
        HTMLParser.feed(self, html)
        # In order to check that we have parsed new values (from a new page).
        return self.pageRowStart

    """ if several, feeds all of the MatsResult pages """
    def feedEveryPage(self, browser):

        pageWebSource = browser.page_source.encode('utf8')

        
        # parser.feed return pageRowStart(type int)
        rowStart = self.feed(pageWebSource) 

        # Go to the next pages if any.
        pageNbTotal = self.pagesNb
        if pageNbTotal > 1:
            newRowStart = rowStart # In order to check that we parse new results.
            i = 2 # Page 1 is already parsed.
            while i <= pageNbTotal:
                while newRowStart == rowStart:
                    #link = browser.find_elements_by_link_text(str(i))
                    #link = link[0].find_elements_by_tag_name('font')[0]
                    link = browser.find_elements_by_link_text(str(i)) 
                    if len(link) == 0:

                        # Try to find a "More pages" link.
                        # eQ displays page links by group of 10 only.

                        #  .... code to write ...

                        link = browser.find_elements_by_link_text("More->>")[0]
                    else:
                        link = link[0].find_elements_by_tag_name('font')[0]

                    # Before any mouse action, re-focus on the window in case the
                    # user has clicked away.
                    browser.switch_to_active_element()
                    link.click()
                    # pstepii("Page {0}/{1}", i, t)
                    newRowStart = self.feed(browser.page_source.encode('utf8'))
                    # g_c.dec()
                rowStart = newRowStart
                i += 1
                
    """turns the TFL Date into a timestamp"""
    def timeStamp (self, TFLDate):

        thisTFLDate = datetime.datetime.strptime(TFLDate, \
                                                     '%d-%b-%Y')

        epoch = datetime.datetime.utcfromtimestamp(0)
        delta = thisTFLDate - epoch
        thisTFLTimeStamp = int(delta.total_seconds())
        return str(thisTFLTimeStamp)
    
    def handle_starttag(self, tag, attrs):
        """ tables counter is incremented at start tag """ 
        if tag == 'table':
            self.table = True
            self.tablei += 1 
            # if self.tablei == 3:
            #     g_c.inc()
            
            """ rows and cells counters will be at end tag """
        if tag == 'tr' and self.table:
            self.tr = True
        
        elif tag == 'td' and self.tr:
            self.td = True
            
            """bold tags also need to be counted, especially for the feedEveryPage method """
        elif (tag == 'b' or tag == 'strong') and self.td:
            self.b = True
            self.bi += 1        

    def handle_endtag(self, tag):
        
        if tag == 'table':
            self.table = False
            self.tr = False
            self.td = False
            self.b = False

            self.tri = 0
            # if self.tablei == 3:
            #     g_c.dec()
            
            """ incrementation of rows and cells counters, as promised """
        elif tag == 'tr':
            self.tr = False
            self.td = False
            self.b = False

            self.tri += 1

            self.endOfTr()

            """ Re-initialization of cells counter and temporary result."""
            self.tdi = 0
            self.result = [''] * 6
        
        elif tag == 'td':
            self.td = False
            self.b = False

            self.tdi += 1 
            self.bi = 0 

        elif tag == 'b' or tag == 'strong':
            self.b = False

    def handle_data(self, data):
        """ Table 1 contains infos about the current page and the total number
        of pages to parse, valuable for the feedEveryPage method """
        if self.tablei == 1 and self.b:
            if self.bi == 3:
                self.pagesNb = int(data)
                if self.pagesNb == 1:
                    self.bi += 1 # only 1 page => no page link (in which there would else be one bold balise) 
                    self.currentPageNo = 1
            elif self.bi == 4 and self.pagesNb > 1:
                self.currentPageNo = int(data)
                # if self.currentPageNo == 1:
                #     pstepi("Found {0} page(s).", self.pagesNb)
            elif self.bi == 5:
                self.pageRowStart = int(data.lstrip('Rows '))
            elif self.bi == 6:
                self.pageRowEnd = int(data)

            """table 2 contains infos about the total number of rows to parse """
        elif self.tablei == 2 and self.b:
            self.resultsNb = int(data)
            # if self.currentPageNo == 1:
            #     pstepi("Found {0} result(s) in total.", data)
            # if self.pagesNb > 1:
            #     pstepi("Getting results #{0} to #{1}", self.pageRowStart,
            #            self.pageRowEnd)

            """table 3 contains the actual datas that we want """
        elif self.tablei == 3 :
            """ we check wether we are in one of the interesting columns. If we do, we store the datas in result"""
            if self.tdi < self.lengthResultCol and self.td and self.tdi in self.listCol:
                indexCol = self.listCol.index(self.tdi)
                if self.result[indexCol] == '':
                    self.result[indexCol] = data.replace("\xc2\xa0", " ").replace("\n", " ")
                else:
                    self.result[indexCol] += ' ' + data.replace("\xc2\xa0", " ").replace("\n", " ")
                    
    """ called at the end of each html table row, endOfTr appends the current result to resultsByTakenID """                        
    def endOfTr(self):
        # If we have found all cells (td), then transfer temporary result
        # into classified result.
        if self.tablei == 3 and self.tdi == self.lengthResultCol :            
            r = self.result
            # transform matsTime to matsTimeStamp
            r[self.listCol.index(self.DateCol)] = self.timeStamp(r[self.listCol.index(self.DateCol)])            
                          
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

    """ gets the global result : the list of lists showing the datas we need """
    def getResultByTakenID(self):
        return self.resultsByTakenID

    # def getResultByWoIDSerialNoTakenID(self):
    #     return self.resultsByWoIDSerialNoTakenID

"""""""""""""""""""""""""""      CONVENIENCE FUNCTIONS     """""""""""""""""""""""""""


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

""" writes a list into a csv file in current directory """
def listToCsv ( csvFileName, listName):
    with open(csvFileName, 'wb') as f:
        writer = csv.writer(f, delimiter=',')
        # writer.writerows(csvHead)
        writer.writerows(listName)


""" generates a list of the takenIDs for which there has been a TFL
    from the MatsParser.ResultByTakenID """
def getTFLTakenID(listResult) :
    TFLTakenID = []
    for item in listResult :
        if str(item[5]) != "" :
            TFLTakenID.append(item[0])
    return TFLTakenID






def switchToFrameMainMenu(myDriver): 
    #Loop to access SLB Domain.
    #If not in SLB Domain, eQ prompts a basic HTTP authentication (modal
    #dialog) that cannot be handled by Selenium. The user must enter his
    #LDAP credentials.
    machineInSlbDomain = False
    while not machineInSlbDomain:
        try:
            #time.sleep(3)
            focusDefaultContent(myDriver)
            #myDriver.switch_to_default_content()            
            #t = myDriver.find_element_by_x_path("//frame[contains(@name, 'main_menu')]")
            # print "found element"
            myDriver.switch_to_frame(myDriver.find_element_by_name("main_menu"))
            # print "switched"
            machineInSlbDomain = True
            
        except:
            #p_("Cannot access the frame.")
            #p_("eQuality may be prompting for login.")
            #p_("Refreshing the page to reload the login prompt.")
            myDriver.get(myUrl)
            #p_("Please login within the next {0} second(s).",
            #g_param[waitLogin)
            time.sleep(waitLogin)


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


# Re-focus on the window before any mouse action.
def focusActiveElement(myDriver):
    myDriver.switch_to_active_element()

def focusDefaultContent(myDriver):
    myDriver.switch_to_default_content()

def split255(seqLong, maxIdLen):
    seqSplit = []
    while len(seqLong) > 255:
        for i in range(0 , maxIdLen):
            if seqLong[254 - i] ==',':
                seqSplit.append(seqLong[ : 254 - i ])
                seqLong = seqLong[ 255 - i : ]
                break
    seqSplit.append(seqLong)
    return seqSplit

def matsGo(browser, listMats):

    myMatsListResult = []
    print '=== listMats === ' , '\n', listMats, '\n'

    listMatsSplit = split255(listMats,maxIdLen)
    print '=== listMatsSplit === ' , '\n',  listMatsSplit, '\n'

    while listMatsSplit :    

        browser.get(myUrl)
        # browser.implicitly_wait(5)
        switchToFrameMainMenu(browser)

        """ finding the MatsQuery area"""
        area = browser.find_element_by_xpath("//area[contains(@alt, 'Query Performed Tests')]")

        """ clicking on it """
        focusActiveElement(browser)
        test = ActionChains(browser)
        test.click(area)
        test.perform()
        
        """ writing the list in the takenID input """
        browser.find_element_by_name('serial_no').send_keys(listMatsSplit.pop())

        """ finding the submit button """
        t = browser.find_element_by_name('sabutton')

        """clicking on it """
        focusActiveElement(browser)
        t.click()
        t.click() # Click twice in case the first click just re-focused the window.
        t.submit()

        """ getting the result list of the datas we need from this MatsQueryResult page """
        myMatsparser = MatsParser()
        myMatsparser.feedEveryPage(browser)
        # myMatsListResultByTakenID.append(myMatsparser.getResultByTakenID())
        myMatsListResult += myMatsparser.getResultByTakenID()

    print '=== myMatsListResult ===', '\n', myMatsListResult, '\n'

    # stringResultByTakenID = json.dumps(dictResultByTakenID)
    # with open('resultMats_ByTakenID_v2.txt' , 'wb') as f1:
    #   f1.write(stringResultByTakenID

        
    #writeHead doesn't work now!
    # csvHead = (['takenID'] + ['verifiedDate'] + ['serialNo'] + ['testID'] + ['Status'] + ['failLogLink'])

    """ saving it into Mats.csv """
    listToCsv( 'Mats.csv', myMatsListResult )

    return myMatsListResult

def TFLGo(browser, listTFL ,maxIdLen):

    myTFLListResult = []
    listTFLSplit = []

    print '=====listTFL=== ', ' \n', listTFL, '\n'

    listTFLSplit = split255(listTFL,maxIdLen)
    print '=== listTFLSplit === ' , '\n',  listTFLSplit, '\n'

    while listTFLSplit :
  
        """ going back to home page """
        browser.get(myUrl)
        switchToFrameMainMenu(browser)

        """ finding the TFLQuery image """
        img = browser.find_element_by_xpath("//img[contains(@alt, 'Test Failed')]")

        """ clicking on it """
        focusActiveElement(browser)
        test = ActionChains(browser)
        test.click(img)
        test.perform()

        """ writing the list into the takenID input """
        browser.find_element_by_name('test_taken_id').send_keys(listTFLSplit.pop())

        """ finding the submit button """
        t = browser.find_element_by_name('sabutton')

        """ clicking on it """
        focusActiveElement(browser)
        t.click()
        t.click() # Click twice in case the first click just re-focused the window.
        t.submit()

        """ getting the result list of the datas we need from this MatsQueryResult page """
        myTFLparser = TFLParser()
        myTFLparser.feedEveryPage(browser)
        myTFLListResult += myTFLparser.getResultByTakenID()        

    listToCsv( 'Relative_TFLs.csv', myTFLListResult )

    print '=== myTFLListResult === ' , '\n', myTFLListResult, '\n'
    return myTFLListResult



########## Test with resultMats.htm #######################################

# with open ('resultMats.htm', 'r') as source:
#   pageWebSource = source.read()


"""""""""""""""""""""""""""      MAIN     """""""""""""""""""""""""""


waitLogin = 15
maxIdLen = 15

""" loading the eQuality home page on a firefox browser """
# myUrl is a global variable
myUrl = "file:///" + os.path.dirname(os.path.abspath(__file__)) + "/home.htm"   # WRITE eQUALITY HOME PAGE URL HERE !
#myUrl = "http://www.equality-eur.slb.com"
browser = webdriver.Firefox()
browser.implicitly_wait(5)

""" MatsRecherche """
listMats = str([3401783, 3401784, 3401787, 3401790, 3401803]).replace(" ', '", ",")[2:-2]
myMatsListResult = matsGo(browser, listMats)

""" TFLRecherche """
listTFL = str(getTFLTakenID(myMatsListResult)).replace(" ', '", ",").replace("'","")[2:-2]
myTFLListResult = TFLGo(browser,listTFL,maxIdLen)

print  '=== END of Extractor Test==='


