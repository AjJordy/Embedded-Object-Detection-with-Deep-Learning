import json
import os
import yaml

img_file = 'D:\\Humanoid\\squeezeDet\\squeezeDet-master\\data\\val\\images.txt'
gt_dir = 'D:\\Humanoid\\squeezeDet\\squeezeDet-master\\data\\val\\12.txt'
base = 'D:\\Humanoid\\squeezeDet\\squeezeDet-master\\data\\val\\image_2\\'

# 5,6,7,25,36,168

with open(img_file) as imgs:
	img_names = imgs.read().splitlines()
imgs.close()

with open(gt_dir) as g:
	data = yaml.load(g)
g.close()
print("yaml read")

annotations = {}

for img_file in img_names:	
	annotations[img_file] = []
	try: 	
		for img in data['imageset']:
			# dir = base + img
			dir = base + img[:-4] + '.jpg'
			# print("dir ",dir)
			# print("img ",img_file)
			if img_file == dir:
				print(img_file)
				for ann in data['imageset'][img]['annotations']:
					if ann['label'] == 'ball' and ann['present'] == True:
						print(img_file)
						x = ann['center'][0]
						y = ann['center'][1]
						w = ann['dimensions'][0]
						h = ann['dimensions'][1]
						class_name = ann['label']
						annotations[img_file].append([x, y, w, h, class_name])

		if len(annotations[img_file]) == 0:
			print("del ",img_file)
			os.remove(img_file)
			del annotations[img_file]

	except:				
		print("except ",img_file)
		os.remove(img_file)

print("cabou")

with open('val.json', 'w') as outfile:
	json.dump(annotations, outfile)
outfile.close()