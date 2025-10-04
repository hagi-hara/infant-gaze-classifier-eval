import pandas as pd
import numpy as np
import argparse
import os

parser = argparse.ArgumentParser(description="指定ディレクトリ内の動画のicatcher+とffprobeとELANの結果を統合して、csvファイルに出力します。")

parser.add_argument('-d','--dir', default='Public')
args = parser.parse_args() 

input = "icatcher&owlet&ELAN/"
output = "icatcher&owlet&ar&ELAN/"
dir = args.dir + "/"
indir = input + dir
outdir = output + dir
os.makedirs(outdir, exist_ok=True)

files = os.listdir(indir)
for file in files:
    print(file)
    # if file == "37.csv":
    #     print("no")
    #     continue
    ref = pd.read_csv(indir + file)
    ar = pd.read_csv("ar/" + dir + file)

    # dropna = ref.dropna()
    # df = dropna.reset_index(drop=True)
    df = ref
    ar.replace({'prediction': {"noface": "away"}}, inplace=True)

    Tag = ar["prediction"]
    Time = ar["timestamp"]
    df["ar_annotation"] = "nan"

    for i, pts in enumerate(df["pts_time"]):
        pts = pts*1000
        diff_t = list(map(lambda x: x-pts, Time))
        min_t = min(diff_t, key=abs)
        t_point = diff_t.index(min_t)
        df.loc[i, "ar_annotation"] = Tag[t_point]

    df.to_csv(outdir + file, index=False)
