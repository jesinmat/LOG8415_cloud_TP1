import boto3
from constants import IMAGE_ID, KEYPAIR_NAME, SECURITY_GROUP, VPC_ID
import aws_script
import threading
import random

vocals = 'aeiou'
consonants = 'bcdfghjklmnpqrstvwxz'
def create_random_name():
    ans = ''
    for i in range(3):
        ans += consonants[random.randint(0,len(consonants)-1)] + vocals[random.randint(0, len(vocals)-1)]
    return ans

class AmazonManager:
    INSTANCE_TYPE_LIST = ['m4.large', 't2.xlarge']

    def __init__(self, keypair = KEYPAIR_NAME):
        self.ec2_resource = boto3.resource('ec2')
        self.ec2 = boto3.client('ec2')
        self.elbv2 = boto3.client('elbv2')
        self.keypair = keypair
        self.children = [None, None]
        self.load_balancer_arn = None
        self.listener_arn = None
        self.rule_arn = None
        self.dns_name = None
        self.batch_name = create_random_name()
        print('Starting batch ' + self.batch_name)

        self.setup()

    def setup(self):
        threads = []
        for cluster_nb, instance_type in enumerate(AmazonManager.INSTANCE_TYPE_LIST):
            self.children[cluster_nb] = SubCluster(self, cluster_nb+1, instance_type)
            thread = threading.Thread(target=self.children[cluster_nb].setup)
            thread.start()
            threads.append( thread )
            
        self.create_load_balancer()

        for thread in threads:
            thread.join()

        self.create_listener(self.children[0])
        self.create_rule(self.children[1])

        print('Waiting for heath checks (might take ~5 minutes)...')
        for child in self.children:
            child.wait_for_group()
        print('Everything set up!')

    def shutdown(self):
        self.delete_rule()
        self.delete_listener()

        self.delete_load_balancer()

        for child in self.children:
            child.shutdown()

    def create_load_balancer(self):
        #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.create_load_balancer
        print('Create load balancer')
        resp = self.elbv2.create_load_balancer(
            Name='load-balancer-version-one',
            Subnets = [subnet.id for subnet in self.ec2_resource.subnets.filter()],
            SecurityGroups=[ SECURITY_GROUP ],
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

    def create_listener(self, child):
        print('Create listener')
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.create_listener
        listener = self.elbv2.create_listener(
            LoadBalancerArn=self.load_balancer_arn,
            Protocol='HTTP',
            Port=80,
            DefaultActions=[
                {
                    'Type': 'forward',
                    'TargetGroupArn': child.target_group_arn,
                },
            ]
        )
        self.listener_arn = listener['Listeners'][0]['ListenerArn']

    def delete_listener(self):
        if self.listener_arn:
            print('Delete listener')
            #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.delete_listener
            self.elbv2.delete_listener(ListenerArn=self.listener_arn)

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
            Priority=1,
            Actions=[
                {
                    'Type': 'forward',
                    'TargetGroupArn': child.target_group_arn,
                },
            ]
        )
        self.rule_arn = resp['Rules'][0]['RuleArn']

    def delete_rule(self):
        if self.rule_arn:
            print('Delete rule')
            #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.delete_listener
            self.elbv2.delete_rule(RuleArn=self.rule_arn)

class SubCluster:
    def __init__(self, parent, cluster_nb, instanceType = 't2.micro'):
        self.parent = parent
        self.instance_type = instanceType
        self.cluster_nb = cluster_nb
        self.instance_ids = []
        self.target_group_arn = None

    def setup(self):
        try:
            self.create_instances()

            self.create_target_group()
            
            # Reference: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.register_targets
            targets = [ { 'Id': i, 'Port': 80 } for i in self.instance_ids]

            self.parent.elbv2.register_targets(
                    TargetGroupArn=self.target_group_arn,
                    Targets=targets
                )
        except Exception as x:
            print(x)
            self.shutdown()

    def shutdown(self):
        self.delete_target_group()

        aws_script.terminate(self.instance_ids)

    def htmlpath(self):
        return f'/cluster{self.cluster_nb}'

    def create_instances(self, imageId = IMAGE_ID, securityGroup = SECURITY_GROUP, zone = 'us-east-1a'):
        print('Create 4 instances')

        with open('flask_deploy.sh', 'r') as file:
            script = file.read() % self.cluster_nb

        resp = aws_script.create(name = f'{self.parent.batch_name}-{self.cluster_nb}-{self.instance_type}-instance', 
            availabilityZone = zone, nbInstances=4, userScript=script, instanceType = self.instance_type)
        self.instance_ids = [ instance['InstanceId'] for instance in resp['Instances'] ]

        waiter = self.parent.ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=self.instance_ids)

    def create_target_group(self):
        print('Create target group')
        resp = self.parent.elbv2.create_target_group(
            Name=f'cluster-{self.cluster_nb}',
            Protocol='HTTP',
            ProtocolVersion='HTTP1',
            Port=80,
            VpcId=VPC_ID,
            HealthCheckEnabled=True,
            HealthCheckPath=self.htmlpath(),
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

    def delete_target_group(self):
        if self.target_group_arn:
            print('Delete target group')
            #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.delete_target_group
            resp = self.parent.elbv2.delete_target_group(TargetGroupArn=self.target_group_arn)

    def wait_for_group(self):
        #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Waiter.TargetInService
        waiter = self.parent.elbv2.get_waiter('target_in_service')
        waiter.wait( TargetGroupArn=self.target_group_arn )

if __name__ == '__main__':
    manager = AmazonManager()

    print(f'Your load balancer is deployed at {manager.dns_name}.')
    i = input('Press ENTER to quit.')

    manager.shutdown()
