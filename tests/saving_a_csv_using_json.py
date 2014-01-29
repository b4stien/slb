import os
import csv
import json

msg1 = {}
msg1['type'] = 'mats'
msg1['status'] = 'fail'

msg2 = {}
msg2['type'] = 'tfl'
msg2['redo'] = ['12','13','14']

with open('dumptest.csv', 'wb') as csvfile:
    myWriter = csv.writer(csvfile, delimiter=',',
                            quotechar="'", quoting=csv.QUOTE_MINIMAL)
    myWriter.writerow(['130128482'] + ['TCQR-BA.921'] + ['29140'] + [json.dumps(msg1)])
    myWriter.writerow(['130128643'] + ['TCQR-BA.925'] + ['29140'] + [json.dumps(msg2)])

