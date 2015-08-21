#encoding=utf-8
import sys
sys.path.append('../../common')
import text_process
import json
import jieba,jieba.posseg,jieba.analyse
import itertools

#类目id与类目名称映射
def cidToName(category_id):
	return u"运动健康";
	# return u"通讯社交"
	# return u"金融理财"

#标签推荐
def recommendTag(category_id,category_parent_dict,category_child_dict,category_synonyms_dict,category_indicator_dict,comment_category_set,ambiguation_dict):
	#待处理的主类目
	main_category_name = cidToName(category_id)

	outfile_json = open('tag_recommend_result.json','wb')

	jieba.load_userdict('../../../data/jieba_userdict.txt')
	stopword_set = text_process.getStopword('../../../data/stopword.txt')

	#主类目下的所有节点以及节点的同义词，作为候选词集合category_domain_set
	category_domain_set = set([])
	node_children_dict = createNodeChildrenDict(category_child_dict)
	category_delegate_domain_set = node_children_dict[main_category_name]
	for category in category_delegate_domain_set:
		if category in category_synonyms_dict.keys():
			category_domain_set |= category_synonyms_dict[category][1]
	category_domain_set |= node_children_dict[main_category_name]

	match_counter = 0
	all_app_counter = 0

	#未被匹配到的app
	others_app = {}
	#遍历json
	infile = open('../data/'+category_id+'.json','rb')
	for row in infile:
		all_app_counter += 1
		output_dict = {}
		
		json_obj = json.loads(row.strip())
		app_id = int(json_obj["id"])
		app_name = json_obj["title"]
		app_brief = json_obj["brief"]
		app_download = int(json_obj["download_times"])
		app_brief_seg = [word for word in jieba.cut(app_brief) if word not in stopword_set and text_process.isChinese(word)]
		
		output_dict["id"] = app_id
		output_dict["content"] = {}

		#推导词匹配
		indicators = set([])
		for category in category_indicator_dict.keys():
			for indicator in category_indicator_dict[category]:
				indicator_syn_set = set([indicator])
				if indicator in category_synonyms_dict.keys():
					indicator_syn_set |= category_synonyms_dict[indicator][1]
				for indi in indicator_syn_set:
					if indi in app_name+" "+app_brief:
						if indi in category_synonyms_dict.keys():
							indicators.add(category_synonyms_dict[indi][0])
						else:
							indicators.add(indi)

		#情感词匹配
		for comment_word in comment_category_set:
			if comment_word in app_name or comment_word in app_brief:
				output_dict.setdefault("character",[]).append(comment_word)
		
		#对主类目下的候选词进行匹配
		tag_recommend_set = set([])
		for category in category_domain_set:
			#如果候选词出现在标题或描述文本中
			if category in app_name or category in app_brief:
				#消除歧义，发现这个category是歧义词时，暂时不处理这个category
				is_ambiguous = False
				if category in ambiguation_dict.keys():
					for ambiguous_situation in ambiguation_dict[category]:
						if ambiguous_situation in app_name or ambiguous_situation in app_brief:
							is_ambiguous = True
				if is_ambiguous:
					continue		

				#该添加节点的代表词
				category_delegate = category_synonyms_dict[category][0]
				tag_recommend_set.add(category_delegate)
				
				#向上遍历，找出与该节点是强关系的父类
				strong_parent_set = getNodeListOnStrongPath(category_parent_dict[category_delegate],category_parent_dict,set([]))
				tag_recommend_set = tag_recommend_set | strong_parent_set

				for partial_tuple in category_parent_dict[category_delegate]:
					parent_name = partial_tuple[0]
					relation = partial_tuple[1]

					# #隐节点
					# if u'(' in parent_name and u')' in parent_name and parent_name in category_domain_set:	
					# 	output_dict.setdefault(parent_name,[]).append(category_delegate)
					# 	tag_recommend_set.add(parent_name)
		
		#隐节点
		for tag in tag_recommend_set:
			if u'(' in tag and u')' in tag:
				hidden_node_next_level = getNextLevelCategorySet(category_synonyms_dict,category_child_dict,tag)
				for hidden_node_next_level_item in hidden_node_next_level:
					hidden_node_next_level_item = category_synonyms_dict[hidden_node_next_level_item][0]
					if len(node_children_dict[hidden_node_next_level_item] & tag_recommend_set)>0:
						tag_recommend_set.add(tag)
						output_dict.setdefault(tag,[]).append(hidden_node_next_level_item)

		#对没有匹配到的节点，自下而上地判断其所有子节点匹配个数确定是否是这个类目
		tag_recommend_set = upwardInfer(main_category_name,category_delegate_domain_set,category_synonyms_dict,node_children_dict,category_child_dict,category_indicator_dict,indicators,tag_recommend_set)

		#构建输出字典
		top_level_list = getNextLevelCategorySet(category_synonyms_dict,category_child_dict,main_category_name)
		content = {}
		for tag in tag_recommend_set:
			content[tag] = {}
		for node in tag_recommend_set:
			for partial_tuple in category_parent_dict[node]:
				parent_name = partial_tuple[0]
				if parent_name == main_category_name:
					continue
				if parent_name in content.keys():
					content[parent_name][node] = content[node]
		
		for top_level in content.keys():
			if top_level not in top_level_list:
				del content[top_level]

		output_dict['content'] = content

		if len(content.keys()) !=0:
			match_counter += 1
			# if app_download < 10000000:
			outfile_json.write(json.dumps(output_dict,ensure_ascii=False)+'\r\n')
		else:
			others_app.setdefault(app_name,[app_download,' '.join(app_brief_seg)])

	print "覆盖率: "+str(1.0*match_counter/all_app_counter)
	#剩下没有匹配到的按下载量排序，输出
	sorted_list = sorted(others_app.items(),key=lambda p:p[1][0],reverse=True)
	outfile_others = open('others.txt','wb')
	for val in sorted_list:
		outfile_others.write(val[0]+'<@>'+val[1][1]+'\r\n')

	#统计没有匹配到的app的词频
	word_fre = {}
	outfile_others_word = open('others_word.txt','wb')
	for app in others_app.keys():
		for word in others_app[app][1].split():
			word_fre.setdefault(word,0)
			word_fre[word] += 1
	sorted_list = sorted(word_fre.items(),key=lambda p:p[1],reverse=True)
	for val in sorted_list:
		outfile_others_word.write(val[0]+','+str(val[1])+'\r\n')

