#encoding=utf-8
import sys
sys.path.append('../common')
import text_process
import jft
import itertools

#获取语料中的候选词
def getWords():
	word_set = set([])
	infile = open('../../data/all_word.txt','rb')
	for row in infile:
		row = row.strip().decode('utf-8')
		word = row.split(',')[0]
		word_set.add(word)
	infile.close()
	return word_set

def createJftSynonyms(word_set):
	outfile = open('jft_synonyms.txt','wb')
	for word in word_set:
		syn_set = set([word])
		word_f = jft.j2f('gbk','utf-8',word.encode('gbk')).decode('utf-8')
		syn_set.add(word_f)
		outfile.write(word+"@"+",".join(syn_set)+"\r\n")


def main():
	reload(sys)
	sys.setdefaultencoding('utf-8')

	word_set = getWords()
	createJftSynonyms(word_set)


if __name__ == '__main__':
	main()

