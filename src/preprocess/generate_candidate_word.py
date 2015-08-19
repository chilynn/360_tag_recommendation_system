#encoding=utf-8
import sys
sys.path.append('../common')
import text_process
import json
import pickle
import jieba,jieba.posseg,jieba.analyse

def readSegFile():
	jieba.load_userdict("../../data/jieba_userdict.txt")
	infile = open('../../data/all_cn_seg_nwi_clean.txt','rb')
	outfile = open('../../data/all_word.txt','wb')
	stopword_set = text_process.getStopword('../../data/stopword.txt')
	word_set = set([])
	word_fre_dict = {}
	row_counter = 0
	for row in infile:
		row_counter += 1
		print row_counter
		row = row.strip().decode('utf-8')
		items = row.split('<@>')
		app_name = items[1]
		brief_seg = items[2].split()
		title_seg = jieba.cut(app_name)
		for title in title_seg:
			if text_process.isChinese(title) and title not in stopword_set:
				word_set.add(title)
				word_fre_dict.setdefault(title,0)
				word_fre_dict[title] += 1
		for brief in brief_seg:
			if text_process.isChinese(brief) and brief not in stopword_set:
				word_set.add(brief)
				word_fre_dict.setdefault(brief,0)
				word_fre_dict[brief] += 1

	sorted_list = sorted(word_fre_dict.items(),key=lambda p:p[1],reverse=True)
	for val in sorted_list:
		if val[1] >= 10:
			outfile.write(val[0]+','+str(val[1])+'\r\n')
	# for word in word_set:
	# 	outfile.write(word+'\r\n')


def main():
	reload(sys)
	sys.setdefaultencoding('utf-8')

	readSegFile()

if __name__ == '__main__':
	main()











