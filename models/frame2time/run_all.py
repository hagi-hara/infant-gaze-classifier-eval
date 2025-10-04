import subprocess

folders = ['Public','PublicbrighterAI','Scientific','ScientificbrighterAI','Private','PrivatebrighterAI']
for folder in folders:
    command = 'python3 icatcher_ffprobe_ELAN_annotation_box.py -d {}'.format(folder)
    ret = subprocess.run(command, shell=True)
    print(ret)

for folder in folders:
    command = 'python3 finalcsvs_box.py -d {}'.format(folder)
    ret = subprocess.run(command, shell=True)
    print(ret)