#encoding=utf-8
import sys
import json
import jieba,jieba.posseg,jieba.analyse


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
	infile = open('../../category/rule/rule_template/partial.rule','rb')
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
	infile = open('../../category/rule/rule_template/combine.rule','rb')
	for row in infile:
		row = row.strip().decode('utf-8')
		main_category = row.split('==')[0]
		if main_category.isdigit():
			continue
		sub_category_set = set(row.split('==')[1].split(','))
		combine_dict.setdefault(main_category,sub_category_set)
	return combine_dict

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

#转化为json格式
def convertToJsonTree(category_parent_dict,category_synonyms_dict):
	node_dict = {}
	#将category_parent_dict转成node_dict,category_parent_dict中的每个category作为node_dict中的一个节点
	for category in category_parent_dict.keys():
		synonym_set = category_synonyms_dict[category][1]
		node_delegate_name = category_synonyms_dict[category][0]
		node_parent = category_parent_dict[category]
		for synonym in synonym_set:
			if synonym in category_parent_dict.keys():
				node_parent |= category_parent_dict[synonym]
		node_dict[node_delegate_name] = {'name':node_delegate_name,'synonyms':','.join(synonym_set),'parent':node_parent,'children':[]}
	
	#为节点添加children
	for category in node_dict.keys():
		for partial_tuple in node_dict[category]['parent']:
			parent_name = partial_tuple[0]
			relation = partial_tuple[1]
			if parent_name in node_dict.keys():
				node_dict[parent_name]['children'].append(node_dict[category])
			elif parent_name in category_synonyms_dict.keys():
				node_delegate_name = category_synonyms_dict[parent_name][0]
				node_dict[node_delegate_name]['children'].append(node_dict[category])		

	for category in node_dict.keys():
		#如果没有父类，则认为是与根节点相连
		if len(node_dict[category]['parent']) == 0:
			node_dict[category].setdefault('is_connect_root',1)
		else:
			node_dict[category].setdefault('is_connect_root',0)
	
	#删除掉所有节点的parent字段
	for category in node_dict.keys():
		del node_dict[category]['parent']

    #去除不与根节点相连的
	for node_name in node_dict.keys():	
		if node_dict[node_name]['is_connect_root'] != 1:
			del node_dict[node_name]

	return node_dict

def main():
	reload(sys)
	sys.setdefaultencoding('utf-8')

	#获取规则模版
	category_synonyms_dict = getSynonym()
	partial_dict = getPartial()
	combine_dict = getCombine()

	#从规则库中构建类目关系树
	category_parent_dict,category_child_dict,category_synonyms_dict = createCategoryTree(partial_dict,combine_dict,category_synonyms_dict)

	#转成json格式
	tree = convertToJsonTree(category_parent_dict,category_synonyms_dict)

	#外面套一层根节点
	json_tree = {}
	json_tree['name'] = u'类目树'
	json_tree['children'] = []
	for node_name in tree.keys():
		json_tree['children'].append(tree[node_name])

	#输出json	
	encodedjson = json.dumps(json_tree)
	outfile = open('data.json','wb')
	outfile.write(encodedjson)


if __name__ == '__main__':
	main()

