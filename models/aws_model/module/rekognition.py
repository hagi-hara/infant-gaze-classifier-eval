import hashlib
import os
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
import json
import time

def get_job_result(job_id, outname, n):
    """
    Get job result of processed video,
    :param job_id: job_id of Amazon Rekognition
    :param outname: Name of output json file from Amazon Rekognition
    :param n: Interval to request
    :return:
    """

    # Get result from rekognition
    rekognition = boto3.client('rekognition')

    try:
        if job_id is not None:
            while True:
                time.sleep(n)
                response = rekognition.get_face_detection(JobId=job_id)
                if response['JobStatus'] == 'SUCCEEDED':
                    break
                else:
                    print(response)

            allfaces = response['Faces']
            while 'NextToken' in response:
                response = rekognition.get_face_detection(JobId=job_id, NextToken=response['NextToken'])
                allfaces.extend(response['Faces'])
            print("%d faces detected" % len(allfaces))
        else:
            raise Exception

        with open(outname, 'w', encoding='utf-8', newline='\n') as fp:
            json.dump(allfaces, fp, indent=4)

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("No response from rekognition available for job_id %s" % job_id)
        else:
            raise

def run_video_rekognition(bucket, basepath, n, doevenifdone=False):
    """
    Runs AWS face rekognition on all of the files under a directory,
    :param bucket: Name of the s3 bucket in which specified folder is inside
    :param basepath: Path name where outputs are stored
    :param n: Interval to request
    :param doevenifdone: If it is True, even though files are alredy processed, run AR anyway
    :return:
    """

    # Configuration
    prefix =  basepath.split("/")[1]  + "/"
    s3 = boto3.client('s3')
    rekognition = boto3.client('rekognition')

    # Get all files under spedified prefix
    paginator = s3.get_paginator('list_objects')
    operation_parameters = {'Bucket': bucket, 'Prefix': prefix}
    page_iterator = paginator.paginate(**operation_parameters)

    # Store filenames of videos
    outname_list = []

    # For each file create start face detection job
    for page in page_iterator:
        for myobj in page['Contents']:
            # Only process objects with .mp4 suffix
            if myobj['Key'][-4:] == '.mp4':
                # Set the video name
                v_path = myobj['Key']  
                basename = v_path.replace(prefix, '')
                basesubpath = basename.replace('.mp4', '.json')
                outname = basepath + basesubpath
                print(outname)

                # Don't submit if already coded
                is_file = os.path.isfile(outname)
                print(is_file)

                # Exclude spedified videos (you can modify as you like)
                if v_path[-12:] == '_lighter.mp4':
                    print("Skipping lighter video %s" % outname)
                    continue
                
                # Record the name of videos
                outname_list.append(v_path)

                # Run Amazon Rekognition
                if doevenifdone or not is_file:
                    response = rekognition.start_face_detection(
                        Video={'S3Object': {
                            'Bucket': bucket, 'Name': v_path}
                        },
                        ClientRequestToken=hashlib.md5(str('s3://' + bucket + '/' + v_path).encode()).hexdigest(),
                        FaceAttributes='ALL',
                    )
                    get_job_result(response['JobId'], outname, n)
                else:
                    print("Already done %s" % outname)

    return outname_list