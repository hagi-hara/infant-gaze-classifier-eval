import os
import argparse
import pickle
import pandas as pd
import numpy as np

def predict_machine_learning(dir, outpth, usemedianforcentering=False, doevenifdone=False):
    """
    Run machine learning using trained model

    :param dir: path of combined results
    :param outpth: path for output of prediction
    :param usemedianforcentering: True - use median; False - use mean
    :param doevenifdone: Just run even if prediction results already exist
    :return:
    """

    # Used features
    pose_columns = ['Pitch', 'Yaw', 'Roll']
    landmark_columns = [['leftPupil', 'X'], ['rightPupil', 'X'], ['eyeLeft', 'X'], ['eyeRight', 'X']]
    bb_columns = ['Top', 'Left', 'Width', 'Height']
    classifycols = ['Pitch', 'Roll', 'Yaw', 'eyeLeft', 'eyeRight', 'EyesOpenValue',
                    'EyesOpenConfidence'] + ['BoundingBox' + col for col in bb_columns]
    finalcols = [col for col in classifycols] + ['leftPupil', 'rightPupil'] + ['Confidence', 'QualitySharpness', 'QualityBrightness']

    # Directory settings
    predict_dir = "ar/" + outpth
    combine_dir = dir + "combine/"
    print(combine_dir)
    os.makedirs(predict_dir, exist_ok=True)

    # Predict for each combined data
    files = os.listdir(combine_dir)
    for file in files:

        if file[-7:] != '.pickle':
            print(file)
            continue

        df = pd.DataFrame(columns=finalcols)

        with open(combine_dir + file, 'rb') as f:
            # Output settings
            basename = os.path.splitext(file)[0]
            print(basename)
            csv_name = predict_dir + basename +".csv"
            if not doevenifdone and os.path.isfile(csv_name):
                print("already predicted %s" % csv_name)
                continue
            
            # Load combined data and process
            obj = pickle.load(f)
            q = [[x['faces'][y] for y in x['infantind']] for x in obj['coding']] 
            myfaces = [[obj['allfaces'][z1] for z1 in z0] for z0 in q]

            for ind, item in enumerate(myfaces):
                # Build a row
                row = {}

                # One infant face?
                if len(item) == 1:
                    # Pose
                    for col in pose_columns:
                        row[col] = item[0]['Face']['Pose'][col]
                    # Landmarks
                    for col in landmark_columns:
                        row[col[0]] = [x[col[1]] for x in item[0]['Face']['Landmarks'] if x['Type'] == col[0]][0]
                    # Eyes open
                    row['EyesOpenValue'] = int(item[0]['Face']['EyesOpen']['Value'])
                    row['EyesOpenConfidence'] = item[0]['Face']['EyesOpen']['Confidence']
                    # Bounding box
                    for col in bb_columns:
                        row['BoundingBox' + col] = item[0]['Face']['BoundingBox'][col]
                    # Confidence and Quality
                    row['Confidence'] = item[0]['Face']['Confidence']
                    row['QualitySharpness'] = item[0]['Face']['Quality']['Sharpness']
                    row['QualityBrightness'] = item[0]['Face']['Quality']['Brightness']


                row['timestamp'] = obj['coding'][ind]['timestamp']
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

            timestamp = df['timestamp']
            mask = df.isnull().any(axis=1)

            # Split data into data with faces and without faces
            noface = df[mask]
            noface = noface.assign(prediction="noface")
            dropna = df[~mask]

            # Apply trained model only to data with faces
            if dropna.empty:
                df = noface
            else:
                if usemedianforcentering:
                    zerocentre = dropna[classifycols].subtract(
                            dropna[classifycols].median())
                else:
                    zerocentre = dropna[classifycols].subtract(
                        dropna[classifycols].mean())

                # Run trained model
                modelname = 'model.sav'
                clf = pickle.load(open(modelname, 'rb'))
                prednonan = clf.predict(zerocentre)
                result = dropna.assign(prediction=prednonan)
                df = pd.concat([noface, result], sort=False).sort_index()

            # Formatting the output
            df = df.fillna("NA")
            df = df.replace({'prediction': {-1: "left", 1: "right", 2: "away"}})
            df['timestamp'] = timestamp

            print(df)
            df.to_csv(csv_name, index=False)

    print("///////////////// finish machine learning ////////////////////")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dir', default='Public')
    args = parser.parse_args() 
    outpth = args.dir + "/"
    mlres = predict_machine_learning("result/" + outpth, outpth, usemedianforcentering=True)