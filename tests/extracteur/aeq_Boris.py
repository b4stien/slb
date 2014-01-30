##############################################################################
##  FILE DESCRIPTION
###############################################################################

"""  Automate eQuality
Copyright (c) 2012-2013 B.Seang , Schlumberger.
Works with June 2012 version of eQuality.
This script performs the following actions:
1. Open Microsoft Internet Explorer.
2. Connect to eQuality website. If auto-login does not work, eQuality
   prompts the user for login data.
3. Search for a list of serial_no/wo_id and retrieve list of performed tests.
4. Record this data into a text file.
"""


###############################################################################
##  IMPORTS
###############################################################################

# Selenium WebDriver modules
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait

# Common modules
from collections import defaultdict # For easy dict arrays setting up.
from datetime import date # For dates manipulation.
from datetime import timedelta # For dates manipulation.
import json # For local database formatting.
import csv # For local database formatting.
import time # For timeouts.
import os.path # For file I/O.
import inspect # To get the current path and file name.
#import re # For regular expressions.
from HTMLParser import HTMLParser # To parse HTML content.


###############################################################################
##  CLASSES
###############################################################################

# Controller to parse MATS test_perform query result HTML page.
class matsQueryResultHTMLParser(HTMLParser):
    def __init__(self, dbTakenID={}, dbWoIDSerialNoTakenID=defaultdict(dict)):
        HTMLParser.__init__(self)

        self.table = False
        self.tr = False
        self.td = False
        self.b = False
        self.a = False

        self.resultsByTakenID = dbTakenID
        self.resultsByWoIDSerialNoTakenID = dbWoIDSerialNoTakenID
        self.initTemporaryResultsAndCounters()

        # Columns: TakenID, TestID, Version, Dated, Site, Try, Status, WO ID,
        #    Name (test), Category, Technician, Part (P/N), Department,
        #    SerialNo, VerifiedDate, Test Taken (link), Fail Log (link).
        self.cols = 'takenID', 'testID', 'testVersion', 'takenDate',\
            'site', 'tryNo', 'status', 'woID', 'po', 'line', 'testName',\
            'category', 'technician', 'wo', 'wc', 'operation', 'partNo',\
            'partDesc', 'rev', 'department', 'qaproc', 'prodLine', 'plDesc',\
            'project', 'serialNo', 'parentSN', 'supplierNo', 'supplierName',\
            'performedDate', 'modifiedDate', 'verifiedBy', 'verifiedDate',\
            'remarks','testEditLink', 'failLogLink'

    def feed(self, html):
        self.initTemporaryResultsAndCounters()
        HTMLParser.feed(self, html)
        # In order to check that a we have parsed new values (from a new page).
        return self.pageRowStart

    def initTemporaryResultsAndCounters(self):
        self.result = {} # Temporary result.
        self.pagesNb = 0
        self.currentPageNo = 0
        self.pageRowStart = 0
        self.pageRowEnd = 0
        self.resultsNb = 0

        self.tablei = 0 # Tables counter.
        self.tdi = 0 # Cells counter.
        self.bi = 0 # Bold text counter.

    def handle_starttag(self, tag, attrs):
        # Detect tables (table).
        if tag == 'table':
            self.table = True
            self.tablei += 1 # Tables counter.
            if self.tablei == 3:
                g_c.inc()
        # Detect table lines (tr) nested in table (table).
        if tag == 'tr' and self.table:
            self.tr = True
        # Detect table cells (td) nested in lines (tr).
        elif tag == 'td' and self.tr:
            self.td = True
        # Detect bold text (b or strong) nested in cell (td).
        elif (tag == 'b' or tag == 'strong') and self.td:
            self.b = True
            self.bi += 1 # Bold text counter.
        # Detect link (a) to TFL nested in cell (td).
        elif tag == 'a' and self.td and self.cols[self.tdi] == 'failLogLink':
            self.result[self.cols[self.tdi]] = True

    def handle_endtag(self, tag):
        # End of table line (tr).
        if tag == 'table':
            self.table = False
            self.tr = False
            self.td = False
            self.b = False
            if self.tablei == 3:
                g_c.dec()
        elif tag == 'tr':
            self.tr = False
            self.td = False
            self.b = False

            self.endOfTr()

            # Re-initialize cells counter and temporary result.
            self.tdi = 0
            self.result = {}

        # End of cell (td)
        elif tag == 'td':
            self.td = False
            self.b = False

            # If the cell was associated with TFL link, set the temporary
            # result to False if it has not been set previously by the presence
            # of a link in the cell.
            if (self.cols[self.tdi] == 'failLogLink'
                and not self.cols[self.tdi] in self.result
                ):
                self.result[self.cols[self.tdi]] = False

            self.tdi += 1 # Cells counter.
            self.bi = 0 # Re-initialize bold text counter.

        elif tag == 'b' or tag == 'strong':
            self.b = False

    def handle_data(self, data):
        # For table #1, get number of pages.
        if self.tablei == 1 and self.b:
            if self.bi == 3:
                self.pagesNb = int(data)
                if self.pagesNb == 1:
                    self.bi += 1 # If only 1 page, no page links are displayed.
                    self.currentPageNo = 1
            elif self.bi == 4 and self.pagesNb > 1:
                self.currentPageNo = int(data)
                if self.currentPageNo == 1:
                    pstepi("Found {0} page(s).", self.pagesNb)
            elif self.bi == 5:
                self.pageRowStart = int(data.lstrip('Rows '))
            elif self.bi == 6:
                self.pageRowEnd = int(data)

        # For table #2, get total number of results.
        elif self.tablei == 2 and self.b:
            self.resultsNb = int(data)
            if self.currentPageNo == 1:
                pstepi("Found {0} result(s) in total.", data)
            if self.pagesNb > 1:
                pstepi("Getting results #{0} to #{1}", self.pageRowStart,
                       self.pageRowEnd)

        # Record data for table #3 (actual list of tests taken).
        elif self.tablei == 3:
            t = self.cols[self.tdi]
            if (self.td
                and t != 'failLogLink'
                and t != 'testEditLink'
                ):
                if t not in self.result:
                    self.result[t] = data
                else:
                    self.result[t] += ' ' + data

    def endOfTr(self):
        # If we have found all cells (td), then transfer temporary result
        # into classified result.
        if self.tablei == 3 and self.tdi == len(self.cols):
            r = self.result

            woID = getDictKey(r, 'woID', 'None')
            serialNo = getDictKey(r, 'serialNo', 'None')
            takenID = getDictKey(r, 'takenID', 'None')

            # Print some progress comments.
            pstepi("Recording test taken {0}, for S/N {1}, in WO {2}.", \
                  takenID, serialNo, woID)

            # Insert the test taken dict into:
            # takenID > testData.
            self.resultsByTakenID[takenID] = r

            # Initialize the dicts if necessary.
            # The first dict does not need initialization thanks to
            # defaultdict. For some reason, a defaultdict of defaultdict
            # does not work.
            initDict(self.resultsByWoIDSerialNoTakenID[woID], serialNo)

            # Insert the test taken dict into:
            # woID > serialNo > takenID > testData.
            self.resultsByWoIDSerialNoTakenID[woID][serialNo][takenID] = r

    def getResultByTakenID(self):
        return self.resultsByTakenID

    def getResultByWoIDSerialNoTakenID(self):
        return self.resultsByWoIDSerialNoTakenID

