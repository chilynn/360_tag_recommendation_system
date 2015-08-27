#encoding=utf-8
import sys
sys.path.append('../../common')
import text_process
import json
import jieba,jieba.posseg,jieba.analyse
import itertools
import re

#类目id与类目名称映射
def idToName(category_id):
	category_name = ""
	if "_" in category_id:
		category_name = u"实用工具"
	else:	
		id_category_dict = {11:u"系统安全",12:u"通讯社交",14:u"影视视听",16:u"便捷生活",17:u"办公商务",18:u"主题壁纸",\
							998:u"实用工具",102139:u"金融理财",102230:u"购物优惠",102233:u"运动健康"}
		category_name = id_category_dict[int(category_id)]
	return category_name

#用正则表达式匹配连续英文和数字
def grabEnglish(text):
	english_list = []
	expression = ur"[a-zA-Z0-9-]+"
	pattern = re.compile(expression)
	english_list = [val.lower() for val in pattern.findall(text)] 
	return " ".join(english_list)


#获取主类目下的候选标签集合
def getCandidateTag(main_category,node_children_dict,category_synonyms_dict):
	#所有候选标签集合（代表词＋同义词）
	candidate_tag_set = set([])
	#候选标签代表词的集合
	candidate_delegate_tag_set = node_children_dict[main_category]
	candidate_tag_set |= candidate_delegate_tag_set
	for category in candidate_delegate_tag_set:
		if category in category_synonyms_dict.keys():
			candidate_tag_set |= category_synonyms_dict[category][1]
	return candidate_tag_set,candidate_delegate_tag_set

#标签推荐
def recommendTag(category_name,category_parent_dict,category_child_dict,category_synonyms_dict,indicator_set,comment_category_set,ambiguation_dict):
	#主类目名称
	main_category = u"实用工具"

	jieba.load_userdict('../../../data/jieba_userdict.txt')
	stopword_set = text_process.getStopword('../../../data/stopword.txt')
	node_children_dict = createNodeChildrenDict(category_child_dict)

	candidate_tag_set,candidate_delegate_tag_set = getCandidateTag(main_category,node_children_dict,category_synonyms_dict)
	level_category_dict = createLevelCategoryDict(main_category,candidate_tag_set,category_parent_dict,category_child_dict,category_synonyms_dict)
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
		app_name_brief += " "+grabEnglish(app_name_brief)

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
				if current_level_category in app_name_brief and not isAmbiguous(current_level_category,ambiguation_dict,app_name_brief):
					category_delegate = category_synonyms_dict[current_level_category][0]
					tag_recommend_set.add(category_delegate)
					#强规则
					strong_parent_set = getNodeListOnStrongPath(category_parent_dict[category_delegate],category_parent_dict,set([]))
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
				hidden_node_next_level = getNextLevelCategorySet(category_synonyms_dict,category_child_dict,tag)
				for hidden_node_next_level_item in hidden_node_next_level:
					hidden_node_next_level_item = category_synonyms_dict[hidden_node_next_level_item][0]
					if hidden_node_next_level_item in tag_recommend_set:
						output_dict.setdefault(tag,[]).append(hidden_node_next_level_item)
		#去除推导词
		tag_recommend_set = tag_recommend_set - indicator_set

		#构建输出字典
		content = outputJson(main_category,category_parent_dict,category_child_dict,category_synonyms_dict,tag_recommend_set)
		output_dict['content'] = content

		if len(content.keys()) != 0 and len(tag_recommend_set) >= 3:
			outfile_classification.write(app_name+"<@>"+" ".join(app_brief_seg)+'\r\n')

			# outfile_classification.write(" ".join(content.keys())+" -> "+app_name+"<@>"+" ".join(app_brief_seg)+'\r\n')

def outputJson(main_category,category_parent_dict,category_child_dict,category_synonyms_dict,tag_recommend_set):
	top_level_list = getNextLevelCategorySet(category_synonyms_dict,category_child_dict,main_category)
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

#歧义消除
def isAmbiguous(category,ambiguation_dict,document):
	is_ambiguous = False
	if category in ambiguation_dict.keys():
		for ambiguous_situation in ambiguation_dict[category]:
			if ambiguous_situation in document:
				is_ambiguous = True
	return is_ambiguous

