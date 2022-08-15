import json
import ovh
import time
import paramiko
import requests
from sys import exit

projectid = '' # insert your project ID
url = '' # insert URL to your website

# Client info
client = ovh.Client(
    endpoint='ovh-eu',
    application_key='', # insert your AK
    application_secret='', # insert your AS
    consumer_key='', # insert your CK
)

# Greetings
print("Welcome,", client.get('/me')['firstname'])

# Instance creation
print('Creating the instance...')
result = client.post('/cloud/project/'+ projectid +'/instance', 
    flavorId='3cf2bf37-4e49-411a-93c1-8908ff3e05f0',
    imageId='5e8b011f-917a-4a36-8bc8-38aaaf0aa327',
    name='testinst',
    region='WAW1',
    sshKeyId='sshkeyid' # replace 'sshkeyid' with your SSH key ID
)

# Make sure the instance is up and running
if result:
    time.sleep(100) # let OVH create the instance
    print('Done')
else:
    print('Failed to create an instance')
    exit()

# Get the ID and IP of the created instance
result1 = client.get('/cloud/project/'+ projectid +'/instance', 
    region='WAW1'
)
vpsid = result1[0]['id']
if vpsid:
    print('Instance ID is successfully extracted')
else:
    print('Failed to extract the instance ID')
    exit()
for i in range(len(result1)):
    if result1[i]['ipAddresses'][0]['version']==4:
        vpsip = result1[i]['ipAddresses'][0]['ip']
if vpsip:
    print('Instance IP is successfully extracted')
else:
    print('Failed to extract the instance IP')
    exit()

# Connect
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print("Connecting...")
c.connect(hostname = vpsip, username = "ubuntu", key_filename='') # insert full path to your SSH key into key_filename
print("Connected")

# Transfer certificate
print("Uploading Cloudfare certificate to the instance")
ftpc = c.open_sftp()
ftpc.put('localPathToJS','vmPathToJS') # replace with paths to .js certificate file
ftpc.put('localPathToPem','vmPathToPem') # replace with paths to .pem certificate file
ftpc.put('localPathToJson','vmPathToJson') # replace with paths to .json certificate file
ftpc.close()
print("Done")

# Execute commands
jsoncertname = '' # insert your .json certificate filename
command = 'sudo docker container run --name web_server -d -p 8080:80 nginx'
command1 = 'wget -q https://bin.equinox.io/c/VdrWdbjqyF/cloudflared-stable-linux-amd64.deb && \
#sudo dpkg -i cloudflared-stable-linux-amd64.deb && mkdir .cloudflared && mv cert.pem \
#~/.cloudflared/cert.pem && mv '+ jsoncertname +' \
#~/.cloudflared/'+ jsoncertname +' && cloudflared tunnel --hostname '+ url +' http://localhost:8080'
print('Creating docker container')
stdin, stdout, stderr = c.exec_command(command)
time.sleep(120)
print('Done, executing commands')
stdin1, stdout1, stderr1 = c.exec_command(command1)
time.sleep(30)
print('Done')

# Website status check
request_response = requests.head(url)
status_code = request_response.status_code
if status_code == 200:
    print('Website is up')
else:
    print('Website is down')
c.close()

# Stop and terminate the instance
print('Stopping the instance...')
result2 = client.post('/cloud/project/'+ projectid +'/instance/'+ vpsid +'/stop')
time.sleep(3)
print('Stopped')
print('Deleting the instance...')
result3 = client.delete('/cloud/project/'+ projectid +'/instance/'+ vpsid)
print('Deleted')
time.sleep(7)
result4 = client.get('/cloud/project/'+ projectid +'/instance',
region='WAW1')
print('Available instances:')
print(json.dumps(result4, indent=4))
