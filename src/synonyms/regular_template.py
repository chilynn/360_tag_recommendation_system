#encoding=utf-8
import sys
sys.path.append("../common/")
import text_process
import file_utils
import json
import jieba
import jieba.posseg as pseg
import jieba.analyse
import re

definition_stopword = set([u"旧称",u"简称",u"古称",u"“",u"”",u"：",u":",u"《",u"》"])

#是 \u662f
#和 \u548c
#的 \u7684
#合 \u5408
#又 \u53c8
#简 \u7b80
#称 \u79f0
#叫 \u53eb
#为 \u4e3a
#等 \u7b49
#作 \u4f5c
#也 \u4e5f
#或 \u6216
#有 \u6709
#及 \u53ca
#之 \u4e4b
#名 \u540d
#亦 \u4ea6
#被 \u88ab
#指 \u6307
#对 \u5bf9
#者 \u8005
#呼 \u547c
#原 \u539f
#本 \u672c
#俗 \u4fd7
#旧 \u65e7
#泛 \u6cdb
#还 \u8fd8
#谐 \u8c10
#音 \u97f3
#艺 \u827a
#译 \u8bd1

#、 \u3001
#， \uff0c
#。 \u3002
#； \uff1b
#？ \uff1f
#！ \uff01
#“ \u201c
#” \u201d
#（ \uff08
#） \uff09
#《 \u300a
#》 \u300b
#中文范围 [\u4e00-\u9fa5]


def getRegularExpression():
	regular_set = set([])
	#并列成分
	#[^、，。；或和]{1,10}（[、；或和][^、，。；或等])+
	parallel_expression = ur"[^\u3001\uff0c\u3002\uff1b\u6216\u548c]{1,10}([\u3001\uff1b\u6216\u548c][^\u3001\uff0c\u3002\uff1b\u6216\u7b49]{1,10})*"
	#[原本]名xxx
	regular_set.add(ur"[\u539f\u672c]{1}\u540d[\u4e00-\u9fa5]{1,10}")
	#艺名xxx
	regular_set.add(ur"\u827a\u540d[\u4e00-\u9fa5]{1,6}")
	#音译为
	regular_set.add(ur"\u97f3\u8bd1\u4e3a[\u4e00-\u9fa5]{1,6}")
	#又名xxx
	regular_set.add(ur"\u53c8\u540d[^\u3001\u6216\uff1b\uff0c]{1,10}([\u3001\u6216 ][^\u3001\u6216\uff1b\uff0c\u3002\u7b49]{1,10})+")
	#俗称xxx
	regular_set.add(ur"\u4fd7\u79f0[^\u3001\u6216\uff1b\uff0c]{1,10}([\u3001\u6216 ][^\u3001\u6216\uff1b\uff0c\u3002\u7b49]{1,10})+")
	#旧称xxx
	regular_set.add(ur"\u65e7\u79f0[^\u3001\u6216\uff1b\uff0c]{1,10}([\u3001\u6216 ][^\u3001\u6216\uff1b\uff0c\u3002\u7b49]{1,10})+")
	# #B简称A
	# #需要细分
	# regular_set.add(ur"[^\uff0c\u3002\uff1b]{1,30}[\uff0c]{0,1}\u7b80\u79f0[^\uff0c\u3002]{0,10}")
	#,xxx的简称
	regular_set.add(ur"\uff0c.{1,10}\u7684\u7b80\u79f0")
	#xxx泛指yyy
	regular_set.add(ur"\u6cdb\u6307[\u4e00-\u9fa5]{1,4}")
	#[亦也又还][称叫][作为]
	regular_set.add(ur"[\u4ea6\u4e5f\u53c8\u8fd8]{1}[\u79f0\u53eb]{1}[\u4f5c]{0,1}"+parallel_expression)
	#对xxx的称呼
	regular_set.add(ur"\u5bf9"+parallel_expression+ur"\u7684\u79f0\u547c")
	#是xxx和yyy的合称
	regular_set.add(ur"\u662f.{1,10}\u548c.{1,10}\u7684\u5408\u79f0")
	#有xxx[和或及]之名
	regular_set.add(ur"\u6709.{1,10}[\u548c\u6216\u53ca]{0,1}.{0,10}\u4e4b\u540d")
	#“xxx”的谐音
	regular_set.add(ur"\u201c.{1,6}\u201d.*\u7684\u8c10\u97f3")
	#中出现的称号
	#tudo

	return regular_set

