#encoding=utf-8
import sys
sys.path.append('../../common')
import text_process
import json
import jieba,jieba.posseg,jieba.analyse
import itertools

def cidToName(category_id):
	return u'通讯社交'

#去除一些被否定的类目词
def negativeCategory(text,category_domain_set):
	negative_category = set([])

	return negative_category

def recommendTag(category_id,category_parent_dict,category_child_dict,category_synonyms_dict,comment_category_set,ambiguation_dict):
	category_name = cidToName(category_id)
	outfile_txt = open('tag_recommend_result.txt','wb')
	outfile_json = open('tag_recommend_result.json','wb')

	jieba.load_userdict('../../../data/jieba_userdict.txt')
	stopword_set = text_process.getStopword('../../../data/stopword.txt')

	#构建候选词集合，category_domain_set
	node_children_dict = createNodeChildrenDict(category_child_dict)
	category_domain_set = set([])
	for category in node_children_dict[category_name]:
		if category in category_synonyms_dict.keys():
			category_domain_set |= category_synonyms_dict[category][1]
	category_domain_set |= node_children_dict[category_name]

	category_supportor_dict = {}

	#level3候选词
	level3_category_set = getNextLevelCategorySet(category_synonyms_dict,category_child_dict,category_name)
	for level3_category in level3_category_set:
		if u'[' in level3_category and u']' in level3_category:
			level3_category_set = level3_category_set - set([level3_category])
			category_supportor_dict.setdefault(level3_category, getNextLevelCategorySet(category_synonyms_dict,category_child_dict,level3_category))
		# if u'(' in level3_category and u')' in level3_category:
		# 	level3_category_set = level3_category_set | getNextLevelCategorySet(category_synonyms_dict,category_child_dict,level3_category)
		# 	level3_category_set = level3_category_set - set([level3_category])

	#level4候选词
	level4_category_set = set([])
	for level3_category in level3_category_set:
		level4_category_set = level4_category_set | getNextLevelCategorySet(category_synonyms_dict,category_child_dict,level3_category)
		for level4_category in level4_category_set:
			if u'[' in level4_category and u']' in level4_category:
				level4_category_set = level4_category_set - set([level4_category])
				category_supportor_dict.setdefault(level4_category, getNextLevelCategorySet(category_synonyms_dict,category_child_dict,level4_category))
			# if u'(' in level4_category and u')' in level4_category:
			# 	level4_category_set = level4_category_set | getNextLevelCategorySet(category_synonyms_dict,category_child_dict,level4_category)
			# 	level4_category_set = level4_category_set - set([level4_category])

	print ' '.join(level3_category_set)
	print ' '.join(level4_category_set)

	# for category in category_supportor_dict.keys():
	# 	print category
	# 	print ' '.join(category_supportor_dict[category])

	#未被匹配到的app
	others_app = {}

	print 'reading app json'
	infile = open('../data/'+category_id+'.json','rb')
	for row in infile:
		output_dict = {}
		tag_recommend_set = set([])
		json_obj = json.loads(row.strip())
		app_id = int(json_obj["id"])
		app_name = json_obj["title"]
		app_brief = json_obj["brief"]
		app_download = int(json_obj["download_times"])
		app_brief_seg = [word for word in jieba.cut(app_brief) if word not in stopword_set and text_process.isChinese(word)]
		
		output_dict["soft_id"] = app_id
		output_dict["content"] = {}

		#情感词匹配
		for comment_word in comment_category_set:
			if comment_word in app_name or comment_word in app_brief:
				# tag_recommend_set.add(comment_word)
				output_dict.setdefault("character",[]).append(comment_word)

		#非情感词匹配
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
				strong_parent_set = getNodeListToRoot(category_parent_dict[category_delegate],category_parent_dict,set([]))
				tag_recommend_set = tag_recommend_set | strong_parent_set

				for partial_tuple in category_parent_dict[category_delegate]:
					parent_name = partial_tuple[0]
					relation = partial_tuple[1]
					#隐节点
					if u'(' in parent_name and u')' in parent_name:
						hidden_node_list = list(getNextLevelCategorySet(category_synonyms_dict,category_child_dict,parent_name))
						output_dict.setdefault(parent_name,[]).append(category)
						tag_recommend_set.add(parent_name)

		#找出匹配到的三四级类目词
		level3_match_category_set = set([])
		level4_match_category_set = set([])
		for tag in [tag for tag in tag_recommend_set if tag in level3_category_set]:
			level3_match_category_set.add(tag)
		for tag in [tag for tag in tag_recommend_set if tag in level4_category_set]:
			level4_match_category_set.add(tag)

		# #通过判断子类匹配个数确定是否是这个类目
		# for category in (level3_category_set - level3_match_category_set):
		# 	match_counter = 0
		# 	children_set = node_children_dict[category_synonyms_dict[category][0]]
		# 	for child in children_set:
		# 		if child in app_name+' '+app_brief:
		# 			match_counter += 1
		# 	if match_counter >= 3:
		# 		tag_recommend_set.add(category_synonyms_dict[category][0])
		# 		level3_match_category_set.add(category_synonyms_dict[category][0])
	
		# for category in (level4_category_set - level4_match_category_set):
		# 	match_counter = 0
		# 	children_set = node_children_dict[category_synonyms_dict[category][0]]
		# 	for child in children_set:
		# 		if child in app_name+' '+app_brief:
		# 			match_counter += 1
		# 	if match_counter >= 3:
		# 		tag_recommend_set.add(category_synonyms_dict[category][0])
		# 		level4_match_category_set.add(category_synonyms_dict[category][0])

		# for category in category_supportor_dict.keys():
		# 	supportors = category_supportor_dict[category]
		# 	category_format = category_synonyms_dict[category.lstrip('[').rstrip(']')][0]
		# 	if category_format not in level3_match_category_set | level4_match_category_set:
		# 		match_counter = 0
		# 		for supportor in supportors:
		# 			if supportor in app_name+' '+app_brief:
		# 				match_counter += 1
		# 		if match_counter >= 3:
		# 			tag_recommend_set.add(category_format)
		# 			if category_format in level3_category_set:
		# 				level3_match_category_set.add(category_format)
		# 			elif category_format in level4_category_set:
		# 				level4_match_category_set.add(category_format)

		
		is_match_level3_level4 = False
		for tag in tag_recommend_set:

			#level3
			if tag in level3_match_category_set:
				output_dict["content"].setdefault(tag,{})
			
			#level4
			if tag in level4_match_category_set:
				for level3_match_category in [level3_match_category for level3_match_category in level3_match_category_set]:
					level3_match_category = category_synonyms_dict[level3_match_category][0]
					if tag in node_children_dict[level3_match_category]:
						output_dict["content"].setdefault(level3_match_category,{}).setdefault(tag,[])
						is_match_level3_level4 = True
	
			#lower than level3.4
			if tag not in level3_match_category_set or tag not in level4_match_category_set:
				for level3_match_category in [level3_match_category for level3_match_category in level3_match_category_set]:
					level3_match_category = category_synonyms_dict[level3_match_category][0]
					if tag in node_children_dict[level3_match_category]:
						for level4_match_category in [level4_match_category for level4_match_category in level4_match_category_set]:
							level4_match_category = category_synonyms_dict[level4_match_category][0]
							if tag in node_children_dict[level4_match_category]:
								output_dict["content"].setdefault(level3_match_category,{}).setdefault(level4_match_category,[]).append(tag)

 		if is_match_level3_level4:
 			outfile_json.write(json.dumps(output_dict,ensure_ascii=False)+'\r\n')
 		else:
 			others_app.setdefault(app_name,[app_download,' '.join(app_brief_seg)])

		outfile_txt.write(str(app_id)+'<@>'+app_name+'<@>'+' '.join(app_brief_seg)+'<@>')
		outfile_txt.write(' '.join(tag_recommend_set))
		outfile_txt.write('\r\n')

	sorted_list = sorted(others_app.items(),key=lambda p:p[1][0],reverse=True)
	outfile_others = open('others.txt','wb')
	for val in sorted_list:
		outfile_others.write(val[0]+'<@>'+val[1][1]+'\r\n')

