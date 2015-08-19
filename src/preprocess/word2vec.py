#encoding=utf-8
import sys
import gensim
from gensim.models import Word2Vec
from gensim.models.word2vec import LineSentence

def createCorpus():
	print 'creating corpus'
	infile = open('../../data/all_cn_seg_nwi_clean.txt','rb')
	outfile = open('../../data/corpus.txt','wb')
	row_index = 0
	for row in infile:
		row = row.strip().decode('utf-8')
		# if u'英语四级' in row.split('<@>')[-1]:
		# 	print row.split('<@>')[-1]
		outfile.write(row.split('<@>')[-1]+'\r\n')

def getCorpus():
	print 'getting corpus'
	sentences = LineSentence('../../data/corpus.txt')
	return sentences

def word2vec(sentences):
	print 'training'
	model = Word2Vec(sentences, size=100, window=5, min_count=5, workers=4)
	model.save('../../data/word2vec.model')

def main():
	reload(sys)
	sys.setdefaultencoding('utf-8')

	createCorpus()
	sentences = getCorpus()
	word2vec(sentences)
	
if __name__ == '__main__':
	main()