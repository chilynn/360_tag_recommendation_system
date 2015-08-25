#encoding=utf-8
import sys
sys.path.append('../common')
import text_process
import json
import jft
import itertools

#获取语料中的候选词
def getWords():
	word_set = set([])
	word_list = []
	infile = open('../../data/all_word.txt','rb')
	for row in infile:
		row = row.strip().decode('utf-8')
		word = row.split(',')[0]
		fre = int(row.split(',')[1])
		word_set.add(word)
		word_list.append(word)
	infile.close()
	return word_set,word_list

#按照固定格式读取同义词文件
def readSynonymsFile(word_synonyms_dict,file_path):
	infile = open(file_path,'rb')
	for row in infile:
		row = row.strip().decode('utf-8')
		word = row.split('@')[0]
		for synonyms_word in row.split('@')[1].split(','):
			word_synonyms_dict.setdefault(word,set([word])).add(synonyms_word)
	infile.close()
	return word_synonyms_dict

#获取同义词关系
def getSynonyms():
	word_synonyms_dict = {}
	# word_synonyms_dict = readSynonymsFile(word_synonyms_dict,'jft_synonyms.txt')
	# word_synonyms_dict = readSynonymsFile(word_synonyms_dict,'baidu_wenku_format.txt')
	word_synonyms_dict = readSynonymsFile(word_synonyms_dict,'baidu_baike_definition.txt')
	word_synonyms_dict = readSynonymsFile(word_synonyms_dict,'abbreviation.txt')
	return word_synonyms_dict

#合并
def finalCombine(word_synonyms_dict,word_list):
	handle_word_set = set([])
	outfile = open('final_combine.txt','wb')
	word_parent_dict = {}
	for word in word_synonyms_dict.keys():
		if word not in word_parent_dict.keys():
			word_parent_dict[word] = word
		synonyms_set = word_synonyms_dict[word]
		for synonyms_word in synonyms_set:
			if synonyms_word not in word_parent_dict.keys():
				word_parent_dict[synonyms_word] = word
			synonyms_word_root = getRoot(word_parent_dict,synonyms_word)
			if getRoot(word_parent_dict,word) == synonyms_word_root:
				continue
			word_parent_dict[synonyms_word_root] = word
			word_parent_dict[synonyms_word] = word

	delegate_syn_dict = {}
	for word in word_parent_dict.keys():
		root = getRoot(word_parent_dict,word)
		delegate_syn_dict.setdefault(root,set([])).add(word)
		handle_word_set.add(word)


	for word in delegate_syn_dict.keys():
		outfile.write(word+'@'+','.join(delegate_syn_dict[word])+'\r\n')

	# for word in word_list:
	# 	if word in delegate_syn_dict.keys():
	# 		outfile.write(word+'@'+','.join(delegate_syn_dict[word])+'\r\n')

	print len(handle_word_set)	

#获取query节点的root节点
def getRoot(word_parent_dict,query):
	if word_parent_dict[query] != query:
		return getRoot(word_parent_dict,word_parent_dict[query])
	else:
		return query

def main():
	reload(sys)
	sys.setdefaultencoding('utf-8')

	word_set,word_list = getWords()
	word_synonyms_dict = getSynonyms()
	finalCombine(word_synonyms_dict,word_list)

if __name__ == '__main__':
	main()

