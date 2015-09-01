#encoding=utf-8
import sys
sys.path.append('../../common')
import text_process
import json
import jieba
import gensim
from gensim.models import Word2Vec

#获取语料中的候选词
def getWords():
	word_set = set([])
	infile = open('../../../data/all_word.txt','rb')
	row_index = 0
	for row in infile:
		row = row.strip().decode('utf-8')
		word = row.split(',')[0]
		word_set.add(word)
	infile.close()
	return word_set

#缩写挖掘
def mineAbbreviation():
	print 'mining abbreviation'
	jieba.load_userdict("../../../data/jieba_userdict.txt")
	stopword_set = text_process.getStopword('../../../data/stopword.txt')
	word2vec_model = Word2Vec.load('../../../data/word2vec.model')
	word_set = getWords()
	word_syn_dict = {}
	for word in word_set:
		word_syn_dict.setdefault(word,set([word]))
		if len(word) != 2:
			continue
		try:
			for simi_word_tuple in word2vec_model.most_similar(positive=[word],topn=20):
				simi_word = simi_word_tuple[0]
				simi_value = simi_word_tuple[1]
				reverse_word = word[1]+word[0]
				if reverse_word == simi_word:
					pass
				else:	
					if len(set(word)&set(simi_word)) != len(word) or simi_value < 0.5 or word in simi_word or reverse_word in simi_word:
						continue
				word_syn_dict[word].add(simi_word)
		except:
			pass
			# print word

	outfile = open('abbreviation.txt','wb')
	for word in word_syn_dict.keys():
		if len(word_syn_dict[word])>=2:
			outfile.write(word+'@'+','.join(word_syn_dict[word])+'\r\n')	

def main():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	mineAbbreviation()

if __name__ == '__main__':
	main()

