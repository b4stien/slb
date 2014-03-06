
exemple = []

i = 1
while i < 1000 :
    exemple.append(i)
    i += 1

exemple = str(exemple)
print exemple

remainingLen = len(exemple)
maxIDLen = 10
TFLSendKey = []


i = 0
lettre = ""
while remainingLen > 30 :
    while lettre != ',' :
        lettre = exemple[255 - i]
        i += 1

    TFLSendKey.append(exemple[:254 - i])
    exemple = exemple[255 - i:]
    remainingLen = len(exemple)
           

for element in TFLSendKey :
    print element + '\n'
    