# Controller to manage the session with eQuality.
# It handles the login issues.
class EqSession():
    def __init__(self):
        self.start()

    def goToMatsPerformQuery(self):
        # Try to find "Return to search page" link.
        t = g_bd.d.find_elements_by_link_text('Return')
        if len(t) > 0:
            self.focusActiveElement()
            t[0].click()
            time.sleep(g_param['waitMainMenu']/2)
            return

        # Otherwise, assume we are on the main menu and try to click on
        # MATS Perform Query image.
        else:
            imgs = g_bd.d.find_elements_by_tag_name('img')
            i=1
            for img in imgs:
                if (img.get_attribute('src').find(g_mats['imageLinkPerform'])\
                    >= 0
                    ):
                    test = ActionChains(g_bd.d)
                    test.move_to_element_with_offset(img, 158, 1)
                    test.click()
                    self.focusActiveElement()
                    test.perform()
                    # Give some time for the click to take effect.
                    time.sleep(g_param['waitMainMenu'])
                    return

            # If no appropriate image/link has been found, go back to eQ home
            # and try again.
            self.goToHome()
            return self.goToMatsPerformQuery()

    def start(self):
        pstepi("Opening eQuality.")
        g_bd.d.get(g_eq['url'])
        
        pstepi("Finding the main frame.", 1)
        self.switchToFrameMainMenu()
        
        # Try to get an element to check if eQ displays a login page.
        userAuthenticated = False
        while not userAuthenticated:
            try:
                g_bd.d.find_element_by_name('password')
                p_("eQuality requests login.")
                p_("Please login within the next {0} second(s).",
                   g_param['waitLogin'])
                time.sleep(g_param['waitLogin'])
                g_bd.d.get(g_eq['url'])
                self.switchToFrameMainMenu()
            except NoSuchElementException:
                userAuthenticated = True

    def goToHome(self):
        self.switchToFrameToolbar()
        imgs = g_bd.d.find_elements_by_tag_name('img')
        for img in imgs:
            if (img.get_attribute('src').find(g_eq['imageLinkHome'])\
                >= 0
                ):
                self.focusActiveElement()
                img.click()
                # Give some time for the click to take effect.
                time.sleep(g_param['waitMainMenu'])
                self.switchToFrameMainMenu()
                return

    def switchToFrameMainMenu(self):
        # Loop to access SLB Domain.
        # If not in SLB Domain, eQ prompts a basic HTTP authentication (modal
        # dialog) that cannot be handled by Selenium. The user must enter his
        # LDAP credentials.
        machineInSlbDomain = False
        while not machineInSlbDomain:
            try:
                self.focusDefaultContent()
                #g_bd.d.switch_to_default_content()
                t = g_bd.d.find_element_by_name(g_eq['frameMainMenu'])
                g_bd.d.switch_to_frame(t)
                machineInSlbDomain = True
            except:
                p_("Cannot access the frame.")
                p_("eQuality may be prompting for login.")
                p_("Refreshing the page to reload the login prompt.")
                g_bd.d.get(g_eq['url'])
                p_("Please login within the next {0} second(s).",
                   g_param['waitLogin'])
                time.sleep(g_param['waitLogin'])

    def switchToFrameToolbar(self):
        self.focusDefaultContent()
        t = g_bd.d.find_element_by_name(g_eq['frameToolbar'])
        g_bd.d.switch_to_frame(t)

    # Re-focus on the window before any mouse action.
    def focusActiveElement(self):
        g_bd.d.switch_to_active_element()

    def focusDefaultContent(self):
        g_bd.d.switch_to_default_content()