#给定query，获取其下一级的类目词
def getNextLevelCategorySet(category_synonyms_dict,category_child_dict,query):
	next_level_category_set = set([])
	#查询节点的同义词集合
	query_syn_set = set([query])
	if query in category_synonyms_dict.keys():
		query_syn_set = category_synonyms_dict[query][1]
	for query_syn in query_syn_set:
		if query_syn not in category_child_dict.keys():
			continue
		for partial_tuple in category_child_dict[query_syn]:
			child_name = partial_tuple[0]
			if child_name in category_synonyms_dict.keys():
				next_level_category_set |= category_synonyms_dict[child_name][1]
			else:
				next_level_category_set |= set([child_name])
	return next_level_category_set

#向上获取其强联通路径的所有节点，放到strong_parent_set中
def getNodeListOnStrongPath(to_handle_set,category_parent_dict,strong_parent_set):
	if len(to_handle_set) == 0:
		return strong_parent_set
	# temp_to_handle_set = to_handle_set
	for parent_tuple in to_handle_set:
		parent_name = parent_tuple[0]
		relation = parent_tuple[1]
		if relation == 2:
			strong_parent_set.add(parent_name)
			to_handle_set = to_handle_set | category_parent_dict[parent_name]
		to_handle_set = to_handle_set - set([parent_tuple])
	return getNodeListOnStrongPath(to_handle_set,category_parent_dict,strong_parent_set)

def getNodeListToRoot(to_handle_set,category_parent_dict,parent_set):
	if len(to_handle_set) == 0:
		return parent_set
	for parent_tuple in to_handle_set:
		parent_name = parent_tuple[0]
		relation = parent_tuple[1]
		parent_set.add(parent_name)
		to_handle_set = to_handle_set | category_parent_dict[parent_name]
		to_handle_set = to_handle_set - set([parent_tuple])
	return getNodeListToRoot(to_handle_set,category_parent_dict,parent_set)

