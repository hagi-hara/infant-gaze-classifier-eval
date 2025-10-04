import subprocess

folders = ['Public','PublicbrighterAI','Scientific','ScientificbrighterAI','Private','PrivatebrighterAI']
for folder in folders:
    command = 'python3 owlet_concat.py -d {}'.format(folder)
    ret = subprocess.run(command, shell=True)
    print(ret)
    
for folder in folders:
    command = 'python3 ar_concat.py -d {}'.format(folder)
    ret = subprocess.run(command, shell=True)
    print(ret)

command = 'python3 add_2direction.py'
ret = subprocess.run(command, shell=True)

command = 'python3 reliability_check.py'
ret = subprocess.run(command, shell=True)