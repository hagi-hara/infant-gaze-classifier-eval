import hashlib
from .utils.infant_face_match_video_and_behav_s3 import find_behav_for_video
from .utils import videotools as videotools
import os
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
from scipy import stats
import skvideo
from .utils import s3tools as s3tools
import json
import pickle
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw

def calc_deltat(allfaces):
    ts = [face['Timestamp'] for face in allfaces]
    difft = np.ediff1d(ts)
    difft = [x for x in difft if not x == 0]
    deltat = stats.mode(difft).mode
    print("Delta t is %f" % deltat)
    return deltat

def detect_infant(faces, allfaces):
    infantfaces = []
    infantind = []
    for i0, faceind in enumerate(faces):
        if allfaces[faceind]['Face']['AgeRange']['Low'] < 10: # you shold change
            infantind.append(i0)  # which of elements in faces are infants
            infantfaces.append(allfaces[faceind]['Face'])

    # If two largely overlapping faces are found, they must be the same one, so delete one
    if len(infantind) == 2:
        bb0 = allfaces[faces[infantind[0]]]['Face']['BoundingBox']
        bb1 = allfaces[faces[infantind[1]]]['Face']['BoundingBox']
        dx = bb0['Left'] - bb1['Left']
        mw = 0.5 * (bb0['Width'] + bb1['Width'])
        dy = bb0['Top'] - bb1['Top']
        mh = 0.5 * (bb0['Height'] + bb1['Height'])

        if np.sqrt((dx / mw) ** 2 + (dy / mh) ** 2) < 0.1:  # shifted by less than 10% of size
            infantind = [infantind[0]]
            infantfaces = [infantfaces[0]]

    return infantfaces, infantind

def combine_manual_coding(bucket, outname, basepath, doevenifdone=False, predict=False):
    """
    Extract details from processed video,
    :param bucket: S3 bucket for data
    :param outname: Names of an output from AR
    :param basepath: Path name where outputs from AR are stored
    :param doevenifdone: Do again even if output already present
    :param predict: Specifiy it False when there is no annotation
    :return:
    """

    # Setting of names
    basename = outname.replace(".mp4", '')
    filename = "result/" + basename

    # Open json output from AR
    json_open = open(filename + '.json', 'r')
    allfaces = json.load(json_open)

    # Coding filename
    outpath = basepath + "combine/" + basename.split("/")[-1] + '.pickle'
    print(outpath)

    if doevenifdone or not os.path.exists(outpath):
        try:
            # Get the behavioural file that corresponds to the video
            deltat = calc_deltat(allfaces)

            if not predict:
                behav = find_behav_for_video(bucket, outname, template=False)
                print(behav)

                if not behav['matches']:
                    print("No behavioural file found to correspond to %s" % outname)
                    return False

                exp = []
                for rater in behav['matches']:
                    print(rater)
                    pth = s3tools.getpath({'S3Bucket': behav['S3Bucket'], 'S3ObjectName': rater})
                    exp.append(behav['experiment'](pth))
                print(exp)

            # Get the video
            vid = {'S3Bucket': bucket, 'S3ObjectName': outname}
            v = videotools.Video(vid)
            if v._pth is None or not os.path.exists(v._pth):
                print("Video not found")
                return False
            else:
                v.open()
                dur = v.get_dur()
                fps = v.get_fps()
                print("Dur %f and FPS %f" % (dur, fps))

                # Make directory if necessary
                dirname = os.path.dirname(outpath)
                if not os.path.exists(dirname):
                    os.makedirs(dirname)

                facetimes = [face['Timestamp'] for face in allfaces]

                firstface = 0
                # Store all coding results
                coding = []

                #1timestamp - 1loop
                while v.isopen:
                    # Get frame
                    img = v.get_next_frame()

                    # End of video
                    if img is None:
                        break

                    currtime_ms = np.round(v.currtime * 1000)

                    # Move forwards the first face we need to consider, if appropriate
                    while firstface < len(facetimes) and facetimes[firstface] < (
                            currtime_ms - deltat / 2 + 1):  # 1 ms buffer for rounding errors
                        firstface += 1

                    # Add all faces to the last one we need to consider
                    faces = []
                    for ind in range(firstface, len(facetimes)):
                        if facetimes[ind] >= (currtime_ms + deltat / 2):
                            break
                        faces.append(ind)

                    # Select only infant faces
                    infantfaces, infantind = detect_infant(faces, allfaces)

                    # Annotate manual coding status on border of image
                    if not predict:
                        mancod_allraters = []
                        for singlerater in exp:
                            mancod_allraters.append(singlerater.get_mancod_state(currtime_ms))

                        # Store the coding results
                        coding.append({'mancod_allraters': mancod_allraters, 'faces': faces,
                                    'infantind': infantind, 'timestamp' : currtime_ms})
                    else:
                        coding.append({'faces': faces,'infantind': infantind, 'timestamp' : currtime_ms})

                # Create summary dict
                summary = {'coding': coding, 'allfaces': allfaces, 'vid': outname, 'deltat': deltat, 'fps': fps, 'dur': dur}

                # Write coding file
                with open(outpath, 'wb') as f:
                    pickle.dump(summary, f)

                return True

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print("No response from rekognition available for job_id")
                return False
            else:
                raise
    else:
        print("Not repeating previously annotated %s" % outpath)
        return False