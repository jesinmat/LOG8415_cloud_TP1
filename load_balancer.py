import boto3
from constants import IMAGE_ID, KEYPAIR_NAME, SECURITY_GROUP, VPC_ID
import aws_script

class AmazonManager:
    def __init__(self, keypair = KEYPAIR_NAME):
        self.ec2_resource = boto3.resource('ec2')
        self.ec2 = boto3.client('ec2')
        self.elbv2 = boto3.client('elbv2')
        self.keypair = keypair

class SubCluster:
    def __init__(self, parent, cluster_nb, instanceType = 't2.micro'):
        self.parent = parent
        self.instance_type = instanceType
        self.cluster_nb = cluster_nb

    def create_instances(self, nb_instances = 1, imageId = IMAGE_ID, securityGroup = SECURITY_GROUP, userScript = '', zone = 'us-east-1a'):
        return aws_script.create()

    def create_target_group(self):
        return parent.ec2.create_target_group(
            Name=f'cluster-{self.cluster_nb}',
            Protocol='HTTP',
            ProtocolVersion='HTTP1',
            Port=80,
            VpcId=VPC_ID,
            HealthCheckEnabled=True,
            HealthCheckPath=f'/cluster{self.cluster_nb}',
            TargetType='instance',
            Tags=[
                {
                    'Key': 'Name',
                    'Value': f'target-group-{self.cluster_nb}'
                },
            ]
        )

    def create_load_balancer(self):
        #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.create_load_balancer
        return client.create_load_balancer(
            Name='insert-uncreative-name-here',
            SecurityGroups=[
                SECURITY_GROUP,
            ],
            Scheme='internet-facing',
            Type='application',
            IpAddressType='ipv4'
        )

def create_group_with_instances(cluster_nb, instance_type, client):
    targets = []

    resp = create_instances(cluster_nb, nb_instances=5, instanceType = instance_type)
    
    ids = [ instance['InstanceId'] for instance in resp['Instances'] ]
    # Reference: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.register_targets
    for i in ids:
        targets.append({
            'Id': i,
            'Port': 80,
            'AvailabilityZone': 'all' # TODO: should it really be 'all' ?
        })

    target_group = create_target_group(f'cluster-{cluster_nb}', client)
    target_group_arn = target_group['TargetGroups'][0]['TargetGroupArn']

    elbv2.register_targets(
            TargetGroupArn=target_group_arn,
            Targets=targets
        )
    return target_group_arn

if __name__ = '__main__':
    elbv2 = boto3.client('elbv2')
    target_group_arns = []

    load_balancer = create_load_balancer(elbv2)
    load_balancer = load_balancer['LoadBalancers'][0]['LoadBalancerArn']

    for cluster_nb, instance_type in enumerate(['m4.large', 't2.xlarge']):
        target_group_arns.append( create_group_with_instances(cluster_nb, instance_type) )

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.create_listener
    listener = elbv2.create_listener(
        LoadBalancerArn=load_balancer,
        Protocol='HTTP',
        Port=80,
        DefaultActions=[
            {
                'Type': 'forward',
                'TargetGroupArn': target_group_arns[0],
            },
        ]
    )

    listener = listener['Listeners'][0]['ListenerArn']

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.create_rule
    elbv2.create_rule(
        ListenerArn=listener,
        Conditions=[
            {
                'Field': 'path-pattern',
                'Values': [ '/cluster2' ]
            },
        ],
        Priority=1,
        Actions=[
            {
                'Type': 'forward',
                'TargetGroupArn': target_group_arns[1],
            },
        ]
    )
