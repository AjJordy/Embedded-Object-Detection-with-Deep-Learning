## SqueezeDet

This repository contains a tensorflow implementation of SqueezeDet, a convolutional neural network based object detector described in this paper: https://arxiv.org/abs/1612.01051. If you find this work useful for your research, please consider citing:

    @inproceedings{squeezedet,
        Author = {Bichen Wu and Forrest Iandola and Peter H. Jin and Kurt Keutzer},
        Title = {SqueezeDet: Unified, Small, Low Power Fully Convolutional Neural Networks for Real-Time Object Detection for Autonomous Driving},
        Journal = {arXiv:1612.01051},
        Year = {2016}
    }
    
## Installation:

The following instructions are written for Linux-based distros.

Let's call the top level directory of SqueezeDet `$SQDT_ROOT`. 
    
- Use pip to install required Python packages:
    
    ```Shell
    pip install -r requirements.txt
    ```
## Demo:
- Download SqueezeDet model parameters from [here](https://www.dropbox.com/s/a6t3er8f03gdl4z/model_checkpoints.tgz?dl=0), untar it, and put it under `$SQDT_ROOT/data/` If you are using command line, type:

  ```Shell
  cd $SQDT_ROOT/data/
  wget https://www.dropbox.com/s/a6t3er8f03gdl4z/model_checkpoints.tgz
  tar -xzvf model_checkpoints.tgz
  rm model_checkpoints.tgz
  ```

- Now we can run the demo. To detect the sample image `$SQDT_ROOT/data/sample.png`,

  ```Shell
  cd $SQDT_ROOT/
  python ./src/demo.py
  ```
  If the installation is correct, the detector should generate this image: ![alt text](https://github.com/BichenWuUCB/squeezeDet/blob/master/README/out_sample.png)

  To detect other image(s), use the flag `--input_path=./data/*.png` to point to input image(s). Input image(s) will be scaled to the resolution of 1242x375 (KITTI image resolution), so it works best when original resolution is close to that.  

- SqueezeDet is a real-time object detector, which can be used to detect videos. The video demo will be released later.

## Training/Validation:
- Download KITTI object detection dataset: [images](http://www.cvlibs.net/download.php?file=data_object_image_2.zip) and [labels](http://www.cvlibs.net/download.php?file=data_object_label_2.zip). Put them under `$SQDT_ROOT/data/KITTI/`. Unzip them, then you will get two directories:  `$SQDT_ROOT/data/KITTI/training/` and `$SQDT_ROOT/data/KITTI/testing/`. 

- Now we need to split the training data into a training set and a vlidation set. 

  ```Shell
  cd $SQDT_ROOT/data/KITTI/
  mkdir ImageSets
  cd ./ImageSets
  ls ../training/image_2/ | grep ".png" | sed s/.png// > trainval.txt
  ```
  `trainval.txt` contains indices to all the images in the training data. In our experiments, we randomly split half of indices in `trainval.txt` into `train.txt` to form a training set and rest of them into `val.txt` to form a validation set. For your convenience, we provide a script to split the train-val set automatically. Simply run
  
    ```Shell
  cd $SQDT_ROOT/data/
  python random_split_train_val.py
  ```
  
  then you should get the `train.txt` and `val.txt` under `$SQDT_ROOT/data/KITTI/ImageSets`. 

  When above two steps are finished, the structure of `$SQDT_ROOT/data/KITTI/` should at least contain:

  ```Shell
  $SQDT_ROOT/data/KITTI/
                    |->training/
                    |     |-> image_2/00****.png
                    |     L-> label_2/00****.txt
                    |->testing/
                    |     L-> image_2/00****.png
                    L->ImageSets/
                          |-> trainval.txt
                          |-> train.txt
                          L-> val.txt
  ```

- Next, download the CNN model pretrained for ImageNet classification:
  ```Shell
  cd $SQDT_ROOT/data/
  # SqueezeNet
  wget https://www.dropbox.com/s/fzvtkc42hu3xw47/SqueezeNet.tgz
  tar -xzvf SqueezeNet.tgz
  

- Finally, to monitor training and evaluation process, you can use tensorboard by

  ```Shell
  tensorboard --logdir=$LOG_DIR
  ```
  Here, `$LOG_DIR` is the directory where your training and evaluation threads dump log events, which should be the same as `-train_dir` and `-eval_dir` specified in `train.sh` and `eval.sh`. From tensorboard, you should be able to see a lot of information including loss, average precision, error analysis, example detections, model visualization, etc.

  ![alt text](https://github.com/BichenWuUCB/squeezeDet/blob/master/README/detection_analysis.png)
  ![alt text](https://github.com/BichenWuUCB/squeezeDet/blob/master/README/graph.png)
  ![alt text](https://github.com/BichenWuUCB/squeezeDet/blob/master/README/det_img.png)
