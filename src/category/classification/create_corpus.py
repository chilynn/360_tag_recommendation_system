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


query = u"微博"

def createCorpus(category_name,query_set):
	match_counter = 0
	outfile = open('corpus/'+query+".json",'wb')
	infile = open('../data/'+category_name+'.json','rb')
	for row in infile:
		json_obj = json.loads(row.strip())
		app_id = int(json_obj["id"])
		app_name = json_obj["title"]
		app_brief = json_obj["brief"]
		app_download = int(json_obj["download_times"])
		app_name_brief = app_name+" "+app_brief

		for q in query_set:
			if q in app_name_brief:
				match_counter += 1
				outfile.write(row)

	print "match counter: "+str(match_counter)

def main(category_name):
	reload(sys)
	sys.setdefaultencoding('utf-8')

	#获取规则模版(同义词，偏序关系，推导词，组合关系，情感词，歧义词)
	category_synonyms_dict = rule_base.getSynonym('../rule/rule_template/synonym.rule')
	partial_dict,indicator_set = rule_base.getPartial('../rule/rule_template/partial.rule')
	combine_dict = rule_base.getCombine('../rule/rule_template/combine.rule')
	comment_category_set = rule_base.getCommenCategorySet('../rule/rule_template/comment.rule')
	ambiguation_dict = rule_base.getDisambiguation('../rule/rule_template/disambiguation.rule')

	query_set = category_synonyms_dict[query][1]
	createCorpus(category_name,query_set)

if __name__ == '__main__':
	category_name = u"通讯社交"
	main(category_name)