#向上推导
def upwardInfer(main_category_name,category_delegate_domain_set,category_synonyms_dict,node_children_dict,category_child_dict,category_indicator_dict,indicators,tag_recommend_set):
	level_category_dict = {}
	for node in category_delegate_domain_set:
		min_depth = getNodeMinDepthGivenRoot(set([main_category_name]),category_synonyms_dict[node][0],category_child_dict,1)
		level_category_dict.setdefault(min_depth,set()).add(node)
	max_depth = max(level_category_dict.keys())
	
	#从最底层开始匹配
	for depth in reversed(range(1,max_depth+1)):
		if depth-1 == 0:
			continue
		if depth not in level_category_dict.keys():
			continue
		handling_level_category_set = level_category_dict[depth]
		unmatch_node_set = handling_level_category_set - tag_recommend_set
		for unmatch_node in unmatch_node_set:
			unmatch_node_children = node_children_dict[unmatch_node]
			if unmatch_node in category_indicator_dict.keys():
				unmatch_node_children |= category_indicator_dict[unmatch_node]
			match_children = unmatch_node_children&(tag_recommend_set|indicators)
			if len(match_children) >= 3:
				tag_recommend_set.add(unmatch_node)
	return tag_recommend_set

#获取query节点在root节点下的最小深度
def getNodeMinDepthGivenRoot(root_set,query,category_child_dict,depth):
	if query not in category_child_dict.keys():
		return -1
	if query in root_set:
		return 0
	next_root_set = set([])
	for root in root_set:
		for child_tuple in category_child_dict[root]:
			child = child_tuple[0]
			if child == query:
				return depth
			else:	
				next_root_set.add(child)
	depth += 1
	return getNodeMinDepthGivenRoot(next_root_set,query,category_child_dict,depth)

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
	infile = open('../../category/rule/rule_template/synonym.rule','rb')
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
	category_indicator_dict = {}
	infile = open('rule_template/partial.rule','rb')
	for row in infile:
		row = row.strip().decode('utf-8')
		if row == "":
			continue
		#强偏序关系2
		if '>>' in row:
			relation_weight = 2
			master = row.split('>>')[0]
			slaver = row.split('>>')[1]
		#弱偏序关系1
		else:
			relation_weight = 1
			master = row.split('>')[0]
			slaver = row.split('>')[1]
		if '[' in master and ']' in master:
			master = master.lstrip('[').rstrip(']')
			category_indicator_dict.setdefault(master,set([])).add(slaver)
		else:
			partial_dict.setdefault(master,set([])).add((slaver,relation_weight))
	return partial_dict,category_indicator_dict

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

def main(category_id):
	reload(sys)
	sys.setdefaultencoding('utf-8')

	#获取规则模版(同义词，偏序关系，组合关系，情感词，歧义词)
	category_synonyms_dict = getSynonym()
	partial_dict,category_indicator_dict = getPartial()
	combine_dict = getCombine()
	comment_category_set = getCommenCategorySet()
	ambiguation_dict = getDisambiguation()

	#从规则库中构建类目关系树
	category_parent_dict,category_child_dict,category_synonyms_dict = createCategoryTree(partial_dict,combine_dict,category_synonyms_dict)

	#标签推荐
	recommendTag(category_id,category_parent_dict,category_child_dict,category_synonyms_dict,category_indicator_dict,comment_category_set,ambiguation_dict)

if __name__ == '__main__':
	# category_id = u"102139"
	category_id = u"999"
	# category_id = u"12"
	main(category_id)

