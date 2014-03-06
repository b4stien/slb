exemple = []
exempleSendKey = []
maxIdLen = 10

''' generate exemple'''
for i in range(0,800):
	exemple.append(i)
exemple = str(exemple).replace(" ", '')[1:-1]
print exemple

''' split exemple '''
while len(exemple) > 255:
	for i in range(0 , maxIdLen):
		if exemple[254 - i] == ',':
			exempleSendKey.append(exemple[:254 - i])
			exemple = exemple[255 - i:]
			break
exempleSendKey.append(exemple)# the last seqence

'''print exempleSendKey'''
for item in exempleSendKey:
	print item



