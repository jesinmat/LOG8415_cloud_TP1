from cloudwatch import Metric, MetricWidgetOptions, MetricWidget, MetricSource, MetricIdentifierType
import os
import boto3

class MetricsDownloader:
    def __init__(self, workdir):
        self.directory = workdir
        self.cloudwatch = boto3.client('cloudwatch')

    def downloadMetricsWidget(self, widgetOptions, directory, name):
        MetricWidget(widgetOptions).saveImage(os.path.join(directory, f'{name}.png'), self.cloudwatch)

    def getImportantMetrics(self, directory, instanceID):
        cpuutil = Metric(MetricSource.EC2, 'CPUUtilization', MetricIdentifierType.EC2_INSTANCEID, instanceID, 'CPU Usage', 'right')
        netin = Metric(MetricSource.EC2, 'NetworkIn', MetricIdentifierType.EC2_INSTANCEID, instanceID, 'Network in')
        netout = Metric(MetricSource.EC2, 'NetworkOut', MetricIdentifierType.EC2_INSTANCEID, instanceID, 'Network out')
        opts = MetricWidgetOptions([cpuutil, netin, netout], "CPU and Network usage")
        self.downloadMetricsWidget(opts, directory, '1-cpu-network')

    def getMetricsForInstance(self, directory, instanceID):
        self.getImportantMetrics(directory, instanceID)

        availableMetrics = [ 'CPUCreditUsage', 'CPUCreditBalance', 'CPUSurplusCreditBalance', 'NetworkPacketsIn',
                            'NetworkPacketsOut', 'DiskReadBytes', 'DiskWriteBytes', 'DiskReadOps', 'DiskWriteOps',
                            'MetadataNoToken', 'StatusCheckFailed_System', 'StatusCheckFailed_Instance', 'StatusCheckFailed']

        for metric in availableMetrics:
            opts = MetricWidgetOptions([Metric(MetricSource.EC2, metric, MetricIdentifierType.EC2_INSTANCEID, instanceID, metric)], f"Graph of {metric}")
            self.downloadMetricsWidget(opts, directory, metric)


    def getMetricsForInstances(self, directory, instanceIDs):
        for id in instanceIDs:
            instanceDir = os.path.join(directory, id)
            if not os.path.exists(instanceDir):
                os.makedirs(instanceDir)
            self.getMetricsForInstance(instanceDir, id)

    def getMetricsForClusters(self):
        clusters = self.getTargetGroups()
        for cluster in clusters:
            clusterDir = os.path.join(self.directory, cluster['name'])
            if not os.path.exists(clusterDir):
                os.makedirs(clusterDir)
            self.getMetricsForInstances(clusterDir, cluster['instances'])

    def getTargetGroups(self):
        client = boto3.resource('ec2')
        ans = []

        for i in range(1,3):
            response = client.instances.filter( Filters=[{'Name': 'tag:Cluster', 'Values': [ str(i) ] }] )
            ans.append({
                'name' : 'cluster' + str(i),
                'instances' : [ instance.id for instance in response ]
            })

        return ans

    def getELBMetrics(self):
        elbId = self.getELBId()
        dir = os.path.join(self.directory, 'load-balancer')
        if not os.path.exists(dir):
                os.makedirs(dir)
        availableMetrics = ['ConsumedLCUs' ,'ProcessedBytes' ,'NewConnectionCount' ,'RuleEvaluations' ,
                        'TargetResponseTime' ,'ActiveConnectionCount' ,'HTTP_Fixed_Response_Count' ,'HTTPCode_ELB_4XX_Count' ,
                        'HTTPCode_Target_2XX_Count' ,'RequestCount' ,'DesyncMitigationMode_NonCompliant_Request_Count']

        for metric in availableMetrics:
            opts = MetricWidgetOptions([Metric(MetricSource.APPLICATION_LOAD_BALANCER, metric, MetricIdentifierType.LOAD_BALANCER, elbId, metric)],
                                        f"Graph of {metric}",
                                        statType='Sum' if metric == 'RequestCount' else 'Average')
            self.downloadMetricsWidget(opts, dir, metric)

    def getELBId(self):
        elbclient = boto3.client('elbv2')
        elbId = 'app/' + elbclient.describe_load_balancers()['LoadBalancers'][0]['LoadBalancerArn'].split('/app/')[1]
        return elbId
