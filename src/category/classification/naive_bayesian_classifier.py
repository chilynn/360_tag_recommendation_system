#encoding=utf-8
import sys
sys.path.append('../../common')
sys.path.append('../rule')
import rule_base
import text_process
import json
import jieba,jieba.posseg,jieba.analyse
from gensim import corpora, models, similarities
from sklearn import svm
import numpy as np
from sklearn.naive_bayes import BernoulliNB, MultinomialNB

def getCorpus(category_name):

	app_lable_dict = {10743:1,1002128:1,47:1,498:1,550:-1,48:-1,490:-1,761:-1,101108:-1,101916:-1}

	x_train = []
	y_train = []
	x_test = []

	jieba.load_userdict('../../../data/jieba_userdict.txt')
	stopword_set = text_process.getStopword('../../../data/stopword.txt')

	doc_app_id = []
	docs = []
	id_name_dict = {}
	infile = open('corpus/'+category_name+'.json','rb')
	for row in infile:
		json_obj = json.loads(row.strip())
		app_id = int(json_obj["id"])
		app_name = json_obj["title"]
		app_brief = json_obj["brief"]
		app_download = int(json_obj["download_times"])
		app_brief_seg = [word for word in jieba.cut(app_name+" "+app_brief) if word not in stopword_set and text_process.isChinese(word)]

		if len(app_brief_seg) <= 10 and app_download <= 100:
			continue

		doc_app_id.append(app_id)
		id_name_dict[app_id] = app_name
		docs.append(app_brief_seg)

	dictionary = corpora.Dictionary(docs)
	corpus = [dictionary.doc2bow(text) for text in docs]

	for i in range(len(corpus)):
		doc = corpus[i]
		x = [0 for n in range(len(dictionary))]
		for val in doc:
			x[val[0]] = val[1]

		app_id = doc_app_id[i]
		if app_id in app_lable_dict.keys():
			x_train.append(x)
			if app_lable_dict[app_id] == 1:
				y_train.append(1)
			else:
				y_train.append(-1)
		else:
			x_test.append(x)

	return x_train,x_test,y_train,doc_app_id,id_name_dict

def nb(x_train,x_test,y_train,doc_app_id,id_name_dict):
	clf = MultinomialNB(alpha=0.01)
	clf.fit(x_train,y_train)
	pred = clf.predict(x_test)
	for i in range(len(pred)):
		app_id = doc_app_id[i]
		print id_name_dict[app_id]+" "+str(pred[i])
	
def main(category_name):
	reload(sys)
	sys.setdefaultencoding('utf-8')

	x_train,x_test,y_train,doc_app_id,id_name_dict = getCorpus(category_name)

	nb(x_train,x_test,y_train,doc_app_id,id_name_dict)


if __name__ == '__main__':
	category_name = u"微博"
	main(category_name)
