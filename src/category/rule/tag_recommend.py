#encoding=utf-8
import sys
sys.path.append('../../common')
import json
import jieba,jieba.posseg,jieba.analyse
import itertools
import re
import text_process
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
	main_category = category_name

	#未被匹配到的app
	others_app = {}
	outfile_json = open('tag_recommend_result.json','wb')
	jieba.load_userdict('../../../data/jieba_userdict.txt')
	stopword_set = text_process.getStopword('../../../data/stopword.txt')
	node_children_dict = rule_base.createNodeChildrenDict(category_child_dict)

	candidate_tag_set,candidate_delegate_tag_set = rule_base.getCandidateTag(main_category,node_children_dict,category_synonyms_dict)
	level_category_dict = rule_base.createLevelCategoryDict(main_category,candidate_tag_set,category_parent_dict,category_child_dict,category_synonyms_dict)
	# level_category_dict[0] = set([main_category])
	for level in level_category_dict.keys():
		print level
		print ' '.join(level_category_dict[level])
	
	match_counter = 0
	all_app_counter = 0

	#遍历主类目下的app
	infile = open('../data/'+category_name+'.json','rb')
	outfile_match = open('../data/'+category_name+'_match.json','wb')
	outfile_unmatch = open('../data/'+category_name+'_unmatch.json','wb')

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

		#情感词匹配，暂时不处理情感词的同义关系
		for comment_word in [comment_word for comment_word in comment_category_set if comment_word in app_name_brief]:
			output_dict.setdefault("character",[]).append(comment_word)

		#自下而上匹配
		for depth in reversed(range(0,max(level_category_dict.keys())+1)):
			if depth not in level_category_dict.keys():
				continue
			current_level_category_set = level_category_dict[depth]
			for current_level_category in current_level_category_set:
				if current_level_category in app_name_brief and not rule_base.isAmbiguous(current_level_category,ambiguation_dict,app_name_brief):
					category_delegate = category_synonyms_dict[current_level_category][0]
					tag_recommend_set.add(category_delegate)
					#强规则
					strong_parent_set = rule_base.getNodeListOnStrongPath(category_parent_dict[category_delegate],category_parent_dict,set([]))
					tag_recommend_set = tag_recommend_set | (strong_parent_set&candidate_tag_set)

			current_level_unmatch_category_set = current_level_category_set - tag_recommend_set
			for unmatch_category in current_level_unmatch_category_set:
				if unmatch_category in indicator_set:
					continue
				unmatch_category = category_synonyms_dict[unmatch_category][0]
				unmatch_category_children = node_children_dict[unmatch_category]
				match_children = unmatch_category_children&tag_recommend_set
				if len(match_children) >= 3:
					tag_recommend_set.add(unmatch_category)
		
		#隐节点
		for tag in tag_recommend_set:
			if u'(' in tag and u')' in tag:
				hidden_node_next_level = rule_base.getNextLevelCategorySet(category_synonyms_dict,category_child_dict,tag)
				for hidden_node_next_level_item in hidden_node_next_level:
					hidden_node_next_level_item = category_synonyms_dict[hidden_node_next_level_item][0]
					if hidden_node_next_level_item in tag_recommend_set:
						output_dict.setdefault(tag,[]).append(hidden_node_next_level_item)
		#去除推导词
		tag_recommend_set = tag_recommend_set - indicator_set

		#构建输出字典
		content = outputJson(main_category,category_parent_dict,category_child_dict,category_synonyms_dict,tag_recommend_set)
		output_dict['content'] = content

		if len(content.keys()) != 0:
			outfile_match.write(row)
			match_counter += 1
			if app_download >= 10000000:
				continue
			outfile_json.write(json.dumps(output_dict,ensure_ascii=False)+'\r\n')
		else:
			outfile_unmatch.write(row)
			if app_download <= 500:
				continue
			others_app.setdefault(app_name,[app_download,' '.join(app_brief_seg)])
	print "覆盖率: "+str(1.0*match_counter/all_app_counter)
	
	#剩下没有匹配到的按下载量排序，输出
	other_title_fre = {}
	sorted_list = sorted(others_app.items(),key=lambda p:p[1][0],reverse=True)
	outfile_others = open('others.txt','wb')
	for val in sorted_list:
		title_seg = jieba.cut(val[0])
		for title in title_seg:
			if text_process.isChinese(title) and title not in stopword_set:
				other_title_fre.setdefault(title,0)
				other_title_fre[title] += 1
		outfile_others.write(val[0]+'<@>'+val[1][1]+'\r\n')

	sorted_list = sorted(other_title_fre.items(),key=lambda p:p[1],reverse=True)
	outfile_others_title = open('others_title.txt','wb')
	for val in sorted_list:
		outfile_others_title.write(val[0]+'<@>'+str(val[1])+'\r\n')

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
 	# category_name = u"便捷生活"
	# category_name = u"金融理财"
	category_name = u"实用工具"
	main(category_name)