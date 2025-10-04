# Many Babies -AWS Video-
## Introduction & Explanation
This program makes it possible to recognize which direction babies are gazing. 

## Preparation
Prepare videos in which you want to know the gaze directions.
Codes are written in Python so you need a Python environment.  
AWS (Amazon Rekognition) is used to detect faces, so you need an AWS IAM account.  
You need to create your environment using Anaconda with environment.yml. 
If you want to use the codes in your environment, you have to modify some path settings in the codes.

## Usage
At first, upload videos on your s3. Videos have to be inside a folder, and this folder is directly under one bucket.After this procedure, s3 file structure is like below.

### AWS structure
<pre>
bucket
└── folder
    ├── video1
    ├── video2
    ├── ...
    └── videoN
</pre>

Then, modify bucket name in "preparation_for_ml.py". And run the code below in local.
```
python3 preparation_for_ml.py -d Foldername
```
After that, run the code below for prediction.
```
python3 ml_prediction.py -d Foldername
```
You will get prediction result in "ar" folder.

## File Structure
<pre>
aws_video_updated
├── preparation_for_ml.py -(preprocess for ml)
├── ml_prediction.py -(for prediction)
├── module
│   ├── utils
│   ├── rekognition.py
│   ├── combine.py
│   ├── summary.py
│   └── ml.py
├── ar -(prediction results will be here)
│   └── folder
├── ml_w_pickels.py -(for training)
└── model.sav -(model for prediction)
</pre>

## Retraining
First, you need Lookit annotation files. And upload them to the same bucket as videos. 
You need to modify some codes.
1. preparation_for_ml.py
Change the value of variable "predict" from  True to False.
2. module/utils/infant_face_match_video_and_behav_s3.py
Change variables or add some codes to make resp['matches'] bocomes your annotation path.

And run the code below in local.
```
python3 preparation_for_ml.py -d Foldername
```
You will get summary file in "summary" folder.
And run the code below to start training.
```
python3 ml_w_pickles.py
```