#创建level与类目词之间映射字典
def createLevelCategoryDict(main_category,candidate_tag_set,category_parent_dict,category_child_dict,category_synonyms_dict):
	level_category_dict = {}
	for node in candidate_tag_set:
		node_delegate = category_synonyms_dict[node][0]
		node_parent_set = set([partial_tuple[0] for partial_tuple in category_parent_dict[node_delegate]])
		node_show_place_num = len(node_parent_set&(candidate_tag_set|set([main_category])))
		depth_set = getNodeDepthGivenRoot(set([main_category]),node_delegate,category_child_dict,1,0,node_show_place_num,set([]))
		for depth in depth_set:
			level_category_dict.setdefault(depth,set()).add(node)
	return level_category_dict

#获取query节点在root节点下出现的所有深度可能
def getNodeDepthGivenRoot(root_set,query,category_child_dict,depth,match_counter,need_match_num,depth_set):
	if query not in category_child_dict.keys():
		return -1
	if query in root_set:
		return set([0])
	next_root_set = set([])
	for root in root_set:
		for child_tuple in category_child_dict[root]:
			child = child_tuple[0]
			if child == query:
				match_counter += 1
				depth_set.add(depth)
			else:	
				next_root_set.add(child)
	if match_counter == need_match_num:
		return depth_set
	depth += 1
	return getNodeDepthGivenRoot(next_root_set,query,category_child_dict,depth,match_counter,need_match_num,depth_set)

#给定query，获取其下一级的类目词，包括同义词
def getNextLevelCategorySet(category_synonyms_dict,category_child_dict,query):
	next_level_category_set = set([])
	query_delegate = category_synonyms_dict[query][0]
	for partial_tuple in category_child_dict[query_delegate]:
		child_name = partial_tuple[0]
		next_level_category_set |= category_synonyms_dict[child_name][1]
	return next_level_category_set

#向上获取其强联通路径的所有节点，放到strong_parent_set中
def getNodeListOnStrongPath(to_handle_set,category_parent_dict,strong_parent_set):
	if len(to_handle_set) == 0:
		return strong_parent_set
	for parent_tuple in to_handle_set:
		parent_name = parent_tuple[0]
		relation = parent_tuple[1]
		if relation == 2:
			strong_parent_set.add(parent_name)
			to_handle_set = to_handle_set | category_parent_dict[parent_name]
		to_handle_set = to_handle_set - set([parent_tuple])
	return getNodeListOnStrongPath(to_handle_set,category_parent_dict,strong_parent_set)

#向上遍历直到根节点
def getNodeListToRoot(to_handle_set,category_parent_dict,parent_set):
	if len(to_handle_set) == 0:
		return parent_set
	for parent_tuple in to_handle_set:
		parent_name = parent_tuple[0]
		parent_set.add(parent_name)
		to_handle_set = to_handle_set | category_parent_dict[parent_name]
		to_handle_set = to_handle_set - set([parent_tuple])
	return getNodeListToRoot(to_handle_set,category_parent_dict,parent_set)

#获取一个节点下面的所有孩子(代表词)
def getNodeChildren(category_child_dict,child_set,to_handle_set):
	if len(to_handle_set) == 0:
		return child_set
	for partial_tuple in to_handle_set:
		child_name = partial_tuple[0]
		relation = partial_tuple[1]
		child_set.add(child_name)
		to_handle_set = to_handle_set | category_child_dict[child_name]
		to_handle_set = to_handle_set - set([partial_tuple])
	return getNodeChildren(category_child_dict,child_set,to_handle_set)

#创建节点与其所有孩子集合(代表词)的映射字典
def createNodeChildrenDict(category_child_dict):
	node_children_dict = {}
	for category in category_child_dict.keys():
		child_set =  getNodeChildren(category_child_dict,set([]),category_child_dict[category])
		node_children_dict.setdefault(category,set([]))
		for child in child_set:
			node_children_dict[category].add(child)
	return node_children_dict

#获取情感词
def getCommenCategorySet():
	print 'getting comment category'
	comment_category_set = set([])
	infile = open('rule_template/comment.rule','rb')
	for row in infile:
		comment_category_set.add(row.strip().decode('utf-8'))
	return comment_category_set

#获取同义词
def getSynonym():
	print 'getting synonym set'
	category_synonyms_dict = {}
	handled_set = set([]) #存储已经处理过的词
	infile = open('rule_template/synonym.rule','rb')
	for row in infile:
		#该同义词集合的代表词
		delegate = row.strip().split('@')[0].decode('utf-8')
		#同义词集合
		#暂时不考虑一个词可以存在多个不同语义的同义词集合
		synonym_set = set(row.strip().split('@')[1].decode('utf-8').split(',')) - handled_set
		handled_set = handled_set | synonym_set
		for word in synonym_set:
			category_synonyms_dict.setdefault(word,[delegate,set([])])
			category_synonyms_dict[word][1] |= synonym_set
	return category_synonyms_dict

