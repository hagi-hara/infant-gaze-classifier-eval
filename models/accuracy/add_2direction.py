import pandas as pd
import numpy as np
import argparse
import os

parser = argparse.ArgumentParser(description="指定ディレクトリ内の動画のicatcher+とffprobeとELANの結果を統合して、csvファイルに出力します。")

parser.add_argument('-d','--dir', default='Public')
args = parser.parse_args() 

input = "icatcher&owlet&ar&ELAN/"
output = "all_concat_raw_data/"
dirs = os.listdir(input)
for dir in dirs:
    dir = dir + "/"
    indir = input + dir
    outdir = output + dir
    os.makedirs(outdir, exist_ok=True)

    files = os.listdir(indir)
    for file in files:
        df = pd.read_csv(indir + file)

        df.replace({'icatcher_annotation': {"noface": "away"}}, inplace=True)
        df.replace({" left": "left"}, inplace=True)
        df.replace({" right": "right"}, inplace=True)
        df.replace({" noface": "away"}, inplace=True)
        df.replace({" away": "away"}, inplace=True)
        df = df.assign(
                   human2_annotation=df["human_annotation"],
                   icatcher2_annotation=df["icatcher_annotation"],
                   owlet2_annotation=df["owlet_annotation"],
                   ar2_annotation=df["ar_annotation"])
        df.replace({'icatcher2_annotation': {"left": "looking", "right": "looking"},
                   'owlet2_annotation': {"left": "looking", "right": "looking"},
                   'ar2_annotation': {"left": "looking", "right": "looking"},
                   'human2_annotation': {"left": "looking", "right": "looking", "center": "looking"}},
                   inplace=True)
        
        df.to_csv(outdir + file, index=False)
