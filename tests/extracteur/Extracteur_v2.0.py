# Extracteur v2.0 

"""  
Some explanations of this script :

1. output the file csv with 
   cols = 'takenID','verifiedDate', 'serialNo', 'testID', 'Status', 'failLogLink'

2. use of TimeStamp

3. #Problem with format of datetime "no-break space" ,it causes another problem

"""

from collections import defaultdict
import json
import csv
from HTMLParser import HTMLParser
import datetime
from selenium import webdriver

# Controller to parse MATS test_perform query result HTML page.
class matsQueryResultHTMLParser(HTMLParser):
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

        self.listCol = [ self.takenIDCol, self.modifiedDateCol, self.serialNoCol, \
                    self.testIDCol, self.statusCol, self.failLogLinkCol]

        self.lengthResultCol = 35


    def feed(self, html):
        self.initTemporaryResultsAndCounters()
        HTMLParser.feed(self, html)
        # In order to check that a we have parsed new values (from a new page).
        return self.pageRowStart

    def initTemporaryResultsAndCounters(self):

        self.result = ['']* 6 # Temporary result.
        self.pagesNb = 0
        self.currentPageNo = 0
        self.pageRowStart = 0
        self.pageRowEnd = 0
        self.resultsNb = 0

        self.tablei = 0 # Tables counter.
        self.tdi = 0 # Cells counter.
        self.bi = 0 # Bold text counter.
        self.tri = 0 # Lines counter

    def handle_starttag(self, tag, attrs):
        # Detect tables (table).
        if tag == 'table':
            self.table = True
            self.tablei += 1 # Tables counter.
            # if self.tablei == 3:
            #     g_c.inc()
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
        # elif tag == 'a' and self.td and self.cols[self.tdi] == 'failLogLink':
        elif tag == 'a' and self.td and self.tdi == self.failLogLinkCol:
            self.result[self.listCol.index(self.failLogLinkCol)] = str(True)

    def handle_endtag(self, tag):
        # End of table line (tr).
        if tag == 'table':
            self.table = False
            self.tr = False
            self.td = False
            self.b = False

            self.tri = 0
            # if self.tablei == 3:
            #     g_c.dec()
        elif tag == 'tr':
            self.tr = False
            self.td = False
            self.b = False

            self.tri += 1

            self.endOfTr()

            # Re-initialize cells counter and temporary result.
            self.tdi = 0
            self.result = [''] * 6
        # End of cell (td)
        elif tag == 'td':
            self.td = False
            self.b = False

            # If the cell was associated with TFL link, set the temporary
            # result to False if it has not been set previously by the presence
            # of a link in the cell.
            if ( self.tdi == self.failLogLinkCol
                and self.result[self.listCol.index(self.failLogLinkCol)] != 'True'
                ):
                self.result[self.listCol.index(self.failLogLinkCol)] = str(False)


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
                # if self.currentPageNo == 1:
                #     pstepi("Found {0} page(s).", self.pagesNb)
            elif self.bi == 5:
                self.pageRowStart = int(data.lstrip('Rows '))
            elif self.bi == 6:
                self.pageRowEnd = int(data)

        # For table #2, get total number of results.
        elif self.tablei == 2 and self.b:
            self.resultsNb = int(data)
            # if self.currentPageNo == 1:
            #     pstepi("Found {0} result(s) in total.", data)
            # if self.pagesNb > 1:
            #     pstepi("Getting results #{0} to #{1}", self.pageRowStart,
            #            self.pageRowEnd)

        # Record data for table #3 (actual list of tests taken).
        elif self.tablei == 3 :
            if self.tdi < self.lengthResultCol and self.td and self.tdi in self.listCol:
                indexCol = self.listCol.index(self.tdi)
                if self.tdi != self.failLogLinkCol:   
                    if self.result[indexCol] == '':
                        self.result[indexCol] = data
                    else:
                        self.result[indexCol] += ' ' + data

                
    def endOfTr(self):
        # If we have found all cells (td), then transfer temporary result
        # into classified result.
        if self.tablei == 3 and self.tdi == self.lengthResultCol :
            r = self.result
            # transform matsTime to matsTimeStamp
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

def listToCsv ( csvFileName, listName):
    with open( csvFileName, 'wb') as f:
        writer = csv.writer(f)
        # writer.writerows(csvHead)
        writer.writerows(listName)

def matsTimeStamp (matsTime):

    # Problem with format of datetime "no-break space"
    # So add \xc2\xa0
    # But it causes another problem

    # thisMatsDateTime = datetime.datetime.strptime(matsTime, \
    #                                             '%d-%b-%Y %I:%M %p')

    thisMatsDateTime = datetime.datetime.strptime(matsTime, \
                                                '%d-%b-%Y\xc2\xa0%I:%M %p')
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = thisMatsDateTime - epoch
    thisMatsTimeStamp = int(delta.total_seconds())
    return thisMatsTimeStamp
    



########## Test with resultMats.htm #######################################

# with open ('resultMats.htm', 'r') as source:
# 	pageWebSource = source.read()

myDriver = webdriver.Firefox()
myDriver.get('file:///C:/Users/Benjamin/Documents/Etudes/Centrale/Projet_Option/Schlumberger/tests/extracteur/resultMats.htm')
pageWebSource = myDriver.page_source.encode('utf8')


parser = matsQueryResultHTMLParser()
nnn = parser.feed(pageWebSource)

listResultByTakenID = parser.getResultByTakenID()

print listResultByTakenID

# stringResultByTakenID = json.dumps(dictResultByTakenID)
# with open('resultMats_ByTakenID_v2.txt' , 'wb') as f1:
# 	f1.write(stringResultByTakenID


#writeHead doesn't work now!
# csvHead = (['takenID'] + ['verifiedDate'] + ['serialNo'] + ['testID'] + ['Status'] + ['failLogLink'])
listToCsv( 'Result_V2.csv', listResultByTakenID )


 
  



