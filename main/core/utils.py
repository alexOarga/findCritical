f = open("/home/alex/PycharmProjects/tfg/models/test_models/mabs.xml","r")
f1 = f.readlines()

keyword_start = "id=\""
keyword_end = "\""

for line in f1:
	if keyword_start in line:
		left, rid = line.split(keyword_start, 1)
		cut_id, left = rid.split(keyword_end, 1)
		if len(cut_id) > 255:
			print("		-> ", "(",len(cut_id), ")" ,cut_id)
			print("		---> ", cut_id[0:200])
			print()  
	