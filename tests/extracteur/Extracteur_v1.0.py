# Extracteur v1.0 

"""  
Some explanations of this script :

1. This script will record dota( type of string )into two .txt files 
2. resultMats_ByTakenID.txt :
    {   takenID1 : {r} , 
        takenID2 : {r} ,
        ...
    }
3. resultMats_ByWorkID.txt :
    {   woID1 : {   serialNo1 : {   takenIDxxx : {r} ,    takenIDxxx : {r}, ...}
                    serialNo2 : {   takenIDxxx : {r} ,    takenIDxxx : {r}, ...}} ,

        woID2 : {   serialNo1 : {   takenIDxxx : {r} ,    takenIDxxx : {r}, ...}
                    serialNo2 : {   takenIDxxx : {r} ,    takenIDxxx : {r}, ...}} ,
        ....
    }

4.  r = { 'woID': data , 'serialNo' : data , ....} , 
    r is the dict that records the info of one line.


"""



from collections import defaultdict
import json
from HTMLParser import HTMLParser

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
        elif tag == 'a' and self.td and self.cols[self.tdi] == 'failLogLink':
            self.result[self.cols[self.tdi]] = True

    def handle_endtag(self, tag):
        # End of table line (tr).
        if tag == 'table':
            self.table = False
            self.tr = False
            self.td = False
            self.b = False
            # if self.tablei == 3:
            #     g_c.dec()
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
        elif self.tablei == 3:
            # add one condition comparedt to original code
            if self.tdi < len(self.cols):
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
            # pstepi("Recording test taken {0}, for S/N {1}, in WO {2}.", \
            #       takenID, serialNo, woID)

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

# Get the value of the dict[key]. If the key is not defined yet, initialize
# it with the given default value.
def getDictKey(myDict, key, initValue=None):
    if key not in myDict:
        myDict[key] = initValue
    return myDict[key]

# Initialize a key as dict within a parent dict.
def initDict(parentDict, newKeyDict):
    if newKeyDict not in parentDict:
        parentDict[newKeyDict] = {}


########## Test with resultMats.htm #######################################

with open ('resultMats.htm', 'r') as source:
	pageWebSource = source.read()


parser = matsQueryResultHTMLParser()
nnn = parser.feed(pageWebSource)

dictResultByTakenID = parser.getResultByTakenID()
dictResultsByWoIDSerialNoTakenID = parser.getResultByWoIDSerialNoTakenID()

print dictResultByTakenID
print dictResultsByWoIDSerialNoTakenID

stringResultByTakenID = json.dumps(dictResultByTakenID)
stringResultByWoIDSerialNoTakenID = json.dumps(dictResultsByWoIDSerialNoTakenID)



with open('resultMats_ByTakenID.txt' , 'wb') as f1:
	f1.write(stringResultByTakenID)

with open('resultMats_ByWorkID.txt' , 'wb') as f2:
    f2.write(stringResultByWoIDSerialNoTakenID)
 
  