def cleanParallelNote(text):
	parallel_expression = ur"[^\u3001\uff0c\u3002\uff1b\u6216\u548c]{1,10}([\u3001\uff1b\u6216\u548c][^\u3001\uff0c\u3002\uff1b\u6216\u7b49]{1,10})*"
	pattern = re.compile(parallel_expression)
	match_obj = re.search(pattern,text)
	if match_obj:
		text = re.sub(ur'\uff08[^\uff08]+\uff09', "", text)
	return text

def regularMatch(text,regular_set,query):
	definition_text_set = set([])
	definition_set = set([])
	for pattern_expression in regular_set:		
		pattern = re.compile(pattern_expression)
		match_obj = re.search(pattern,text)
		if match_obj:
			match_text = match_obj.group()
			match_text = cleanParallelNote(match_text)
			definition_text_set.add(match_text)
			# if grabDefinitionWord(match_text) != None:
			# 	definition_set.add(grabDefinitionWord(match_text))
	return definition_text_set,definition_set

def grabDefinitionWord(text):
	pattern = re.compile(ur"\u201c[^\u201c]+\u201d")
	match_obj = re.search(pattern,text)
	if match_obj:
		return match_obj.group()
	else:
		return None

#判断是否是英文词组
def isEnglishPhrase(text):
	is_english_phrase = 0
	pattern = re.compile(ur"^[A-Za-z0-9 ]+$")
	match_obj = re.search(pattern,text)
	if match_obj and len(text.split())>=2:
		is_english_phrase = 1
	return is_english_phrase

def cleanNote(word):
	word = re.sub(ur"\uff08[^\uff08]+\uff09", "", word)
	word = re.sub(r"\([^(]+\)", "", word)
	word = re.sub(r"\[[0-9]\]", "", word)
	return word


def cleanDefinition(word):
	for stopword in definition_stopword:
		if stopword in word:
			word = word.replace(stopword,"")
	#去掉[num]
	word = re.sub(r"\[[0-9]\]", "", word)
	return word

def main(text,query=""):
	reload(sys)
	sys.setdefaultencoding('utf-8')

	# print repr(u"》")

	regular_set = getRegularExpression()
	return regularMatch(text,regular_set,query)
	