# Controller for Internet browser driver.
# For now, it uses only Microsoft Internet Explorer.
class BrowserDriver():
    def __init__(self):
        pstepi("Starting a new instance of Internet Explorer.")
        
        # Specify to ignore IE protected mode settings for Win 64-bits
        # machines. Otherwise, IEDriver requires that the protected mode
        # settings are the same for all zones, which is rarely the case,
        # so the driver cannot start.
        webdriver.DesiredCapabilities.\
            INTERNETEXPLORER['ignoreProtectedModeSettings'] = True
        
        # Start the driver.
        try:
            self.d = webdriver.Ie()
            #self.d = webdriver.Ie(executable_path= \
            #    "C:\\Python27\\AutomateEQuality\\IEDriverServer.exe")
        except:
            p_("Cannot automate Microsoft Internet Explorer.")
            raise

        # Set the size of the window.
        # Typically this allows the user to keep a view of what is happening
        # in the console, and of eQdisplay if present.
        self.d.set_window_size(g_param['windowWidth'], g_param['windowHeight'])
    
    def __del__(self):
        # Close the browser.
        pstepi("Closing the Internet browser.")
        self.d.quit()

# Program steps counter.
class Counter:
    def __init__(self, sep="."):
        self.sep = sep
        self.levels = []
        self.currentLevel = 0
    
    def get(self, level=0):
        txt = ""
        # Increase depth of levels if necessary
        while len(self.levels) <= level:
            self.levels.append(0)
        for i in range(len(self.levels)):
            if i < level: # Show parent levels
                if self.levels[i] == 0: # In case jumping levels
                    self.levels[i] = 1
                txt += str(self.levels[i]) + self.sep
            elif i == level: # Increment current level
                self.levels[i] += 1
                txt += str(self.levels[i])
            else: # Re-initialize child levels
                self.levels[i] = 0
        return txt

    def geti(self):
        return self.get(self.currentLevel)

    def inc(self, levels=1):
        self.currentLevel += int(levels)
        if self.currentLevel < 0:
            self.currentLevel = 0
        return self.currentLevel

    def dec(self, levels=-1):
        return self.inc(levels)


