#encoding=utf-8
import sys
sys.path.append('../../common')
import text_process
import json
import jieba,jieba.posseg,jieba.analyse
import itertools
import re
import rule_base
from gensim import corpora, models, similarities
from sklearn import svm
import numpy as np


def main(category_name):
	reload(sys)
	sys.setdefaultencoding('utf-8')

	#获取规则模版(同义词，偏序关系，推导词，组合关系，情感词，歧义词)
	category_synonyms_dict = rule_base.getSynonym('rule_template/synonym.rule')
	partial_dict,indicator_set = rule_base.getPartial('rule_template/partial.rule')
	combine_dict = rule_base.getCombine('rule_template/combine.rule')
	comment_category_set = rule_base.getCommenCategorySet('rule_template/comment.rule')
	ambiguation_dict = rule_base.getDisambiguation('rule_template/disambiguation.rule')

	#从规则库中构建类目关系树
	category_parent_dict,category_child_dict,category_synonyms_dict = rule_base.createCategoryTree(partial_dict,combine_dict,category_synonyms_dict)


	classify(category_name,category_parent_dict,category_child_dict,category_synonyms_dict,indicator_set,comment_category_set,ambiguation_dict)


def ocsvm():

	outfile_classification = open('../data/'+ category_name+'_classification.json','wb')

	X_train,X_test,X_test_info = getTrainTest(category_name,category_parent_dict,category_child_dict,category_synonyms_dict,indicator_set,comment_category_set,ambiguation_dict)

	clf = svm.OneClassSVM(nu=0.1, kernel="rbf", gamma=0.1)
	clf.fit(X_train)
	y_pred_test = clf.predict(X_test)
	for i in range(len(y_pred_test)):
		if y_pred_test[i] == 1:
			print X_test_info[i][0]
			print X_test_info[i][1]
			outfile_classification.write(X_test_info[i][0]+"<@>"+X_test_info[i][1]+"\r\n")

def getTrainTest(category_name,category_parent_dict,category_child_dict,category_synonyms_dict,indicator_set,comment_category_set,ambiguation_dict):
	#主类目名称
	main_category = u"软件"

	jieba.load_userdict('../../../data/jieba_userdict.txt')
	stopword_set = text_process.getStopword('../../../data/stopword.txt')

	node_children_dict = rule_base.createNodeChildrenDict(category_child_dict)
	candidate_tag_set,candidate_delegate_tag_set = rule_base.getCandidateTag(main_category,node_children_dict,category_synonyms_dict)
	level_category_dict = rule_base.createLevelCategoryDict(main_category,candidate_tag_set,category_parent_dict,category_child_dict,category_synonyms_dict)
	# for level in level_category_dict.keys():
	# 	print level
	# 	print ' '.join(level_category_dict[level])

	dictionary = corpora.Dictionary([list(candidate_delegate_tag_set)])
	valcabulary_size = len(dictionary)

	#遍历主类目下的app
	infile = open('../data/'+category_name+'.json','rb')
	X_train = []
	X_test = []
	X_test_info = []
	all_counter = 0
	train_counter = 0
	for row in infile:
		if all_counter >= 5000:
			break
		all_counter += 1
		json_obj = json.loads(row.strip())
		app_id = int(json_obj["id"])
		app_name = json_obj["title"]
		app_brief = json_obj["brief"]
		app_tag = json_obj["tags"]
		app_download = int(json_obj["download_times"])
		app_brief_seg = [word for word in jieba.cut(app_brief) if word not in stopword_set and text_process.isChinese(word)]
		app_name_brief = app_name+" "+app_brief
		app_name_brief += " "+rule_base.grabEnglish(app_name_brief)

		tag_recommend_set = set([])

		for tag in candidate_tag_set:
			if tag in app_name_brief:
				tag_recommend_set.add(category_synonyms_dict[tag][0])

		doc = dictionary.doc2bow(list(tag_recommend_set))
		x = [0 for i in range(valcabulary_size)]
		for val in doc:
			index = val[0]
			x[index] = val[1]
		if u"视频" in app_tag or u"音乐" in app_tag and app_download >= 1000:
			train_counter += 1
			X_train.append(x)
		else:
			X_test.append(x)
			X_test_info.append([app_name,' '.join(app_brief_seg)])

	print 1.0*train_counter/all_counter
	return X_train,X_test,X_test_info

def classify(category_name,category_parent_dict,category_child_dict,category_synonyms_dict,indicator_set,comment_category_set,ambiguation_dict):
	#主类目名称
	main_category = u"软件"

	jieba.load_userdict('../../../data/jieba_userdict.txt')
	stopword_set = text_process.getStopword('../../../data/stopword.txt')

	node_children_dict = rule_base.createNodeChildrenDict(category_child_dict)
	candidate_tag_set,candidate_delegate_tag_set = rule_base.getCandidateTag(main_category,node_children_dict,category_synonyms_dict)
	level_category_dict = rule_base.createLevelCategoryDict(main_category,candidate_tag_set,category_parent_dict,category_child_dict,category_synonyms_dict)
	for level in level_category_dict.keys():
		print level
		print ' '.join(level_category_dict[level])

	#遍历主类目下的app
	infile = open('../data/'+category_name+'.json','rb')
	outfile_classification = open('../data/'+ category_name+'_classification.json','wb')

	for row in infile:
		
		json_obj = json.loads(row.strip())
		app_id = int(json_obj["id"])
		app_name = json_obj["title"]
		app_brief = json_obj["brief"]
		app_download = int(json_obj["download_times"])
		app_brief_seg = [word for word in jieba.cut(app_brief) if word not in stopword_set and text_process.isChinese(word)]
		app_name_brief = app_name+" "+app_brief
		app_name_brief += " "+rule_base.grabEnglish(app_name_brief)

		tag_recommend_set = set([])

		for tag in candidate_tag_set:
			if tag in app_name_brief:
				tag_recommend_set.add(category_synonyms_dict[tag][0])
	
		if len(level_category_dict[1] & tag_recommend_set) != 0:
			candidate_main_level_set = level_category_dict[1] & tag_recommend_set
			candidate_main_level_score_dict = {}
			for candidate_main_level in candidate_main_level_set:
				score = len(node_children_dict[candidate_main_level] & tag_recommend_set)
				candidate_main_level_score_dict.setdefault(score,set([])).add(candidate_main_level)
			max_score = max(candidate_main_level_score_dict.keys())
			if max_score >= 3:
				final_category_list = list(candidate_main_level_score_dict[max_score])
				if final_category_list[0] != category_name:
					outfile_classification.write(str(app_id)+"->"+final_category_list[0]+"->"+app_name+"<@>"+" ".join(app_brief_seg)+'\r\n')


if __name__ == '__main__':
	category_name = u"摄影摄像_unmatch"
	main(category_name)
