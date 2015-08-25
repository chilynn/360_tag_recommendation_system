#encoding=utf-8
import sys
sys.path.append('../common')
import text_process
import json
import jft
import itertools


#获取偏序关系
def getPartial():
	partial_word_set = set([])
	infile = open('../category/rule/rule_template/partial.rule','rb')
	for row in infile:
		row = row.strip().decode('utf-8')
		if row == "":
			continue
		#微弱偏序关系0，作推导词，不作tag
		if "~" in row:
			master = row.split("~")[0]
			slaver = row.split("~")[1]
		#强偏序关系2
		elif '>>' in row:
			master = row.split('>>')[0]
			slaver = row.split('>>')[1]
		#弱偏序关系1
		else:
			master = row.split('>')[0]
			slaver = row.split('>')[1]
		partial_word_set.add(master)
		partial_word_set.add(slaver)
	return partial_word_set

def filterImportantSynonyms(partial_word_set):
	outfile = open('important_synonyms.txt','wb')
	infile = open('final_combine.txt','rb')
	for row in infile:
		row = row.strip().decode('utf-8')
		delegate = row.split('@')[0]
		synonyms = set(row.split('@')[1].split(','))
		if len(synonyms & partial_word_set) >= 1:
			outfile.write(row+'\r\n')


def main():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	partial_word_set = getPartial()
	filterImportantSynonyms(partial_word_set)



if __name__ == '__main__':
	main()

