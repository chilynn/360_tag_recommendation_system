#encoding=utf-8
import sys
sys.path.append("../common/")
import os
import text_process
import file_utils
import json
import jieba,jieba.posseg,jieba.analyse
from gensim.models import Word2Vec
import regular_template
import itertools

baidu_tag_keys = [u"别名",u"简称",u"其他名称",u"英文缩写"]


def readJson(word2vec_model):
	print 'parsing json'
	stopword_set = text_process.getStopword('../../data/stopword.txt')
	outfile = open('baidu_baike_definition.txt','wb')
	infile = open('../scrapy/baidu_baike_definition/crawl_data/definition.json','rb')
	row_index = 0
	for row in infile:
		# row_index += 1
		# if row_index > 30000:
		# 	break
		json_str = row.strip()
		json_str = json_str.lstrip('[')
		json_str = json_str.rstrip(',')
		json_str = json_str.rstrip(']')
		json_obj = json.loads(json_str)

		query_word = json_obj['query_category']
		is_only = json_obj['is_only']
		ambiguous_tips = json_obj['ambiguous_tips']
		title = json_obj['title']
		title_note = json_obj['title_note']
		structure_tag = json_obj['structure_tag']
		abstract = json_obj['abstract']
		content = json_obj['content']

		word_synonyms_set = set([query_word])
		
		if is_only:
			word_synonyms_set.add(title)
	
		alias_list = []
		alias_list_clean = []
		for tag_key in structure_tag.keys():
			tag_key = tag_key.decode('utf-8')
			tag_value = structure_tag[tag_key].decode('utf-8')
			tag_key_clean = tag_key.replace(u' ','')
			if tag_key_clean in baidu_tag_keys:
				if tag_value != u"无":
					alias_list.append(tag_value)
		for alias in alias_list:
			alias = regular_template.cleanNote(alias)
			if regular_template.isEnglishPhrase(alias):
				print alias
				continue
			for word in alias.replace(u","," ").replace(u"、"," ").replace(u"，"," ").replace(u";"," ").replace(u"；"," ").split():
				word = word.replace(u"“","").replace(u"”","").replace(u" ","").rstrip(u"等")
				alias_list_clean.append(regular_template.cleanDefinition(word))

		alias_text = ' '.join(alias_list_clean)

		if is_only:
			word_synonyms_set = word_synonyms_set | set(alias_list_clean)

		
		ambiguous_tips = regular_template.cleanNote(ambiguous_tips)
		
		abstract_definition_text_set,abstract_definition_set = regular_template.main(abstract,query_word)
		abstract_definition_text = ' '.join(abstract_definition_text_set)

		title_note_definition_text_set,title_note_definition_set = regular_template.main(title_note,query_word)
		title_note_definition_text = ' '.join(title_note_definition_text_set)

		try:
			top_simi_words = [simi_word_tuple[0] for simi_word_tuple in word2vec_model.most_similar(positive=[query_word],topn=80)]
			for simi_word in top_simi_words:
				if len(simi_word)==1:
					continue
				if simi_word in alias_text or simi_word in abstract_definition_text or simi_word in ambiguous_tips or simi_word in title_note_definition_text or simi_word in title:
					if not text_process.isSubsetGeneral(query_word,simi_word):
						word_synonyms_set.add(simi_word)
			for pair in itertools.combinations(word_synonyms_set,2):
				new_word = ''.join(pair)
				if new_word not in  word_synonyms_set and (new_word in abstract_definition_text or new_word in title):
					word_synonyms_set.add(new_word)

			if len([word for word in word_synonyms_set if len(word)>0]) >= 2:
				outfile.write(query_word+'@'+','.join([word for word in word_synonyms_set if len(word)>0])+'\r\n')
		except:
			print 'not in vocabulary '+query_word


def main():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	
	word2vec_model = Word2Vec.load('../../data/word2vec.model')
	# for simi_word_tuple in word2vec_model.most_similar(positive=[u"传奇"],topn=80):
	# 	print simi_word_tuple[0]+" "+str(simi_word_tuple[1])
	readJson(word2vec_model)

if __name__ == '__main__':
	main()


