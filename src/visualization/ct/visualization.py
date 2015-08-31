#encoding=utf-8
import sys
sys.path.append('../../category/rule')
import json
import jieba,jieba.posseg,jieba.analyse
import rule_base

#数据可视化
def main():
	reload(sys)
	sys.setdefaultencoding('utf-8')

	#获取规则模版(同义词，偏序关系，组合关系)
	category_synonyms_dict = rule_base.getSynonym('../../category/rule/rule_template/synonym.rule')
	partial_dict,indicator_set = rule_base.getPartial('../../category/rule/rule_template/partial.rule')
	combine_dict = rule_base.getCombine('../../category/rule/rule_template/combine.rule')

	#从规则库中构建类目关系树
	category_parent_dict,category_child_dict,category_synonyms_dict = rule_base.createCategoryTree(partial_dict,combine_dict,category_synonyms_dict)

	#转成json格式
	tree = convertToJsonTree(category_parent_dict,category_synonyms_dict,indicator_set)

	#输出json	
	encodedjson = json.dumps(tree[u"根节点"])
	outfile = open('data.json','wb')
	outfile.write(encodedjson)

	outfile = open("synonym.csv","wb")
	outfile.write("delegate,synonym_set\r\n")
	delegate_handle_set = set([])
	for category in category_synonyms_dict.keys():
		if "(" in category and ")" in category:
			continue
		delegate = category_synonyms_dict[category][0]
		if delegate not in delegate_handle_set:
			outfile.write(delegate+","+" ".join(category_synonyms_dict[category][1])+"\r\n")
			delegate_handle_set |= set([delegate])


#转化为json格式
def convertToJsonTree(category_parent_dict,category_synonyms_dict,indicator_set):
	node_dict = {}
	#将category_parent_dict转成node_dict,category_parent_dict中的每个category作为node_dict中的一个节点
	for category in category_parent_dict.keys():
		synonym_set = category_synonyms_dict[category][1]
		node_delegate_name = category_synonyms_dict[category][0]
		node_parent = category_parent_dict[category]
		for synonym in synonym_set:
			if synonym in category_parent_dict.keys():
				node_parent |= category_parent_dict[synonym]
		node_dict[node_delegate_name] = {'name':node_delegate_name,'supportors':[],'synonyms':','.join(synonym_set),'parent':node_parent,'children':[]}
	
	#为节点添加children
	for category in node_dict.keys():
		for partial_tuple in node_dict[category]['parent']:
			parent_name = partial_tuple[0]
			relation = partial_tuple[1]
			if relation == 0:
				node_dict[parent_name]['supportors'].append(category)
			if parent_name in node_dict.keys():
				node_dict[parent_name]['children'].append(node_dict[category])
			elif parent_name in category_synonyms_dict.keys():
				node_delegate_name = category_synonyms_dict[parent_name][0]
				node_dict[node_delegate_name]['children'].append(node_dict[category])		
	
	#删除推导词
	for category in node_dict.keys():
		supportors = node_dict[category]['supportors']
		remove_children = []
		for child_node in node_dict[category]['children']:
			child_name = child_node['name']
			if child_name in supportors:
				remove_children.append(child_node)
		for remove_child in remove_children:
			node_dict[category]['children'].remove(remove_child)

	#删除掉所有节点的parent字段
	for category in node_dict.keys():
		del node_dict[category]['parent']

	return node_dict

if __name__ == '__main__':
	main()

