import json
import os
import re

# img_file = 'D:\\Humanoid\\squeezeDet\\Embedded_Object_Detection\\imagetagger\\train_jpg.txt'
# gt_dir = 'D:\\Humanoid\\squeezeDet\\Embedded_Object_Detection\\imagetagger\\train_jpg.json'
# path = 'D:\\Humanoid\\squeezeDet\\Embedded_Object_Detection\\imagetagger\\training\\label_2\\'

img_file = 'D:\\Humanoid\\squeezeDet\\squeezeDet-master\\data\\val\\images.txt'
gt_dir = 'D:\\Humanoid\\squeezeDet\\squeezeDet-master\\data\\val\\val.json'
path = 'D:\\Humanoid\\squeezeDet\\squeezeDet-master\\data\\val\\label_2\\'


with open(img_file,'r') as imgs:
    img_names = imgs.read().splitlines()
imgs.close()

with open(gt_dir,'r') as f:
    data = json.load(f)
f.close()

for img_name in img_names:  
    # txt = path + img_name[-16:-4] + ".txt"  
    txt = path +  re.search(r'image_2\\(.*).jpg', img_name).group(1) + '.txt'
    f = open(txt,"w+")     
    for ann in data[img_name]:
        cx, cy, w, h, cls = ann[:]
        xmin = cx - w/2
        ymin = cy - h/2
        xmax = cx + w/2
        ymax = cy + h/2    
        f.write(cls + " " + str(xmin) + " " + str(ymin)+ " " + str(xmax)+ " " + str(ymax) + "\n")
    f.close()

print("Acabou!")