#获取偏序关系
def getPartial():
	print 'getting partial relationship'
	partial_dict = {}
	indicator_set = set([])
	infile = open('rule_template/partial.rule','rb')
	for row in infile:
		row = row.strip().decode('utf-8')
		if "<" in row and ">" in row:
			continue
		if row == "":
			continue
		#微弱偏序关系0，作推导词，不作tag
		if "~" in row:
			relation = 0
			master = row.split("~")[0]
			slaver = row.split("~")[1]
			indicator_set.add(slaver)
		#强偏序关系2
		elif '>>' in row:
			relation = 2
			master = row.split('>>')[0]
			slaver = row.split('>>')[1]
		#弱偏序关系1
		else:
			relation = 1
			master = row.split('>')[0]
			slaver = row.split('>')[1]
		#强推导词，不推荐
		if "@" in slaver:
			slaver = slaver.replace("@","")
			indicator_set.add(slaver)
		partial_dict.setdefault(master,set([])).add((slaver,relation))
	return partial_dict,indicator_set

#获取合并规则
def getCombine():
	print 'getting combine rule'
	combine_dict = {}
	infile = open('rule_template/combine.rule','rb')
	for row in infile:
		row = row.strip().decode('utf-8')
		main_category = row.split('==')[0]
		sub_category_set = set(row.split('==')[1].split(','))
		for sub_category in sub_category_set:
			combine_dict.setdefault(main_category,set([])).add((sub_category,3))
	return combine_dict

#获取消除歧义规则
def getDisambiguation():
	ambiguation_dict = {}
	infile = open('rule_template/disambiguation.rule','rb')
	for row in infile:
		row = row.strip().decode('utf-8')
		ambiguous_word = row.split('<>')[0]
		ambiguous_situations = row.split('<>')[1].split(',')
		ambiguation_dict.setdefault(ambiguous_word,set(ambiguous_situations))
	return ambiguation_dict

#填充层次结构树
def fillCategoryTree(category_parent_dict,category_child_dict,parent_child_dict,category_synonyms_dict):
	for master in parent_child_dict.keys():
		if master in category_synonyms_dict.keys():
			master_delegate = category_synonyms_dict[master][0]
		else:
			master_delegate = master
			category_synonyms_dict.setdefault(master_delegate,[master_delegate,set([master_delegate])])
		category_parent_dict.setdefault(master_delegate,set([]))
		for partial_tuple in parent_child_dict[master]:
			slaver = partial_tuple[0]
			relation = partial_tuple[1]
			if slaver in category_synonyms_dict.keys():
				slaver_delegate = category_synonyms_dict[slaver][0]
			else:
				slaver_delegate = slaver
				category_synonyms_dict.setdefault(slaver_delegate,[slaver_delegate,set([slaver_delegate])])
			category_parent_dict.setdefault(slaver_delegate,set([])).add((master_delegate,relation))
			category_child_dict.setdefault(slaver_delegate,set([]))
			category_child_dict.setdefault(master_delegate,set([])).add((slaver_delegate,relation))
	return 	category_parent_dict,category_child_dict

#构建层次结构树
def createCategoryTree(partial_dict,combine_dict,category_synonyms_dict):
	#category与父类关系
	category_parent_dict = {}
	#category与子类关系
	category_child_dict = {}
	#偏序关系
	category_parent_dict,category_child_dict = fillCategoryTree(category_parent_dict,category_child_dict,partial_dict,category_synonyms_dict)
	#合并关系
	category_parent_dict,category_child_dict = fillCategoryTree(category_parent_dict,category_child_dict,combine_dict,category_synonyms_dict)
	
	return category_parent_dict,category_child_dict,category_synonyms_dict

def main(category_name):
	reload(sys)
	sys.setdefaultencoding('utf-8')

	#获取规则模版(同义词，偏序关系，推导词，组合关系，情感词，歧义词)
	category_synonyms_dict = getSynonym()
	partial_dict,indicator_set = getPartial()
	combine_dict = getCombine()
	comment_category_set = getCommenCategorySet()
	ambiguation_dict = getDisambiguation()

	#从规则库中构建类目关系树
	category_parent_dict,category_child_dict,category_synonyms_dict = createCategoryTree(partial_dict,combine_dict,category_synonyms_dict)

	#标签推荐
	recommendTag(category_name,category_parent_dict,category_child_dict,category_synonyms_dict,indicator_set,comment_category_set,ambiguation_dict)

if __name__ == '__main__':
	category_name = u"办公商务_unmatch"
	main(category_name)

