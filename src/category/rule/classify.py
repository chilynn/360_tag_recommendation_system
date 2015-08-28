#encoding=utf-8
import sys
sys.path.append('../../common')
import text_process
import json
import jieba,jieba.posseg,jieba.analyse
import itertools
import re
import rule_base


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

	#标签推荐
	recommendTag(category_name,category_parent_dict,category_child_dict,category_synonyms_dict,indicator_set,comment_category_set,ambiguation_dict)


#标签推荐
def recommendTag(category_name,category_parent_dict,category_child_dict,category_synonyms_dict,indicator_set,comment_category_set,ambiguation_dict):
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
	
	match_counter = 0
	all_app_counter = 0

	#遍历主类目下的app
	infile = open('../data/'+category_name+'.json','rb')
	outfile_classification = open('../data/'+ category_name+'_classification.json','wb')

	for row in infile:
		all_app_counter += 1
		
		json_obj = json.loads(row.strip())
		app_id = int(json_obj["id"])
		app_name = json_obj["title"]
		app_brief = json_obj["brief"]
		app_download = int(json_obj["download_times"])
		app_brief_seg = [word for word in jieba.cut(app_brief) if word not in stopword_set and text_process.isChinese(word)]
		app_name_brief = app_name+" "+app_brief
		app_name_brief += " "+rule_base.grabEnglish(app_name_brief)

		output_dict = {}
		output_dict["id"] = app_id
		output_dict["content"] = {}
		tag_recommend_set = set([])

		for tag in candidate_tag_set:
			if tag in app_name_brief:
				tag_recommend_set.add(category_synonyms_dict[tag][0])

		# #去除推导词
		# tag_recommend_set = tag_recommend_set - indicator_set
	
		#构建输出字典
		content = outputJson(main_category,category_parent_dict,category_child_dict,category_synonyms_dict,tag_recommend_set)
		output_dict['content'] = content

		if len(content.keys()) != 0:
			candidate_main_level_set = set(content.keys())
			candidate_main_level_score_dict = {}
			for candidate_main_level in candidate_main_level_set:
				score = len(node_children_dict[candidate_main_level] & tag_recommend_set)
				candidate_main_level_score_dict.setdefault(score,set([])).add(candidate_main_level)
			max_score = max(candidate_main_level_score_dict.keys())
			if max_score >= 3:
				final_category_list = list(candidate_main_level_score_dict[max_score])
				if final_category_list[0] != category_name:
					outfile_classification.write(str(app_id)+"->"+final_category_list[0]+"->"+app_name+"<@>"+" ".join(app_brief_seg)+'\r\n')

def outputJson(main_category,category_parent_dict,category_child_dict,category_synonyms_dict,tag_recommend_set):
	top_level_list = rule_base.getNextLevelCategorySet(category_synonyms_dict,category_child_dict,main_category)
	content = {}
	for tag in tag_recommend_set:
		content[tag] = {}
	for node in tag_recommend_set:
		for partial_tuple in category_parent_dict[node]:
			parent_name = partial_tuple[0]
			if parent_name == main_category:
				continue
			if parent_name in content.keys():
				content[parent_name][node] = content[node]
	
	for top_level in content.keys():
		if top_level not in top_level_list:
			del content[top_level]
	return content


if __name__ == '__main__':
	category_name = u"影音视听"
	# category_name = u"购物优惠_unmatch"
	main(category_name)