###############################################################################
##  FUNCTIONS
###############################################################################

def performTask(taskName, taskArg):
    # There is no "switch" statement in Python. Therefore, we will test each
    # task with "if/elif" conditions.

    # MATS read list of taken tests.
    if taskName == 'matsReadTestTakenList':
        if type(taskArg) is dict:
            pstepii("TASK: Read list of Tests Taken in MATS.")
            if len(taskArg) > 0:
                parser = matsQueryResultHTMLParser()

                # Perform the query for each input type.
                for queryBy, myList in taskArg.iteritems():
                    pstepii("MATS Perform query by '{0}'", queryBy)
                    performMatsTaskReadTestTakenList(queryBy, myList)
                    g_c.dec()

                # Save the result in file (localDb).
                p = g_p+g_db['dir']+g_db['dbFile']
                pstepi("Writing result in file '{0}'", p)
                if g_db['outputType'] == 'csv':
                    writeCsvFile(p, parser.getResultByTakenID())
                else:
                    jsonWriteFile(p, parser.getResultByTakenID())
                
                # Save the result in file (sharedDb).
                if g_sdb['enabled']:
                    pstepii("Preparing shared database")
                    r = parser.getResultByWoIDSerialNoTakenID()
                    for woID in r:
                        p = g_sdb['dir']+g_sdb['woidPrefix']+woID
                        ensureDir(p)
                        for serialNo in r[woID]:
                            p2 = p+'/'+g_sdb['snPrefix']+serialNo+ \
                                 g_sdb['fileSuffix']
                            # If the target file already exists,
                            # load its content.
                            if os.path.exists(p2):
                                pstepi("Updating file {0}.", p2)
                                t = jsonLoadFile(p2)
                                # Update the content in order not to lose data.
                                for takenID in r[woID][serialNo]:
                                    t[takenID] = r[woID][serialNo][takenID]
                            else:
                                pstepi("Creating file {0}.", p2)
                                t = r[woID][serialNo]
                            jsonWriteFile(p2, t)
                    g_c.dec()

            # No input type is defined in the task.
            else:
                p_("Nothing to do for task '{0}' in file '{1}'.", taskName,
                   g_db['dir']+g_db['tasksFile'])

            g_c.dec()

        # Task is not defined by a dict.
        else:
            p_("Task '{0}' is incorrectly defined in file '{1}'.",
               taskName, g_db['dir']+g_db['tasksFile'])

    # Unknown task name.
    else:
        p_("Unknown task name '{0}' in file '{1}'", taskName,
           g_db['dir']+g_db['tasksFile'])

