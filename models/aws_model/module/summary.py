import os
from botocore.exceptions import ClientError
from pathlib import Path
import pickle
import pandas as pd

def export_summary_pickle(bucket, basepath, predict=False):
    """
    Summarize all data below basepath
    :param bucket: S3 bucket for data
    :param basepath: Path name where outputs from AR are stored
    :param predict: Specifiy it False when there is no annotation
    :return:
    """

    # When predicting, summary file isn't necessary
    if predict: return

    # Columns to be extracted
    pose_columns = ['Pitch', 'Yaw', 'Roll']
    landmark_columns = [['leftPupil', 'X'], ['rightPupil', 'X'], ['eyeLeft', 'X'], ['eyeRight', 'X']]
    bb_columns = ['Top', 'Left', 'Width', 'Height']

    df = []
    allagerangelow = []
    allagerangehigh = []

    # Output path for sammary file
    os.makedirs('summary/', exist_ok=True)
    pth_name= 'summary/' +  basepath.split("/")[1] + '.pickle'
    
    # Path for combined files
    prefix = basepath + "combine/"

    # Process each subject and add to dataframe
    for file in os.listdir(prefix):
        # If file isn't pickle, skip this file
        if file[-7:] != '.pickle':
            continue

        fn = prefix + file
        print(fn)
        df.append({'S3Bucket': bucket, 'S3ObjectName': file,
                   'df': pd.DataFrame(columns=pose_columns + [x[0] for x in landmark_columns] + ['mancod'])})
        
        with open(fn, 'rb') as f:
            obj = pickle.load(f)

            df[-1]['deltat'] = obj['deltat']
            df[-1]['fps'] = obj['fps']
            df[-1]['dur'] = obj['dur']

            q = [[x['faces'][y] for y in x['infantind']] for x in obj[
                'coding']]  # "faces" contains indices within allfaces. "infantind" contains indices within faces. Get indices of infants among allfaces.
            myfaces = [[obj['allfaces'][z1] for z1 in z0] for z0 in q]  # get actual face data from allfaces

            # Get the face details
            allagerangelow.extend([x['Face']['AgeRange']['Low'] for x in obj['allfaces']])
            allagerangehigh.extend([x['Face']['AgeRange']['High'] for x in obj['allfaces']])

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

                # And mean manual coder
                list = [x['code'] for x in obj['coding'][ind]['mancod_allraters']]
                row['mancod'] = float(max(set(list), key=list.count))
                
                df[-1]['df'] = pd.concat([df[-1]['df'], pd.DataFrame([row])], ignore_index=True)

        print(df[-1]['df'].describe())

    # Save result as json in local 
    with open(pth_name, 'wb') as f:
        pickle.dump(df, f)

    # Done!
    print("All done")