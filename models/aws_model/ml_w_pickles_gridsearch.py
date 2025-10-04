import os
import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier
import random 
import threading, time
from multiprocessing import Process

# Used features
bb_columns = ['Top', 'Left', 'Width', 'Height']
classifycols = ['Pitch', 'Roll', 'Yaw', 'eyeLeft', 'eyeRight', 'EyesOpenValue',
                'EyesOpenConfidence'] + ['BoundingBox' + col for col in bb_columns]
summary_dir = "./summary/"

def open_file(fn, usemedianforcentering):
    with open(fn, 'rb') as f:
        obj = pickle.load(f)

        # Drop unnecessary codes
        for testsubjind, testdata in enumerate(obj):
            dropna = testdata['df'].dropna()
            target = dropna.index[(dropna['mancod'] == 0) | (dropna['mancod'] == 3)]
            obj[testsubjind]['df_dropna'] = dropna.drop(target)

        # Centre the classification columns
        for testsubjind, testdata in enumerate(obj):
            if testdata["df_dropna"].empty:
                testdata['df_zerocentre'] = testdata["df_dropna"]
                continue

            if usemedianforcentering:
                testdata['df_zerocentre'] = testdata['df_dropna'][classifycols].subtract(
                    testdata['df_dropna'][classifycols].median())
            else:
                testdata['df_zerocentre'] = testdata['df_dropna'][classifycols].subtract(
                    testdata['df_dropna'][classifycols].mean())

        # Concat all data
        trainlabel = pd.concat(
            [x[1]['df_dropna']['mancod'] for x in enumerate(obj) if not x[1]['df_dropna'].empty])
        trainfeat = pd.concat([x[1]['df_zerocentre'] for x in enumerate(obj) if not x[1]['df_dropna'].empty])

        n_label = trainlabel.reset_index(drop=True)
        n_feat = trainfeat.reset_index(drop=True)

        return n_label, n_feat

def train_machine_learning(min_samples_split, max_depth, min_samples_leaf,  trainfeats, trainlabels):
    """
    Runs leave-one-subject-out machine learning

    :param bucket: bucket to work
    :param experimentfilters: list of paths to coding_summary
    :return:
    """

    random.seed(75)

    # Define model and train
    model = RandomForestClassifier(
        min_samples_split=min_samples_split, 
        max_depth=max_depth, 
        min_samples_leaf=min_samples_leaf, 
        random_state = 75)

    # Check performance of the model
    score = cross_val_score(model, trainfeats, trainlabels, scoring='accuracy', cv=5)
    print(min_samples_split, max_depth, min_samples_leaf, score, np.mean(score))

if __name__ == '__main__':
    current_time = time.time()

    min_samples_splits=[60000, 80000, 100000]
    max_depths=[10, 20, 30, None]
    min_samples_leafs= [4000, 6000, 8000]
    usemedianforcentering=True
    processes = []

    # Extract names of summmary files
    files = os.listdir(summary_dir)

    # Definition for data
    trainlabels = pd.Series()
    trainfeats = pd.DataFrame()

    # Load summary file for training
    for file in files:
        fn = summary_dir + file
        n_label, n_feat = open_file(fn, usemedianforcentering)
        trainlabels = pd.concat(objs=[n_label, trainlabels], ignore_index=True)
        trainfeats = pd.concat(objs=[n_feat, trainfeats], ignore_index=True)
        trainlabels = trainlabels.reset_index(drop=True)
        trainfeats = trainfeats.reset_index(drop=True)
    
    # Change the format
    trainlabels = trainlabels.astype("float")

    for min_samples_split in min_samples_splits:
        for max_depth in max_depths:
            for min_samples_leaf in min_samples_leafs:
                process = Process(target=train_machine_learning,
                                            args=(min_samples_split, 
                                               max_depth, 
                                               min_samples_leaf, 
                                               trainfeats, 
                                               trainlabels))
                process.start()
                processes.append(process)

    # Wait processs
    for process in processes:
        process.join()

    print('Time: ' + str(time.time() - current_time))
    