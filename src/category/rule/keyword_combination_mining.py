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
	id_category_dict = {11:u"系统安全",12:u"通讯社交",14:u"影视视听",16:u"便捷生活",17:u"办公商务",18:u"主题壁纸",\
						998:u"实用工具",102139:u"金融理财",102230:u"购物优惠",102233:u"运动健康"}
	return id_category_dict[int(category_id)]


def combineNeighborWord(seg_list,query_keyword):
	phrase_fre_dict = {}
	for i in range(len(seg_list)):
		word = seg_list[i]
		if query_keyword in word:
			if len(word) > len(query_keyword):
				phrase_fre_dict.setdefault(word,0)
				phrase_fre_dict[word] += 1
			if i-1 != 0:
				phrase_fre_dict.setdefault(seg_list[i-1]+word,0)
				phrase_fre_dict[seg_list[i-1]+word] += 1
			if i+1 != len(seg_list):
				phrase_fre_dict.setdefault(word+seg_list[i+1],0)
				phrase_fre_dict[word+seg_list[i+1]] += 1
	return phrase_fre_dict



def mineKeywordCombination(category_id,query_keyword):

	#主类目名称
	main_category = idToName(category_id)

	jieba.load_userdict('../../../data/jieba_userdict.txt')
	stopword_set = text_process.getStopword('../../../data/stopword.txt')

	combination_fre_dict = {}

	outfile = open('keyword_combination.txt','wb')
	#遍历主类目下的app
	infile = open('../data/'+str(category_id)+'.json','rb')
	for row in infile:
		
		json_obj = json.loads(row.strip())
		app_id = int(json_obj["id"])
		app_name = json_obj["title"]
		app_brief = json_obj["brief"]
		app_download = int(json_obj["download_times"])
		app_name_seg = [word for word in jieba.cut(app_name) if word not in stopword_set and text_process.isChinese(word)]
		app_brief_seg = [word for word in jieba.cut(app_brief) if word not in stopword_set and text_process.isChinese(word)]
		app_name_brief = app_name+" "+app_brief

		app_name_combination_dict = combineNeighborWord(app_name_seg,query_keyword)
		for word in app_name_combination_dict.keys():
			combination_fre_dict.setdefault(word,0)
			combination_fre_dict[word] += app_name_combination_dict[word]
		
		app_brief_combination_dict = combineNeighborWord(app_brief_seg,query_keyword)
		for word in app_brief_combination_dict.keys():
			combination_fre_dict.setdefault(word,0)
			combination_fre_dict[word] += app_brief_combination_dict[word]


	sorted_list = sorted(combination_fre_dict.items(),key=lambda p:p[1],reverse=True)
	for val in sorted_list:
		if val[1] >= 2:
			print val[0]+','+str(val[1])
			outfile.write(val[0]+','+str(val[1])+'\r\n')


def main(category_id,query_keyword):
	reload(sys)
	sys.setdefaultencoding('utf-8')

	mineKeywordCombination(category_id,query_keyword)

if __name__ == '__main__':
	category_id = u"102230"
	query_keyword = u"邮费"

	main(category_id,query_keyword)

