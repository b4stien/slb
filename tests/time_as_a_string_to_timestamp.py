import datetime

thisMatsTime = "02-Dec-2013 5:45 AM"  
thisMatsDatetime = datetime.datetime.strptime(thisMatsTime, '%d-%b-%Y %I:%M %p')

epoch = datetime.datetime.utcfromtimestamp(0)
delta = thisMatsDatetime - epoch
thisMatsTimestamp = int(delta.total_seconds())

return thisMatsTimestamp