#获取一个节点下面的所有孩子
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

#创建节点与其孩子的映射字典
def createNodeChildrenDict(category_child_dict):
	node_children_dict = {}
	for category in category_child_dict.keys():
		child_set =  getNodeChildren(category_child_dict,set([]),category_child_dict[category])
		node_children_dict.setdefault(category,set([]))
		for child in child_set:
			node_children_dict[category].add(child)
	return node_children_dict

#获取地理位置词
def getLocationCategorySet():
	print 'getting comment category'
	location_category_set = set([])
	infile = open('rule_template/location.rule','rb')
	for row in infile:
		location_category_set.add(row.strip().decode('utf-8'))
	return location_category_set

#获取情感词
def getCommenCategorySet():
	print 'getting comment category'
	comment_category_set = set([])
	infile = open('rule_template/comment.rule','rb')
	for row in infile:
		comment_category_set.add(row.strip().decode('utf-8'))
	return comment_category_set

#获取类目停用词
def getFilterCategorySet():
	print 'getting filtered category'
	filter_category_set = set([])
	infile = open('rule_template/category_filter.rule','rb')
	for row in infile:
		filter_category_set.add(row.strip().decode('utf-8'))
	return filter_category_set

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
		partial_dict.setdefault(master,set([])).add((slaver,relation_weight))
	return partial_dict

#获取合并规则
def getCombine():
	print 'getting combine rule'
	combine_dict = {}
	infile = open('rule_template/combine.rule','rb')
	for row in infile:
		row = row.strip().decode('utf-8')
		main_category = row.split('==')[0]
		if main_category.isdigit():
			continue
		sub_category_set = set(row.split('==')[1].split(','))
		combine_dict.setdefault(main_category,sub_category_set)
	return combine_dict

#获取消除歧义规则
#例如soft_id=186342
def getDisambiguation():
	ambiguation_dict = {}
	infile = open('rule_template/disambiguation.rule','rb')
	for row in infile:
		row = row.strip().decode('utf-8')
		ambiguous_word = row.split('<>')[0]
		ambiguous_situations = row.split('<>')[1].split(',')
		ambiguation_dict.setdefault(ambiguous_word,set(ambiguous_situations))
	return ambiguation_dict

#弱偏序1，强偏序2，合并3
#维护与父节点的关系
def createCategoryTree(partial_dict,combine_dict,category_synonyms_dict):
	category_parent_dict = {}
	category_child_dict = {}
	
	#偏序词
	for master in partial_dict.keys():
		if master in category_synonyms_dict.keys():
			master_delegate = category_synonyms_dict[master][0]
		else:
			master_delegate = master
			category_synonyms_dict.setdefault(master_delegate,[master_delegate,set([master_delegate])])
		category_parent_dict.setdefault(master_delegate,set([]))
		for partial_tuple in partial_dict[master]:
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
	
	#合并词
	for master in combine_dict.keys():
		if master in category_synonyms_dict.keys():
			master_delegate = category_synonyms_dict[master][0]
		else:
			master_delegate = master
			category_synonyms_dict.setdefault(master_delegate,[master_delegate,set([master_delegate])])
		category_parent_dict.setdefault(master_delegate,set([]))
		for slaver in combine_dict[master]:
			if slaver in category_synonyms_dict.keys():
				slaver_delegate = category_synonyms_dict[slaver][0]
			else:
				slaver_delegate = slaver
				category_synonyms_dict.setdefault(slaver_delegate,[slaver_delegate,set([slaver_delegate])])
			category_parent_dict.setdefault(slaver_delegate,set([])).add((master_delegate,3))
			category_child_dict.setdefault(slaver_delegate,set([]))
			category_child_dict.setdefault(master_delegate,set([])).add((slaver_delegate,3))

	return category_parent_dict,category_child_dict,category_synonyms_dict

def main(category_id):
	reload(sys)
	sys.setdefaultencoding('utf-8')

	#暂时不处理的词放在filter_category_set中
	filter_category_set = getFilterCategorySet() #类目停用词
	location_category_set = getLocationCategorySet() #地理位置词
	comment_category_set = getCommenCategorySet() #情感词
	filter_category_set = filter_category_set | comment_category_set | location_category_set

	#获取规则模版
	category_synonyms_dict = getSynonym()
	partial_dict = getPartial()
	combine_dict = getCombine()
	ambiguation_dict = getDisambiguation()

	#从规则库中构建类目关系树
	category_parent_dict,category_child_dict,category_synonyms_dict = createCategoryTree(partial_dict,combine_dict,category_synonyms_dict)

	#标签推荐
	recommendTag(category_id,category_parent_dict,category_child_dict,category_synonyms_dict,comment_category_set,ambiguation_dict)

if __name__ == '__main__':
	category_id = u"12"
	main(category_id)

