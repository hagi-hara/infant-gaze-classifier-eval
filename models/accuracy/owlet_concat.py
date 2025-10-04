import pandas as pd
import numpy as np
import argparse
import os

parser = argparse.ArgumentParser(description="指定ディレクトリ内の動画のicatcher+とffprobeとELANの結果を統合して、csvファイルに出力します。")

parser.add_argument('-d','--dir', default='Public')
args = parser.parse_args() 

# input = "icatcher&ELAN/"
input = "../unblinded/"
output = "icatcher&owlet&ELAN/"
dir = args.dir + "/"
indir = input + dir
outdir = output + dir
os.makedirs(outdir, exist_ok=True)

files = os.listdir(indir)
for file in files:
    if file == "38.csv":
        continue
    df = pd.read_csv(indir + file)
    owl = pd.read_csv("owlet/" + dir + "final_csv/" + file)

    # dropna = ref.dropna()
    # df = dropna.reset_index(drop=True)

    # owl.loc[(owl['new_Tag'] == 'looking') & (owl['X-coord'] < 0.5), 'new_Tag'] = 'right'
    # owl.loc[(owl['new_Tag'] == 'looking') & (owl['X-coord'] > 0.5), 'new_Tag'] = 'left'
    u = owl['new_Tag'].unique()
    print(u)

    Tag = owl["new_Tag"]
    Time = owl["Time"]
    X = owl['X-coord']
    Y = owl['Y-coord']
    df["owlet_annotation"] = "nan"

    for i, pts in enumerate(df["pts_time"]):
        pts = pts*1000
        diff_t = list(map(lambda x: x-pts, Time))
        min_t = min(diff_t, key=abs)
        t_point = diff_t.index(min_t)
        df.loc[i, "owlet_annotation"] = Tag[t_point]
        df.loc[i, "owlet_x_cor"] = X[t_point]
        df.loc[i, "owlet_y_cor"] = Y[t_point]

    df.to_csv(outdir + file, index=False)

