import boto3
import botocore
import aws_script
import threading
import random
from constants import IMAGE_ID

vocals = 'aeiou'
consonants = 'bcdfghjklmnpqrstvwxz'
def create_random_name():
    ans = ''
    for i in range(3):
        ans += consonants[random.randint(0,len(consonants)-1)] + vocals[random.randint(0, len(vocals)-1)]
    return ans

class AmazonManager:
    INSTANCE_TYPE_LIST = [
        {'type': 't2.micro', 'zone': 'us-east-1a'},
        {'type': 't2.micro', 'zone': 'us-east-1b'},
    ] #['m4.large', 't2.xlarge']

    def __init__(self):
        self.ec2_resource = boto3.resource('ec2')
        self.ec2 = boto3.client('ec2')
        self.elbv2 = boto3.client('elbv2')
        self.children = []
        self.load_balancer_arn = None
        self.listener_arn = None
        self.rules_arn = []
        self.dns_name = None
        self.security_group = None
        self.vpc = next(iter(self.ec2_resource.vpcs.all()))
        self.batch_name = create_random_name()
        print('Starting batch ' + self.batch_name)

    def setup(self):
        self.create_security_group()

        threads = []
        for cluster_nb, instance_type in enumerate(AmazonManager.INSTANCE_TYPE_LIST):
            self.children.append( SubCluster(self, cluster_nb+1, instance_type) )
            thread = threading.Thread(target=self.children[cluster_nb].setup)
            thread.start()
            threads.append( thread )
            
        self.create_load_balancer()
        self.create_listener_if_needed()

        for thread in threads:
            thread.join()

        for child in self.children:
            self.create_rule(child)

        y = input('Do you want to wait for health checks [y/n]?'+
            ' Your application will not be online before health checks are passed. They might take 5-10 minutes.')
        if y != 'n':
            print('Waiting for health checks (might take 5-10 minutes)...')
            for child in self.children:
                child.wait_for_group()
        print('Everything set up!')

    def shutdown(self):
        self.delete_rules()
        self.delete_listener()

        self.delete_load_balancer()

        for child in self.children:
            child.shutdown()
        for child in self.children:
            child.wait_for_shutdown()

        self.delete_security_group()

    def my_listener_kwargs(self):
        return {'LoadBalancerArn':self.load_balancer_arn,
            'Protocol':'HTTP', 'Port':80,
            'DefaultActions':[
                {
                    'Type': 'fixed-response',
                    'FixedResponseConfig': { 'StatusCode': '404' },
                },
            ]
        }

    def create_load_balancer(self):
        #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.create_load_balancer
        print('Create load balancer')
        resp = self.elbv2.create_load_balancer(
            Name='load-balancer-version-one',
            Subnets = [subnet.id for subnet in self.ec2_resource.subnets.filter()],
            SecurityGroups=[ self.security_group ],
            Scheme='internet-facing',
            Type='application',
            IpAddressType='ipv4'
        )
        self.load_balancer_arn = resp['LoadBalancers'][0]['LoadBalancerArn']
        self.dns_name = resp['LoadBalancers'][0]['DNSName']

    def delete_load_balancer(self):
        if self.load_balancer_arn:
            print('Delete load balancer')
            #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.delete_load_balancer
            self.elbv2.delete_load_balancer(LoadBalancerArn=self.load_balancer_arn)
            self.load_balancer_arn = None

    def create_listener_if_needed(self):
        #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.describe_listeners
        response = self.elbv2.describe_listeners(LoadBalancerArn=self.load_balancer_arn )
        if response['Listeners'] == []: #if there was no listener, create one
            self.create_listener()
            return
        listener_kwargs = self.my_listener_kwargs() #if there was a listener, check whether it is the same than the one we want to create
        for key in listener_kwargs:
            if response['Listeners'][0][key] != listener_kwargs[key]:
                self.elbv2.delete_listener(ListenerArn=response['Listeners'][0]['ListenerArn']) #if not, delete it and create a new one
                self.create_listener()
                return
        rules = client.describe_rules( ListenerArn=response['Listeners'][0]['ListenerArn'] ) #if it is the same, we will still delete its rules,
        #because it's easier than checking whether the rules can stay the same
        for rule in rules['Rules']:
            self.elbv2.delete_rule(RuleArn=rule['RuleArn'])

    def create_listener(self):
        print('Create listener')
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.create_listener
        listener = self.elbv2.create_listener(**self.my_listener_kwargs())
        self.listener_arn = listener['Listeners'][0]['ListenerArn']

    def delete_listener(self):
        if self.listener_arn:
            print('Delete listener')
            #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.delete_listener
            self.elbv2.delete_listener(ListenerArn=self.listener_arn)
            self.listener_arn = None

    def create_rule(self, child):
        print('Create rule')
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.create_rule
        resp = self.elbv2.create_rule(
            ListenerArn=self.listener_arn,
            Conditions=[
                {
                    'Field': 'path-pattern',
                    'Values': [ child.htmlpath() ]
                },
            ],
            Priority=child.cluster_nb,
            Actions=[
                {
                    'Type': 'forward',
                    'TargetGroupArn': child.target_group_arn,
                },
            ]
        )
        self.rules_arn.append( resp['Rules'][0]['RuleArn'] )

    def delete_rules(self):
        for rule in self.rules_arn:
            print('Delete rule')
            #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.delete_rule
            self.elbv2.delete_rule(RuleArn=rule)
        self.rules_arn = []

    def create_security_group(self):
        SECURITY_GROUP_NAME = 'my-security-group-version-one'
        print('Create security group')
        try:
            sec_groups = self.ec2.describe_security_groups(GroupNames=[ SECURITY_GROUP_NAME ])
            self.security_group = sec_groups['SecurityGroups'][0]['GroupId']
        except botocore.exceptions.ClientError as x:
            response = self.vpc.create_security_group(
                Description='Allow ssh and http',
                GroupName=SECURITY_GROUP_NAME,
            )
            self.security_group = response.group_id
            #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.authorize_security_group_ingress
            self.ec2.authorize_security_group_ingress(
                GroupId=self.security_group,
                IpPermissions=[
                    {
                        'FromPort': 80,
                        'ToPort': 80,
                        'IpProtocol': 'tcp',
                        'IpRanges': [{'CidrIp': '0.0.0.0/0' }],
                        'Ipv6Ranges': [{ 'CidrIpv6': '::0/0' }],
                    },
                    {
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpProtocol': 'tcp',
                        'IpRanges': [{'CidrIp': '0.0.0.0/0' }],
                        'Ipv6Ranges': [{ 'CidrIpv6': '::0/0' }],
                    },
                ]
            )

    def delete_security_group(self):
        if self.security_group:
            print('Delete security group')
            #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.delete_security_group
            self.ec2.delete_security_group(GroupId=self.security_group)
            self.security_group = None