def performMatsTaskReadTestTakenList(queryBy, myList):
    if queryBy in g_param['matsQueryBy']:
        
        if type(myList) is list:
            
            if len(myList) > 0:

                # Perform the query for each value.
                for value in myList:
                    if type(value) is dict:
                        text = json.dumps(value)
                    else:
                        text = value
                    pstepii("Value '{0}'.", text)
                    matsReadTests(queryBy, value)
                    g_c.dec()

            # No values are defined for the input.
            else:
                p_("No values specified for query input type '{0}' "+\
                   "in file '{1}'.", queryBy, g_db['dir']+g_db['tasksFile'])
        # Input is not defined with a list.
        else:
            p_("List for input '{0}' is incorrectly defined in file '{1}'.",
               queryBy, g_db['dir']+g_db['tasksFile'])
    # The input type is not allowed in configuration.
    else:
        p_("The requested MATS query input type '{0}' in file '{1}' is "+\
           "unknown in configuration file '{2}'.", queryBy,
           g_db['dir']+g_db['tasksFile'], g_configFile)

# Perform read MATS tests for the given input type and value.
def matsReadTests(queryBy, value):

    # Find the input element.
    eqSession.goToMatsPerformQuery()
    if queryBy == "composite" :
        if type(value) is dict:
            # Fill inputs following the priority list.
            # Upper first (index 0).
            for queryBy2 in g_mats['queryInputPriority']:
                if queryBy2 in value:
                    matsFindAndFillInput(queryBy2, value[queryBy2])
            # Now fill inputs which are not mentioned in the priority list.
            for queryBy2, value2 in value.iteritems():
                if queryBy2 not in g_mats['queryInputPriority']:
                    matsFindAndFillInput(queryBy2, value2)
        # Input is not define with a list.
        else:
            p_("List for input '{0}' is incorrectly defined in file '{1}'.",
               queryBy, g_db['dir']+g_db['tasksFile'])
            return
    else:
        matsFindAndFillInput(queryBy, value)

    # Choose Select All View Fields to parse all data from eQ.
    # By doing another action after sending keys, eQ javascript will refresh
    # the value of the search option ("Equal to" or "Like" if '%' is found in
    # the input value.
    t = g_bd.d.find_element_by_name(g_mats['selectAllViewFields'])
    t.click()
    t.click() # Click twice in case the first click just re-focused the window.
    
    t.submit() # Submit the query form.
    WebDriverWait(g_bd.d, 10) # Wait for the query result page.

    # Parse the Result page HTML.
    pstepii("Result page 1.")
    rowStart = parser.feed(g_bd.d.page_source)
    g_c.dec()

    # Go to the next pages if any.
    t = parser.pagesNb
    if t > 1:
        newRowStart = rowStart # In order to check that we parse new results.
        i = 2 # Page 1 is already parsed.
        while i <= t:
            while newRowStart == rowStart:
                
                link = g_bd.d.find_elements_by_link_text(str(i))
                if len(link) == 0:
                    # Try to find a "More pages" link.
                    # eQ displays page links by group of 10 only.
                    link = g_bd.d.find_elements_by_link_text( \
                        g_eq['linkTextMorePages'])[0]
                else:
                    link = link[0].find_elements_by_tag_name('font')[0]

                # Before any mouse action, re-focus on the window in case the
                # user has clicked away.
                g_bd.d.switch_to_active_element()
                link.click()
                pstepii("Page {0}/{1}", i, t)
                newRowStart = parser.feed(g_bd.d.page_source)
                g_c.dec()
            rowStart = newRowStart
            i += 1

# Find an input element and fill the value.
def matsFindAndFillInput(inputName, value):
    
    # Find the input element.
    inputElement = None
    while not inputElement:
        try:
            inputElement = g_bd.d.find_element_by_name(inputName)
        except NoSuchElementException:
            p_("Could not find the input '{0}'.", inputName)
            eqSession.goToMatsPerformQuery()

    # Fill the value, depending on the input type.
    if inputName not in g_mats["queryInputTypes"] \
    or g_mats['queryInputTypes'][inputName] == "text":
        if type(value) is dict:
            if value['type'] == 'dateFromToday':
                myDate = date.today()
                myTD = timedelta()
                if 'days' in value:
                    myTD += timedelta(days = value['days'])
                myDate += myTD
                # Ouput manipulated date with format "mm-dd-yyyy".
                inputElement.send_keys(myDate.strftime("%m-%d-%Y"))
        else:
            inputElement.send_keys(value)
    else:
        if g_mats['queryInputTypes'][inputName] == "selectAjax":
            inputElement.click()
            time.sleep(g_param['waitAjax'])
            # Reload the inpu element
            inputElement = g_bd.d.find_element_by_name(inputName)
        if g_mats['queryInputTypes'][inputName] == "select" \
        or g_mats['queryInputTypes'][inputName] == "selectAjax":
            allOptions = inputElement.find_elements_by_tag_name("option")
            for option in allOptions:
                if option.get_attribute("value") == value:
                    option.click()
                    break

