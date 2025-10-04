import pandas as pd
import numpy as np
import argparse
import os

parser = argparse.ArgumentParser(description="指定ディレクトリ内の動画のicatcher+とffprobeとELANの結果を統合して、csvファイルに出力します。")

parser.add_argument('-d','--dir', default='Public')
args = parser.parse_args() 

input = "all_concat_raw_data/"
folders = os.listdir(input)
dir = args.dir + "/"
indir = input + dir

twindow = 0.05 
name_list = ["icatcher", "owlet", "ar", "icatcher2", "owlet2", "ar2"]
name_len = len(name_list)

cols = ["folder","filename","frame","pts_time","duration_time","onset","human_annotation","human2_annotation",
"icatcher_annotation","icatcher_human_as_ref","icatcher_pred_as_ref",
"icatcher2_annotation","icatcher2_human_as_ref","icatcher2_pred_as_ref","icatcher_confidence",
"owlet_annotation","owlet_human_as_ref","owlet_pred_as_ref",
"owlet2_annotation","owlet2_human_as_ref","owlet2_pred_as_ref","owlet_x_cor","owlet_y_cor",
"ar_annotation","ar_human_as_ref","ar_pred_as_ref",
"ar2_annotation","ar2_human_as_ref","ar2_pred_as_ref",
"response_uuid","child_hashed_id","trial","videoName","videoStarted","trialCompleted","objectMovement",
"objectNumber","complexity","shape","leftSide","rightSide","sound","phase"]
ans_df = []
all_concat = pd.DataFrame(columns=cols)
for folder in folders:

    print(folder)
    indir = input + folder + "/"
    files = os.listdir(indir)

    acc_dir = "acc_result/" + folder + "/"
    print(acc_dir)
    os.makedirs(acc_dir, exist_ok=True)

    for file in files:
        print(file)
        human_flag_list = [[] for i in range(name_len)]
        predict_flag_list = [[] for i in range(name_len)]

        nan = pd.read_csv(indir + file)
        
        have_onset=nan[~nan['onset'].isnull()]
        no_onset=nan[nan['onset'].isnull()]
        
        # print(dropna)
        dropna = have_onset[(have_onset['human_annotation'] != 'unsure')]
        unsure = have_onset[(have_onset['human_annotation'] == 'unsure')]
        df = dropna.reset_index()

        human = df["human_annotation"]
        icatcher = df["icatcher_annotation"]
        owlet = df["owlet_annotation"]
        ar = df["ar_annotation"]
        human2 = df["human2_annotation"]
        icatcher2 = df["icatcher2_annotation"]
        owlet2 = df["owlet2_annotation"]
        ar2 = df["ar2_annotation"]
        dur_time = df["duration_time"]
        onset = df["onset"]

        length = len(dur_time)
        ans_list_human = np.zeros(name_len)
        ans_list_predict = np.zeros(name_len)
        ans_len = 0

        # these preprocess may change (not common settings)
        icatcher.replace(" ", "", inplace=True)
        icatcher.replace({" left": "left"}, inplace=True)
        icatcher.replace({" right": "right"}, inplace=True)
        icatcher.replace({" noface": "away"}, inplace=True)
        icatcher.replace({" away": "away"}, inplace=True)

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
            target_list = [icatcher[ind],owlet[ind],ar[ind]]
            for ti, target in enumerate(target_list):
                human_flag = 0
                for j in range(min_i+1, max_i):
                    if human[j] == target:
                        ans_list_human[ti] += 1
                        human_flag = 1
                        break
                human_flag_list[ti].append(human_flag)


            # one human annotations - some prediction (predict)
            target = human[ind]
            predict_list = [icatcher, owlet, ar]
            for ti, predict in enumerate(predict_list):
                predict_flag = 0
                for j in range(min_i+1, max_i):
                    if predict[j] == target:
                        ans_list_predict[ti] += 1
                        predict_flag = 1
                        break
                predict_flag_list[ti].append(predict_flag)
            
            # some human annotations - one prediction (human)
            target_list = [icatcher2[ind],owlet2[ind],ar2[ind]]
            for ti, target in enumerate(target_list):
                human_flag = 0
                for j in range(min_i+1, max_i):
                    if human2[j] == target:
                        ans_list_human[ti+3] += 1
                        human_flag = 1
                        break
                human_flag_list[ti+3].append(human_flag)


            # one human annotations - some prediction (predict)
            target = human2[ind]
            predict_list = [icatcher2, owlet2, ar2]
            for ti, predict in enumerate(predict_list):
                predict_flag = 0
                for j in range(min_i+1, max_i):
                    if predict[j] == target:
                        ans_list_predict[ti+3] += 1
                        predict_flag = 1
                        break
                predict_flag_list[ti+3].append(predict_flag)

            if ind == length-1 or now_o != onset[ind+1]:
                noise_col = ["response_uuid","child_hashed_id","videoName","videoStarted","trialCompleted","objectMovement","objectNumber","complexity","shape","leftSide","rightSide","sound","phase"]
                noise = df.loc[ind, noise_col]
                noise_df = dict(zip(noise_col, noise))
                for i in range(name_len):
                    ans_df.append({"folder": folder, "filename":file,"trial":now_o,
                                    "predictor": name_list[i],
                                    "pred_as_ref":ans_list_human[i]/ans_len,
                                    "human_as_ref":ans_list_predict[i]/ans_len,
                                    "mean":(ans_list_predict+ans_list_human)[i]/ans_len/2}
                                    | noise_df)
                ans_list_human = np.zeros(name_len) 
                ans_list_predict = np.zeros(name_len) 
                ans_len = 0
            
        for i in range(name_len):
            name = name_list[i]
            # print(length)
            # print(len(predict_flag_list[0]))
            df[name + "_human_as_ref"] = predict_flag_list[i]
            df[name + "_pred_as_ref"] = human_flag_list[i]
        
        df = df.set_index('index')
        df = pd.concat([df, no_onset, unsure])
        df = df.sort_index()
        df = df.reindex(columns=cols)
        df = df.fillna('NA')
        assert(len(nan) == len(df))

        df.to_csv(acc_dir + file, index=False)
        all_concat = pd.concat([all_concat, df])

    #     break
    # break

final_ans = pd.DataFrame.from_dict(ans_df)
final_ans.to_csv("final_ans.csv", index=False)
all_concat.to_csv("all_concat.csv", index=False)