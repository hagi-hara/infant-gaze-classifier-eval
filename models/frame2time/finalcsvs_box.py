import os
import pandas as pd
import statistics
import glob
import csv
import argparse
import math

parser = argparse.ArgumentParser(description="指定ディレクトリ内の動画のicatcher+とffprobeとELANの結果を統合して、csvファイルに出力します。")

parser.add_argument('-d','--dir', default='Public')
args = parser.parse_args() 

homeDir = "/mnt/c/Users/intern_mbah/"
icatcherDir = homeDir + "OutputData/icatcher_new/" + args.dir + "/annotation"
icatcherfiles = os.listdir(icatcherDir) 
ffprobeDir = homeDir + "OutputData/ffprobe/" + args.dir
# ELANDir = homeDir + "OutputData/ELAN/" + args.dir #ELANのannotationのみの結果のcsvが、このディレクトリの下に「動画名.csv」として入っていることを想定
ELANDir = homeDir + "OutputData/ELAN/final_code_guide"

outDir = homeDir + "OutputData/frame2time/" + args.dir + "/icatcher_ffprobe_ELAN/onset"
os.makedirs(outDir, exist_ok=True)

df = pd.read_csv("result.csv")
correspond = df #[df["folder"] == args.dir+"/"]

for icatcherfile in icatcherfiles:
    csvname = icatcherfile.replace('.txt', '.csv')

    id = icatcherfile.split(".")[0]
    filename = correspond[correspond["id"] == int(id)]["filename"].iloc[-1]
    ELANcsvname = filename + "_code_guide_final.csv"
    print(ELANcsvname, id)

    if os.path.exists(os.path.join(ffprobeDir, csvname)) & os.path.exists(os.path.join(ELANDir, ELANcsvname)):
        annotationfile = os.path.join(icatcherDir, icatcherfile)
        ffprobefile = os.path.join(ffprobeDir, csvname)
        ELANfile = os.path.join(ELANDir, ELANcsvname)

        icatcherDf = pd.read_csv(annotationfile, names=["frame", "annotation", "confidence"])

        ffprobeDf = pd.read_csv(ffprobefile)
        frameNumber = len(ffprobeDf)
        newffprobeDf = ffprobeDf[4:(frameNumber-4)]
        newffprobeDf = newffprobeDf.reset_index(drop=True)

        onsetDf = pd.read_csv(ELANfile)
        onsetDf = onsetDf.sort_values("videoStarted") #時間が昇順になるように並び替える

        df = pd.DataFrame()

        #pkt_durationの情報が明らかに間違っているケースが見られたため、pkt_durationが検出された場合であってもpts_durationを採用するようにした
        #if math.isnan(newffprobeDf['pkt_duration_time'][0]):
        df = pd.concat([icatcherDf["frame"], newffprobeDf["pts_time"], newffprobeDf["pts_duration_time"], icatcherDf["annotation"], icatcherDf["confidence"]],axis=1)
        df = df.rename(columns={'pts_duration_time': 'duration_time'})
        #else:
        #    df = pd.concat([icatcherDf["frame"], newffprobeDf["pts_time"], newffprobeDf["pkt_duration_time"], icatcherDf["annotation"], icatcherDf["confidence"]],axis=1)
        #    df = df.rename(columns={'pkt_duration_time': 'duration_time'})
        df = df.rename(columns={'annotation': 'icatcher_annotation'})
        df = df.rename(columns={'confidence': 'icatcher_confidence'})

        onset = ["NA"]*len(df) #dfと同じ長さの空のリストを作る
        print(type(onset[2]))
        pts = list(df["pts_time"]) #ptstimeをリスト化

        previous_start_point = 0
        previous_end_point = 0

        for row in onsetDf.itertuples():
            start = row[1]
            end = row[2] #中身は１つの値
            annotation = row[3]

            #ptstimeの全要素とstartの差分を取り、最も小さい地点をhumannanotationの開始点とする
            diff_start = list(map(lambda x: x-start, pts))
            min_start = min(diff_start, key=abs)
            start_point = diff_start.index(min_start)

            #endでも同様のことを行い、終了点を決める
            diff_end = list(map(lambda x: x-end, pts))
            min_end = min(diff_end, key=abs)
            end_point = diff_end.index(min_end)

            if previous_end_point >= start_point :
                start_point = previous_end_point + 1 #前のtrial, attentionなどの情報が入っていた場合は、次の情報で上書きしないようにしたい
            
            #その間は全部同じタグにする
            onset[start_point:end_point+1] = [annotation]*(end_point - start_point + 1) #+1最初はなかったけどやっぱり入れるべきだと思う、最初にかけた結果間違ってるかも
            
            #終わったら次のアノテーションに移る

            previous_start_point = start_point
            previous_end_point = end_point
      
        haDf = pd.DataFrame(onset, columns = ['onset'])

        #ELANのannotationの情報を結合
        df = pd.concat([df, haDf], axis=1)

        # moviename = homeDir + "InputData/" + args.dir + "/" + icatcherfile.replace('.txt', '.mp4')
        moviename = icatcherfile.replace('.txt', '.mp4')
        foldername = args.dir
        res = pd.DataFrame([[moviename]]*len(df)).join(df)
        res = res.rename(columns={0: 'filename'})
        res = pd.DataFrame([[foldername]]*len(res)).join(res)
        res = res.rename(columns={0: 'folder'})
        outputfile = os.path.join(outDir, icatcherfile.replace('.txt', '_icatcher&ELAN.csv'))
        res.to_csv(outputfile, index=False)