import pandas as pd
import numpy as np
import argparse
import os

parser = argparse.ArgumentParser(description="指定ディレクトリ内の動画のicatcher+とffprobeとELANの結果を統合して、csvファイルに出力します。")

parser.add_argument('-d','--dir', default='Public')
args = parser.parse_args() 

twindow = 0.05 
name_list = ["icatcher", "owlet", "ar", "icatcher2", "owlet2", "ar2"]
name_len = len(name_list)

folder = "annotation2frame/OutputData/frame2time/" + args.dir + "/"

ans_df = []
all_concat = []
files = os.listdir(folder)

acc_dir = "acc_result/" + args.dir + "/"
print(acc_dir)
os.makedirs(acc_dir, exist_ok=True)

for file in files:
    print(file)
    MT_flag_list = []
    HK_flag_list = []

    nan = pd.read_csv(folder + file)
    
    have_onset=nan[~nan['onset'].isnull()]
    no_onset=nan[nan['onset'].isnull()]
 
    # print(dropna)
    dropna = have_onset[(have_onset['MT'] != 'unsure') & (have_onset['HK'] != 'unsure')]
    unsure = have_onset[(have_onset['MT'] == 'unsure') | (have_onset['HK'] == 'unsure')]
    df = dropna.reset_index()

    MT = df["MT"]
    HK = df["HK"]
    onset = df["onset"]
    dur_time = df["duration_time"]

    length = len(dur_time)
    ans_list_HK = 0
    ans_list_MT = 0
    ans_len = 0

    path = acc_dir + file

    for ind in range(length):
        min_i = ind-1
        max_i = ind+1
        down_win_s = 0
        up_win_s = 0
        now_o = onset[ind]
        ans_len += 1

        while down_win_s < twindow:
            if min_i < 0:
                break
            if onset[min_i] != onset[ind]:
                break
            down_win_s += dur_time[min_i]
            min_i -= 1
        
        while up_win_s < twindow:
            if max_i > length-1:
                break
            if onset[max_i] != onset[ind]:
                break
            up_win_s += dur_time[max_i]
            max_i += 1

        # some human annotations - one prediction (human)
        target = HK[ind]
        MT_flag = 0
        for j in range(min_i+1, max_i):
            if MT[j] == target:
                ans_list_MT += 1
                MT_flag = 1
                break
        MT_flag_list.append(MT_flag)


        # one human annotations - some prediction (predict)
        target = HK[ind]
        MT_flag = 0
        for j in range(min_i+1, max_i):
            if MT[j] == target:
                ans_list_HK += 1
                MT_flag = 1
                break
        HK_flag_list.append(MT_flag)        

        if ind == length-1 or now_o != onset[ind+1]:
            ans_df.append({"folder": args.dir, "filename":file,"trial":now_o,
                            "HK__as_ref":ans_list_HK/ans_len,
                            "MT_as_ref":ans_list_MT/ans_len,
                            "mean":(ans_list_HK+ans_list_MT)/ans_len/2})
            ans_list_HK = 0
            ans_list_MT = 0
            ans_len = 0
        
    df["MT_as_ref"] = MT_flag_list
    df["HK_as_ref"] = MT_flag_list
    df = df.set_index('index')
    df = pd.concat([df, no_onset, unsure])
    df = df.sort_index()
    df = df.fillna('NA')

    df.to_csv(acc_dir + file, index=False)
    all_concat.append(df)

#     break
# break
final_ans = pd.DataFrame.from_dict(ans_df)
final_ans.to_csv("final_ans.csv", index=False)

all_df = pd.concat(all_concat)
all_df.to_csv("all_concat.csv", index=False)