import boto3
import os.path
from ast import literal_eval

ec2 = boto3.resource('ec2')
client = boto3.client('ec2')

instance_name_id = {}

def list_instances(instanceID = None):
    global instance_name_id
    instances = ec2.instances
    if (instanceID is not None):
        instances = instances.filter(InstanceIds=instanceID)
    else:
        instances = instances.filter()
    
    instance_name_id = {}
    for instance in instances:
        name = next((tag['Value'] for tag in instance.tags if tag['Key'] == 'Name'), '-')
        info = '| {:<18s} | {:<18s} | {:<18s} | {:<18s} |'.format(name, instance.id, instance.instance_type, instance.state['Name'])
        print(info)
        if (name != '-'):
            instance_name_id[name] = instance.id

def instances_action(instanceIDs, action):
    if type(instanceIDs) is str:
        instanceIDs = [instanceIDs]

    # Translate names if possible
    instanceIDs = [instance_name_id[id] if id in instance_name_id else id for id in instanceIDs]
    
    try:
        result = action(instanceIDs)
    except Exception as err:
        print('Failed to perform command: {0}'.format(err))
        return

    return result

def start(instanceIDs):
    print('Starting instance...')
    return instances_action(instanceIDs, lambda ids: client.start_instances(InstanceIds=ids))

def stop(instanceIDs):
    print('Stopping instance...')
    return instances_action(instanceIDs, lambda ids: client.stop_instances(InstanceIds=ids))

def terminate(instanceIDs):
    print('Terminating instance...')
    return instances_action(instanceIDs, lambda ids: client.terminate_instances(InstanceIds=ids))

def create(name, imageId = 'ami-09e67e426f25ce0d7', instanceType = 't2.micro', keypair = 'matyas-aws', secGroup = 'sg-07412473e0d10eda1', userScript = ''):
    print('Starting instance...')
    if os.path.exists(userScript):
        with open(userScript, 'r') as file:
            userScript = file.read()
    return client.run_instances(ImageId=imageId,
                        InstanceType=instanceType,
                        MinCount=1,
                        MaxCount=1,
                        KeyName=keypair,
                        SecurityGroupIds=[secGroup],
                        UserData=userScript,
                        TagSpecifications=[{
                            'ResourceType': 'instance',
                            'Tags': [
                                {
                                    'Key': 'Name',
                                    'Value': name
                                },
                            ]}],
                        )

def ssh(instanceID):
    import subprocess, shlex

    # Translate name if possible
    instanceID = [instance_name_id[iid] if iid in instance_name_id else iid for iid in instanceID]
    instance = next((x for x in ec2.instances.filter(InstanceIds=instanceID)), None)
    if (instance is not None):
        print('Connecting to {0}...'.format(instance.public_ip_address))
        subprocess.check_call(shlex.split('ssh.exe -i "C:\\Users\\Matyas\\.ssh\\matyas-aws.pem" ubuntu@{0}'.format(instance.public_ip_address)))
        help()


def help():
    print('Options:')
    print('     l, list                   - show instances and their status')
    print('     u, up, start instance_id  - start instance by id')
    print('     d, down, stop instance_id - stop instance by id')
    print('     t, terminate  instance_id - terminate instance by id')
    print('     c, create name [imageId] [instanceType] [keypair] [securityGroup] [--userScript=script.py]- create new instance')
    print('     x, exit                   - exit')


def main():
    help()

    while True:
        line = input('> ').split()
        if (len(line) == 0):
            continue
        
        cmd = line.pop(0)
        if (cmd in ('l', 'list')):
            list_instances()
        elif (cmd in ('u', 'up', 'start')):
            start(line)
        elif (cmd in ('d', 'down', 'stop')):
            stop(line)
        elif (cmd in ('t', 'terminate')):
            terminate(line)
        elif (cmd in ('c', 'create')):
            name = line.pop(0)
            kwargs = dict((k.lstrip('--'), v) for k, v in (pair.split('=') for pair in line))
            create(name, **kwargs)
        elif (cmd in ('ssh')):
            ssh(line)


        elif (cmd in ('x', 'exit')):
            break
    
main()

