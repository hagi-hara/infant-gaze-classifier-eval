import os
import pickle
import pandas as pd
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn import metrics
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import random
import time

# Used features
bb_columns = ['Top', 'Left', 'Width', 'Height']
classifycols = ['Pitch', 'Roll', 'Yaw', 'eyeLeft', 'eyeRight', 'EyesOpenValue',
                'EyesOpenConfidence'] + ['BoundingBox' + col for col in bb_columns]
summary_dir = "./summary/"

def open_file(fn, usemedianforcentering):
    """
    Open and load training data

    :param fn: filename
    :param usemedianforcentering: True - use median; False - use mean
    :return n_label: Labels of data
    :return n_feat: Features of data
    """
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
                print("empty")
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

def train_machine_learning(possible_codes, usemedianforcentering=False):
    """
    Train with all data you have

    :param possible_codes: Possible codes of data
    :param usemedianforcentering: True - use median; False - use mean
    :return:
    """
    random.seed(75)

    # Extract names of summmary data
    files = os.listdir(summary_dir)

    # Definition for data
    trainlabels = pd.Series()
    trainfeats = pd.DataFrame()

    # Load summary files for training
    for file in files:
        print("train: ", file)
        fn = summary_dir + file
        n_label, n_feat = open_file(fn, usemedianforcentering)
        trainlabels = pd.concat(objs=[n_label, trainlabels], ignore_index=True)
        trainfeats = pd.concat(objs=[n_feat, trainfeats], ignore_index=True)
        trainlabels = trainlabels.reset_index(drop=True)
        trainfeats = trainfeats.reset_index(drop=True)
    
    # Change the format
    trainlabels = trainlabels.astype("float")

    # Define model and train
    clf = RandomForestClassifier(
        min_samples_split=80000, 
        max_depth=20, 
        min_samples_leaf=6000, 
        random_state = 75)
    clf.fit(trainfeats, trainlabels)
    filename = 'model.sav'
    pickle.dump(clf, open(filename, 'wb'))

    # Check whether training works well
    prednonan = clf.predict(trainfeats)
    cnf = metrics.confusion_matrix(trainlabels, prednonan, labels=possible_codes)
    columns_labels = ["pred_" + str(l) for l in possible_codes]
    index_labels = ["act_" + str(l) for l in possible_codes]
    cm = pd.DataFrame(cnf, columns=columns_labels, index=index_labels)
    print(cm)

    sns.heatmap(cm, square=True, cbar=True, annot=True, cmap='Blues')
    plt.savefig('confusion_matrix.png')

    score = accuracy_score(prednonan, trainlabels)
    print(f"accuracy: {score * 100}%")


if __name__ == '__main__':
    current_time = time.time()
    possible_code = np.array([[-1, 1, 2]])
    mlres = train_machine_learning(possible_code[0], usemedianforcentering=True)
    print('Time: ' + str(time.time() - current_time))