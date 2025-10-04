import os
import numpy as np
import boto3
from . import experiment
from .matching_s3_objects import get_matching_s3_keys


def find_behav_for_video(bucket, v_name, template=None):
    '''
    Given a video filename, identifies corresponding behavioural files, and prepares the experimental settings
    Inputs: vidfn - path to s3 file
    Outputs: a dictionary with
        ['matches']=corresponding behavioural files
        ['experiment']=corresponding experiment object
    Rhodri Cusack, Trinity College Dublin, 2018-02-11, rhodri@cusacklab.org
    Lookit data from Kim Scott, MIT via osf.io
    '''

    # path settings: YOU NEED TO CHANGE

    resp={}

    bucketname=bucket
    vidfn=v_name

    # !!the place of annotation is irregular. need to be modified!!
    ctspath = "Meta_data/Lookit/Lookit Annotations/"

    # Find out which experiment and direct to correct behavioural path
    (head, tail) = os.path.split(vidfn)
    
    # !!used this templage in special case. Normally template is False. 
    if template:
        mancodpth = "templates/"
        splits = vidfn.split("_")
        number = int(splits[-2])
        if number ==3 or number ==4 or number==5:
            resp['matches']=[mancodpth + 'right.txt']
        elif number ==6 or number==7 or number==8:
            resp['matches']=[mancodpth + 'left.txt']
        else:
            resp['matches']=[mancodpth + 'away.txt']
    else:

        # Match the each video filename to the corresponding manual coding filename[s]
        # For each video filename find all matching manual coding filenames, and create key we can use for this subject
        flds = tail.split('_privacy')
        subjname = flds[0]
        mancodpth = ctspath
    
        resp['matches']=[f for f in get_matching_s3_keys(bucketname, prefix=mancodpth,suffix='.txt') if os.path.basename(f).startswith(subjname)]
        resp['key'] = ''.join([x if x.isalnum() else '_' for x in subjname])

    resp['S3Bucket']=bucketname
    resp['experiment']=experiment.PreferenceLooking

    return resp