# Initialize a key as dict within a parent dict.
def initDict(parentDict, newKeyDict):
    if newKeyDict not in parentDict:
        parentDict[newKeyDict] = {}

# Get the value of the dict[key]. If the key is not defined yet, initialize
# it with the given default value.
def getDictKey(myDict, key, initValue=None):
    if key not in myDict:
        myDict[key] = initValue
    return myDict[key]

# Check if the directories of the given path exist, create them otherwise.
def ensureDir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

# Get the absolute path to current script location.
def getPath():
    p = os.path.dirname(inspect.getfile(inspect.currentframe()))
    return p.rstrip('.')

# Print a string with step number from counter level and increment + format
# if specified.
def pstepii(string, *args):
    print g_c.geti(), _(string, *args)
    g_c.inc()

# Print a string with step number from counter level and set level + format
# if specified.
def pstepil(string, level=0, *args):
    g_c.currentLevel = level
    print g_c.geti(), _(string, *args)

# Print a string with step number from counter level + format if specified.
def pstepi(string, *args):
    print g_c.geti(), _(string, *args)

# Print a string with step number + format if specified.
def pstep(string, level=0, *args):
    g_c.currentLevel = 0
    print g_c.get(level), _(string, *args)

# Print a string, with formatting if necessary.
def p_(string, *args):
    if len(args) > 0:
        print _(string.format(*args))
    else:
        print _(string)

# Translation function. It also formats the string if more args are specified.
def _(string, *args):
    if string in g_i18n:
        string = g_i18n[string]
    if len(args) > 0:
        return string.format(*args)
    return string

# Encode text into UTF-8, if it is text.
def utf8encode(text):
    if type(text) is str or type(text) is unicode:
        return text.encode('utf8')
    return text

# Open a file as CSV format, write a dict of dict (format ANY > Columns)
# as rows of the CSV file and close the file.
def writeCsvFile(filePath, myDict):
    fieldNames = 'takenID', 'testID', 'testVersion', 'takenDate',\
            'site', 'tryNo', 'status', 'woID', 'po', 'line', 'testName',\
            'category', 'technician', 'wo', 'wc', 'operation', 'partNo',\
            'partDesc', 'rev', 'department', 'qaproc', 'prodLine', 'plDesc',\
            'project', 'serialNo', 'parentSN', 'supplierNo', 'supplierName',\
            'performedDate', 'modifiedDate', 'verifiedBy', 'verifiedDate',\
            'remarks'
    # When exporting a query result in Excel file, the columns are slightly
    # different:
    #fieldNames = [TakenID,TestID,Version,Dated,
    #              Site,Try,Status,WO_ID,PO,Line,Name,
    #              Category,Technician,WorkOrder,WorkCenter,Op,Part,
    #              PartDescription,Rev,Department,QAProc,ProdLine,PLDescription,
    #              ProjectName,SerialNo,ParentSerial,SupplierNo,SupplierName,
    #              PerformedDate,
    #              PerformedTime,
    #              ModifiedDate,
    #              ModifiedTime,
    #              VerifiedBy,VerifiedDate,
    #              VerifiedTime,
    #              Remarks]
    ensureDir(filePath)
    f = open(filePath, 'wb') # 'b' is necessary for CSV format.
    f.write(u'\ufeff'.encode('utf8')) # Specify BOM-Byte Order Mark for Excel.
    if 'csvDelimiter' in g_db:
        csvDelimiter = utf8encode(g_db['csvDelimiter'])
        p_('csvDelimiter = {0}', csvDelimiter)
    else:
        csvDelimiter = ','
    c = csv.DictWriter(f, fieldnames=fieldNames, restval='', \
                       extrasaction='ignore', dialect='excel',
                       delimiter=csvDelimiter)
    if 'resultColumnHeadersConversion' in g_mats:
        c.writerow(g_mats['resultColumnHeadersConversion'])
    else:
        c.writeheader()
    for myKey, myValue in myDict.iteritems():
        # Convert all unicode characters into UTF8 for dictWriter.
        c.writerow({k:utf8encode(v) for k,v in myValue.items()})
    f.close()
    return

