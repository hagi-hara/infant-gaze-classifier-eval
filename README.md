# infant-gaze-classifier-eval

This repository contains the scripts used in the following study.

Hagihara, H., Kimura, N., Zaadnoordijk, L., Yasuda, R., Cusack, R., & Tsuji, S (2025). Comparing automated gaze classifiers in infant looking studies: Accuracy and vulnerability to environmental factors.


## analysis

Scripts for analyzing the estimated results.

Note: The original video data used in the study are safely stored at the IRCN Babylab, The University of Tokyo. Caregivers could consent to share their data publicly, with other research teams, or not at all. Accordingly, upon request, a subset of the data can be shared with other research teams. The anonymized gaze coding data, representing partial data from participants who consented to scientific use (N=24/47), can be found at: [https://doi.org/10.17605/OSF.IO/HPRC2](https://doi.org/10.17605/OSF.IO/HPRC2).


## models

Scripts for obtaining estimation results.

### accuracy

Scripts for calculating reliability between gaze estimator predictions and human annotations using a time window.

### aws_model

Scripts for the AWS-based gaze estimation method.
These scripts are adapted from Rhodri Cusack’s code: https://github.com/rhodricusack/aws_video

### frame2time

Scripts for merging the results of ffprobe with other results.

### human-human_reliabitilty

Scripts for calculating reliability between two human annotations using a time window.

### noise

Scripts for calculating noise factors.