if __name__ == '__main__':
	text1 = u"动漫是动画和漫画的合称的缩写，取这两个词的第一个字合二为一称之为“动漫”，是中国（大陆）地区的特有的合成名词"
	text2 = u"酒店（又叫作宾馆、旅馆、旅店、旅社、商旅、客店、客栈。台湾作饭店，港澳、马来西亚、新加坡等作酒店）其基本定义是提供安全、舒适，令利用者得到短期的休息或睡眠的空间的商业机构。一般地说来就是给宾客提供歇宿和饮食的场所"
	text3 = u"美利坚合众国（United States of America），简称美国，是由华盛顿哥伦比亚特区、51个州、[1] 和关岛等众多海外领土组成的联邦共和立宪制国家"
	text4 = u"拖拉机是一种4人扑克牌游戏，可以选择一副牌、两副牌乃至四副牌进行。打一副牌时，也称为“ 升级”、“40 分” 或“ 打百分”；打两副牌时，也称为“80 分”，还有的地方也有叫“摔小二”、“双升”、“双扣”等。和“升级”一样，牌局采用四人结对竞赛，抢分升级的方式进行。"
	text5 = u"又称为摄影、照相，一般指通过物体所反射的光线使感光介质曝光的过程，通常使用机械照相机或者数码照相机。"
	text6 = u"包拯廉洁公正、立朝刚毅，不附权贵，铁面无私，且英明决断，敢于替百姓申不平，故有“包青天”及“包公”之名，京师有“关节不到，有阎罗包老”之语。后世将他奉为神明崇拜，认为他是文曲星转世，由于民间传其黑面形象，亦被称为“包青天”、“包黑炭”。"
	text7 = u"旅行，指远行；去外地办事或游览。"
	text8 = u"台球也叫桌球（港澳的叫法）、撞球（台湾的叫法）。最初台球是用木料制成的，之后出现了象牙制造的。"
	text9 = u"慨况一，周边通常指旁边的某物。慨况二，国内习惯用周边产品来定义动漫相关产品。而在国外，这类商品被统称为HOBBY（业余爱好，嗜好），有硬周边（CORE HOBBY）与软周边（LIGHT HOBBY）的区分。像扭蛋、挂卡、模型、手办这样没有多少实用价值纯观赏收藏的被称为硬周边，相对价格较高；另外我们常见的借用某个动漫形象生产的具有一定实用性的如文具、服饰、钥扣、手机链等商品被称为软周边，相对价格便宜。"
	text10 = u"幼儿园，旧称蒙养园、幼稚园，为一种学前教育机构，用于对幼儿集中进行保育和教育，通常接纳三至六周岁的幼儿。"
	text11 = u"人物、情节、环境是小说的三要素。情节一般包括开端、发展、高潮、结局四部分，有的包括序幕、尾声。环境包括自然环境和社会环境。 小说按照篇幅及容量可分为长篇、中篇、短篇和微型小说（小小说）。按照表现的内容可分为科幻、公案、传奇、武侠、言情、同人、官宦等。按照体制可分为章回体小说、日记体小说、书信体小说、自传体小说。按照语言形式可分为文言小说和白话小说。"
	text12 = u"地球（英语：Earth）是太阳系八大行星之一（2006年冥王星被划为矮行星，因为其运动轨迹与其它八大行星不同），按离太阳由近及远的次序排为第三颗。它有一个天然卫星——月球，二者组成一个天体系统——地月系统。地球作为一个行星，远在46亿年以前起源于原始太阳星云。地球会与外层空间的其他天体相互作用，包括太阳和月球。地球是上百万生物的家园，包括人类，地球是目前宇宙中已知存在生命的唯一天体。地球赤道半径6378.137千米，极半径6356.752千米，平均半径约6371千米，赤道周长大约为40076千米，地球上71%为海洋，29%为陆地，所以太空上看地球呈蓝色。地球是目前发现的星球中人类生存的唯一星球。"
	text13 = u"宝宝（对婴儿或者小孩的称呼）"
	text14 = u"从人机交互角度看：界面是人与机器（计算机）之间传递和交换信息的媒介，是用户和系统进行双向信息交互的支持软件、硬件以及方法的集合。常用缩写词为UI（User Interface）即用户界面，也称人机界面（Human-Computer Interface，简称HCI）。"
	text15 = u"Android是一种基于Linux的自由及开放源代码的操作系统，主要使用于移动设备，如智能手机和平板电脑，由Google公司和开放手机联盟领导及开发。尚未有统一中文名称，中国大陆地区较多人使用“安卓”或“安致”。Android操作系统最初由Andy Rubin开发，主要支持手机。2005年8月由Google收购注资。2007年11月，Google与84家硬件制造商、软件开发商及电信营运商组建开放手机联盟共同研发改良Android系统。随后Google以Apache开源许可证的授权方式，发布了Android的源代码。第一部Android智能手机发布于2008年10月。Android逐渐扩展到平板电脑及其他领域上，如电视、数码相机、游戏机等。2011年第一季度，Android在全球的市场份额首次超过塞班系统，跃居全球第一。 2013年的第四季度，Android平台手机的全球市场份额已经达到78.1%。[1] 2013年09月24日谷歌开发的操作系统Android在迎来了5岁生日，全世界采用这款系统的设备数量已经达到10亿台。"
	text16 = u"水果是指多汁且大多数有甜味可直接生吃的植物果实，"
	text17 = u"红薯（英文： sweet potato）原名番薯（学名：Ipomoea batatas （L.） Lam.），又名红芋、甘薯、蕃薯、肥大米（广东）、山药（河北）、番芋、地瓜（北方）、红苕、线苕、白薯、金薯、甜薯、朱薯、枕薯、番葛、白芋、茴芋 地瓜等。北方俗称地瓜、山芋。明代李时珍《本草纲目》记有“甘薯补虚，健脾开胃，强肾阴”，并说海中之人食之长寿。中医视红薯为良药。"
	text18 = u"银行是依法成立的经营货币信贷业务的金融机构。银行是商品货币经济发展到一定阶段的产物。银行[1] 是金融机构之一，银行按类型分为：中央银行，商业银行，投资银行，政策性银行，世界银行 它们的职责各不相同。中央银行：“中国人民银行”是我国的中央银行。商业银行：就是所谓我们常指的银行是属于商业银行，有工商银行，农业银行，建设银行，中国银行，交通银行，招商银行，邮储银行，兴业银行等等。投资银行：简称投行，比如国际实力较大有：高盛集团 摩根斯坦利 摩根大通 法国兴业银行等等 。政策性银行：中国进出口银行、中国农业发展银行、国家开发银行。世界银行：资助国家克服穷困，各机构在减轻贫困和提高生活水平的使命中发挥独特的作用。"
	text19 = u"武器，又称为兵器，是用于攻击的工具，也因此被用来威慑和防御。当武器被有效利用时，它应遵循期望效果最大化、附带伤害最小化的原则。任何可造成伤害的事物（甚至可造成心理伤害的）都可称为武器。只要用于攻击，武器可以是一根简单的木棒，也可是一枚核弹头。随着新军事变革深入发展，推进军事转型，构建信息化军队，打赢信息化战争，已经成为世界各国发展武器装备的目标牵引。军事大国正加紧调整军事战略，以信息技术推动信息化武器装备的发展。"
	text20 = u"对婴儿或者小孩的简称"
	text21 = u"包含是集合与集合之间的关系，也叫子集关系。基本含义近同于蕴含、蕴涵、包涵，关系形容词。"
	text22 = u"妹纸：源自湖南、河南、四川话“妹子”的谐音。从2011年初1月左右开始出现并在网络流行。"
	text23 = u"“灰机”是飞机的一种非正规的网络现实的谐音词。把说成“灰机”，是一种飞机的诙谐说法，逐渐成为网络流行语之一。"
	text24 = u".一种网络流行语言。“什么”的谐音，意同“什么”。2011年最流行的一句话：神马都是浮云。"
	text25 = u"2014年3月27日晚间，在中国微博领域一枝独秀的新浪微博宣布改名为“微博”，并推出了新的LOGO标识，新浪色彩逐步淡化。"
	text26 = u"微博（Weibo），微型博客（MicroBlog）的简称，即一句话博客，是一种通过关注机制分享简短实时信息的广播式的社交网络平台。"
	text27 = u"台球也叫桌球（港澳的叫法）、撞球（台湾的叫法）。最初台球是用木料制成的，之后出现了象牙制造的。"
	text = u"桌面（英文：Desktop），是计算机用语。桌面是打开计算机并登录到Windows之后看到的主屏幕区域。就像实际的桌面一样，它是用户工作的平面。打开程序或文件夹时，它们便会出现在桌面上。"

	print cleanNote(u"sfsd sdf（ss）")
	# main(text27)


