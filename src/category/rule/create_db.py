#encoding=utf-8
import sys
import re

def main():
	reload(sys)
	sys.setdefaultencoding('utf-8')

	outfile = open('partial.csv','wb')
	outfile.write("name,parent_name,weight\r\n")

	infile = open('rule_template/partial.rule','rb')
	for row in infile:
		row = row.strip().decode('utf-8')
		if row == "":
			continue
		if "<" in row and ">" in row:
			continue

		name = ""
		parent_name = ""
		weight = 1
		if ">>" in row:
			parent_name = row.split(">>")[0]
			name = row.split(">>")[1]
			weight = 1
			outfile.write(name+","+parent_name+","+str(weight)+"\r\n")
		if ">" in row and ">>" not in row:
			parent_name = row.split(">")[0]
			name = row.split(">")[1]
			weight = 1
			outfile.write(name+","+parent_name+","+str(weight)+"\r\n")
		if "~" in row:
			parent_name = row.split("~")[0]
			name = row.split("~")[1]
			weight = 2
			outfile.write(name+","+parent_name+","+str(weight)+"\r\n")
		




if __name__ == '__main__':
	main()

