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
ELANDir = homeDir + "OutputData/ELAN/" + args.dir #ELANのannotationのみの結果のcsvが、このディレクトリの下に「動画名.csv」として入っていることを想定

outDir = homeDir + "OutputData/frame2time/" + args.dir + "/icatcher_ffprobe_ELAN/annotation"
os.makedirs(outDir, exist_ok=True)


for icatcherfile in icatcherfiles:
    csvname = icatcherfile.replace('.txt', '.csv')
    print(csvname)
    if os.path.exists(os.path.join(ffprobeDir, csvname)) & os.path.exists(os.path.join(ELANDir, csvname)):
        annotationfile = os.path.join(icatcherDir, icatcherfile)
        ffprobefile = os.path.join(ffprobeDir, csvname)
        ELANfile = os.path.join(ELANDir, csvname)

        icatcherDf = pd.read_csv(annotationfile, names=["frame", "annotation", "confidence"])

        ffprobeDf = pd.read_csv(ffprobefile)
        frameNumber = len(ffprobeDf)
        newffprobeDf = ffprobeDf[4:(frameNumber-4)]
        newffprobeDf = newffprobeDf.reset_index(drop=True)

        gazeDf = pd.read_csv(ELANfile, skiprows=1, header=None) #上に余分な情報が入っていることを想定

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

        human_annotation = ["NA"]*len(df) #dfと同じ長さの空のリストを作る
        pts = list(df["pts_time"]) #ptstimeをリスト化

# filename,frame,pts_time,duration_time,icatcher_annotation,icatcher_confidence,onset
        base_time = pd.to_datetime('00:00:0.0', format='%H:%M:%S.%f')
        gazeDf[0]=(pd.to_datetime(gazeDf[0], format='%H:%M:%S.%f') - base_time).dt.total_seconds()
        gazeDf[1]=(pd.to_datetime(gazeDf[1], format='%H:%M:%S.%f') - base_time).dt.total_seconds()
        gazeDf[2]=(pd.to_datetime(gazeDf[2], format='%H:%M:%S.%f') - base_time).dt.total_seconds()
        
        for row in gazeDf.itertuples():
            start = row[1]
            end = row[2] #中身は１つの値
            annotation = row[4]

            #ptstimeの全要素とstartの差分を取り、最も小さい地点をhumannanotationの開始点とする
            diff_start = list(map(lambda x: x-start, pts))
            min_start = min(diff_start, key=abs)
            start_point = diff_start.index(min_start)
            #endでも同様のことを行い、終了点を決める
            diff_end = list(map(lambda x: x-end, pts))
            min_end = min(diff_end, key=abs)
            end_point = diff_end.index(min_end)
            
            #その間は全部同じタグにする
            human_annotation[start_point:end_point+1] = [annotation]*(end_point - start_point + 1)
            
            #終わったら次のアノテーションに移る
      
        haDf = pd.DataFrame(human_annotation, columns = ['human_annotation'])
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