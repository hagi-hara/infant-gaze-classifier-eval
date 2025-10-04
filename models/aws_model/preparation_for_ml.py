from module.rekognition import run_video_rekognition
from module.combine import combine_manual_coding
from module.summary import export_summary_pickle
import os
import argparse
import numpy as np

if __name__ == '__main__':

    # path base settings
    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dir', default='Lookit')
    args = parser.parse_args() 
    basepath = "result/" + args.dir + "/"
    os.makedirs(basepath, exist_ok=True)
    print("basepath:", basepath)

    # s3 settings: YOU NEED TO CHANGE
    bucket = 'box-data'
    predict = True

    # 1.get json output file from videos
    v_name_list = run_video_rekognition(bucket, basepath, 30)
    print(v_name_list)

    # 2.make pickle combined file for each video
    for v_name in v_name_list:
        combine_manual_coding(bucket, v_name, basepath, predict=predict)

    # 3.summarize all the pickle files
    export_summary_pickle(bucket, basepath, predict=predict)