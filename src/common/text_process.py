#encoding=utf-8
import sys

def isChinese(word):
	for w in word:
		if not(0x4e00<=ord(w)<0x9fa6):
			return False
	return True

def getStopword(file_path):
	stopword_set = set()
	infile = open(file_path, 'rb')
	for row in infile:
		stopword_set.add(row.strip().decode('utf-8'))
	infile.close()
	return stopword_set

#判断shorter_text是否被longer_text包含
def isSubset(shorter_text,longer_text):
	is_subset = False
	for i in range(len(longer_text)):	
		if shorter_text == ''.join(longer_text[i:i+len(shorter_text)]):
			is_subset = True
		if i+len(shorter_text) == len(longer_text):
			break
	return is_subset

#判断两个字符串是否有包含关系
def isSubsetGeneral(text1,text2):
	is_cover = False
	if len(text1) >= len(text2):
		if isSubset(text2,text1):
			is_cover = True
	else:
		if isSubset(text1,text2):
			is_cover = True
	return is_cover