class SubCluster:
    def __init__(self, parent, cluster_nb, instanceType = {'type': 't2.micro', 'zone': 'us-east-1a'}):
        self.parent = parent
        self.instance_type = instanceType['type']
        self.cluster_nb = cluster_nb
        self.instance_ids = []
        self.target_group_arn = None
        self.zone = instanceType['zone']

    def setup(self):
        try:
            self.create_instances()

            self.create_target_group_if_needed()
            
            # Reference: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.register_targets
            targets = [ { 'Id': i, 'Port': 80 } for i in self.instance_ids]

            self.parent.elbv2.register_targets(
                    TargetGroupArn=self.target_group_arn,
                    Targets=targets
                )
        except Exception as x:
            self.shutdown()
            raise x

    def shutdown(self):
        self.delete_target_group()

        aws_script.terminate(self.instance_ids)

    def wait_for_shutdown(self):
        print('Waiting for instances to terminate...')
        waiter = self.parent.ec2.get_waiter('instance_terminated')
        waiter.wait( InstanceIds=self.instance_ids )
        self.instance_ids = []

    def htmlpath(self):
        return f'/cluster{self.cluster_nb}'

    def target_group_name(self):
        return f'cluster-{self.cluster_nb}'

    def create_instances(self):
        print('Create 4 instances')

        with open('flask_deploy.sh', 'r') as file:
            script = file.read() % self.cluster_nb

        tags = [
            { 'Key': 'Name', 'Value': f'{self.parent.batch_name}-{self.cluster_nb}-{self.instance_type}' },
            { 'Key': 'Batch', 'Value': self.parent.batch_name },
            { 'Key': 'Cluster', 'Value': str(self.cluster_nb) }
        ]

        resp = aws_script.create(
            availabilityZone=self.zone, nbInstances=4, userScript=script, instanceType = self.instance_type, tags=tags, imageId=IMAGE_ID,
            securityGroup=self.parent.security_group, monitoring=True
        )
        self.instance_ids = [ instance['InstanceId'] for instance in resp['Instances'] ]

        waiter = self.parent.ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=self.instance_ids)

    def create_target_group(self):
        print('Create target group')
        resp = self.parent.elbv2.create_target_group(
            Name=self.target_group_name(),
            Protocol='HTTP',
            ProtocolVersion='HTTP1',
            Port=80,
            VpcId=self.parent.vpc.id,
            HealthCheckEnabled=True,
            HealthCheckPath=self.htmlpath(),
            HealthCheckIntervalSeconds=10,
            HealthyThresholdCount=3,
            TargetType='instance',
            Tags=[
                {
                    'Key': 'Name',
                    'Value': f'target-group-{self.cluster_nb}'
                },
            ]
        )
        self.target_group_arn = resp['TargetGroups'][0]['TargetGroupArn']
        return self.target_group_arn

    def create_target_group_if_needed(self):
        try:
            self.create_target_group() #will succeed if the target group didn't exist, or existed with the same config
        except self.parent.elbv2.exceptions.DuplicateTargetGroupNameException:
            print('Target group exists, deleting old group and create new group...')
            response = self.parent.elbv2.describe_target_groups( Names=[ self.target_group_name() ] )
            self.parent.elbv2.delete_target_group(TargetGroupArn=response['TargetGroups'][0]['TargetGroupArn'])

            self.create_target_group()

    def delete_target_group(self):
        if self.target_group_arn:
            print('Delete target group')
            #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.delete_target_group
            self.parent.elbv2.delete_target_group(TargetGroupArn=self.target_group_arn)
            self.target_group_arn = None

    def wait_for_group(self):
        #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Waiter.TargetInService
        waiter = self.parent.elbv2.get_waiter('target_in_service')
        waiter.wait( TargetGroupArn=self.target_group_arn, WaiterConfig={ 'MaxAttempts': 60 } ) # waits 15 minutes, then throws an error

if __name__ == '__main__':
    manager = AmazonManager()

    try:
        manager.setup()
        print(f'Your load balancer is deployed at {manager.dns_name}.')
        i = input('Press ENTER to quit.')
    finally:
        manager.shutdown()