# Open a file, serialize the value (JSON format), writes the hash into the file
# and close the file.
def jsonWriteFile(filePath, value):
    ensureDir(filePath)
    f = open(filePath, 'w')
    t = json.dump(value, f, indent=4)
    f.close()
    return t

# Load a file, deserialize its content (JSON format), and close the file.
def jsonLoadFile(filePath):
    ensureDir(filePath)
    f = open(filePath, 'r')
    t = json.load(f)
    f.close()
    return t


###############################################################################
##  GLOBAL VARIABLES
###############################################################################

g_scriptVersion = '1.1.1'
g_scriptDate = 'February 19, 2013'

g_p = getPath()
g_configFile = g_p + '.\config.txt' # Program configuration file path.

g_config = {} # Program configuration.
g_i18n = {} # Program internationalization (language translation).
g_c = Counter('.') # Program steps counter.

# Tasks to be performed.
g_tasks = {}

g_bd = None # Browser Driver, only 1 instance is allowed
            # (Internet Explorer driver limitation)

t = None # Temporary trash variable.
f = None # Temporary trash file handler.


###############################################################################
##  MAIN SCRIPT (CONTROLLER)
###############################################################################

try:
    # Load program configuration.
    g_config = jsonLoadFile(g_configFile)
    # Global shortcuts.
    g_param = g_config['param']
    g_eq = g_config['eq']
    g_mats = g_config['eq']['mats']
    g_db = g_config['localDb']
    g_sdb = g_config['sharedDb']

    # Load language file.
    t = g_config['lang'] # Shortcut.
    g_i18n = jsonLoadFile(g_p+t['dir']+t['file'])

    # Load tasks to be performed.
    g_tasks = jsonLoadFile(g_p+g_db['dir']+g_db['tasksFile'])

    # Start message.
    p_("=== Automate eQuality start ===")
    p_("Script version {0}, {1}.", g_scriptVersion, g_scriptDate)

    # Create a new instance of the Internet Explorer driver.
    g_bd = BrowserDriver()

    parser = matsQueryResultHTMLParser()
    eqSession = EqSession()

    for taskName, taskArg in g_tasks.iteritems():
        performTask(taskName, taskArg)

    p_("=== Automate eQuality end ===")
    
except Exception, errormsg:
    p_("An error has occured. Stopped the script.")
    p_(" ")
    p_("Error message: {0}", errormsg)
    p_(" ")
    import traceback
    traceback.print_exc() # This will display the Traceback in the console.
    p_(" ")
    p_("=== Automate eQuality end ===")
    p_(" ")
    p_("If the error persists, please make screenshots or copy the ")
    p_("error message and traceback above to help troubleshooting.")
    p_(" ")
    p_("To copy the entire text: right-click, choose 'select all', "+ \
       "then press 'Enter'.")
    p_(" ")
    p_("Continue to close this console.")
    os.system("pause") # This will force the console to pause.

finally:
    # Close the browser driver and its browser instance if not already done.
    if type(g_bd) is not None:
        del g_bd


###############################################################################
##  FILE HISTORY
###############################################################################

"""
14-Feb-2013: Added support for combination of MATS Query inputs, including
 selects and selects which trigger an ajax request when clicked on (added
 waiting time and element reload). This is an adaptation for Guillem`s
 software in SRTS.
14-Feb-2013: Added support for CSV output result file.
19-Feb-2013: Added CSV column headers conversion.
19-Feb-2013: Added date manipulation for tasks input.
"""
