#encoding=utf-8
import sys
import re

def main():
	reload(sys)
	sys.setdefaultencoding('utf-8')

	#获取规则模版(同义词，偏序关系，推导词，组合关系，情感词，歧义词)
	category_synonyms_dict = getSynonym('rule_template/synonym.rule')
	partial_dict,indicator_set = getPartial('rule_template/partial.rule')
	combine_dict = getCombine('rule_template/combine.rule')
	comment_category_set = getCommenCategorySet('rule_template/comment.rule')
	ambiguation_dict = getDisambiguation('rule_template/disambiguation.rule')

	#从规则库中构建类目关系树
	category_parent_dict,category_child_dict,category_synonyms_dict = createCategoryTree(partial_dict,combine_dict,category_synonyms_dict)

#类目id与类目name的映射
def idToName(category_id):
	id_category_dict = {11:u"系统安全",12:u"通讯社交",14:u"影视视听",16:u"便捷生活",17:u"办公商务",18:u"主题壁纸",\
						998:u"实用工具",102139:u"金融理财",102230:u"购物优惠",102233:u"运动健康"}
	return id_category_dict[int(category_id)]

#获取情感词
def getCommenCategorySet(file_addr):
	comment_category_set = set([])
	infile = open(file_addr,'rb')
	for row in infile:
		row = row.strip().decode('utf-8')
		if row == "":
			continue
		comment_category_set.add(row)
	return comment_category_set

#获取消除歧义规则
def getDisambiguation(file_addr):
	ambiguation_dict = {}
	infile = open(file_addr,'rb')
	for row in infile:
		row = row.strip().decode('utf-8')
		if row == "":
			continue
		ambiguous_word = row.split('<>')[0]
		ambiguous_situations = row.split('<>')[1].split(',')
		ambiguation_dict.setdefault(ambiguous_word,set(ambiguous_situations))
	return ambiguation_dict

#获取同义词
def getSynonym(file_addr):
	category_synonyms_dict = {}
	infile = open(file_addr,'rb')
	for row in infile:
		row = row.strip().decode('utf-8')
		if row == "":
			continue
		delegate = row.split('@')[0]
		
		synonym_set = set(row.split('@')[1].split(','))
		if delegate not in synonym_set:
			print "WARNING: 同义词代表词\""+delegate+"\"没有出现在同义词集合中"

		handle_set = synonym_set & set(category_synonyms_dict.keys())
		if len(handle_set) != 0:
			print "WARNING: 关于\""+delegate+"\"的同义词集合重复出现"
		for handle_word in handle_set:
			delegate = category_synonyms_dict[handle_word][0]
			synonym_set |= category_synonyms_dict[handle_word][1]

		for word in synonym_set:
			category_synonyms_dict.setdefault(word,[delegate,set([])])
			category_synonyms_dict[word][1] |= synonym_set
		
		category_synonyms_dict.setdefault(delegate,[delegate,set([])])
		category_synonyms_dict[delegate][1] |= synonym_set

	return category_synonyms_dict

#获取偏序关系
def getPartial(file_addr):
	partial_dict = {}
	indicator_set = set([])
	infile = open(file_addr,'rb')
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
		if "#" in slaver:
			slaver = slaver.replace("#","")
			indicator_set.add(slaver)
		partial_dict.setdefault(master,set([])).add((slaver,relation))
	return partial_dict,indicator_set

#获取合并规则
def getCombine(file_addr):
	combine_dict = {}
	infile = open(file_addr,'rb')
	for row in infile:
		row = row.strip().decode('utf-8')
		main_category = row.split('==')[0]
		sub_category_set = set(row.split('==')[1].split(','))
		for sub_category in sub_category_set:
			combine_dict.setdefault(main_category,set([])).add((sub_category,3))
	return combine_dict

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

#用正则表达式匹配连续英文和数字
def grabEnglish(text):
	english_list = []
	expression = ur"[a-zA-Z0-9-]+"
	pattern = re.compile(expression)
	english_list = [val.lower() for val in pattern.findall(text)] 
	return " ".join(english_list)

#歧义消除
def isAmbiguous(category,ambiguation_dict,document):
	is_ambiguous = False
	if category in ambiguation_dict.keys():
		for ambiguous_situation in ambiguation_dict[category]:
			if ambiguous_situation in document:
				is_ambiguous = True
	return is_ambiguous

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

#创建level与类目词之间映射字典
def createLevelCategoryDict(main_category,candidate_tag_set,category_parent_dict,category_child_dict,category_synonyms_dict):
	level_category_dict = {}
	for node in candidate_tag_set:
		node_delegate = category_synonyms_dict[node][0]
		depth_set = getNodeDepthGivenRoot(set([main_category]),node_delegate,category_child_dict,1,set([]))
		for depth in depth_set:
			level_category_dict.setdefault(depth,set()).add(node)
	return level_category_dict

#获取query节点在root节点下出现的所有深度可能
def getNodeDepthGivenRoot(root_set,query,category_child_dict,depth,depth_set):
	if query not in category_child_dict.keys():
		return set([-1])
	if query in root_set:
		return set([0])
	next_root_set = set([])
	for root in root_set:
		for child_tuple in category_child_dict[root]:
			child = child_tuple[0]
			if child == query:
				depth_set.add(depth)
			else:	
				next_root_set.add(child)
	if len(next_root_set) == 0:
		return depth_set
	depth += 1
	return getNodeDepthGivenRoot(next_root_set,query,category_child_dict,depth,depth_set)

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

if __name__ == '__main__':
	main()

