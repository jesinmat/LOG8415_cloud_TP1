from loadtest import SimpleLogger, LoadTester
from cloudwatch import Metric, MetricWidgetOptions, MetricWidget
import os
import boto3


def benchmark(url, logger):
    #paths = [ '/cluster1', '/cluster2' ]
    paths = [ '/' ]

    for path in paths:
        cluster = url + path
        tester = LoadTester(cluster, logger)
        logger.log("Starting benchmark for {}".format(url))
        tester.benchmark()
        logger.log('Benchmark done')


def downloadMetricsWidget(widgetOptions, directory, name):
    MetricWidget(widgetOptions).saveImage(os.path.join(directory, f'{name}.png'))

def getImportantMetrics(directory, instanceID):
    cpuutil = Metric('CPUUtilization', instanceID, 'CPU Usage', 'right')
    netin = Metric('NetworkIn', instanceID, 'Network in')
    netout = Metric('NetworkOut', instanceID, 'Network out')
    opts = MetricWidgetOptions([cpuutil, netin, netout], "CPU and Network usage")
    downloadMetricsWidget(opts, directory, '1-cpu-network')

def getMetrics(directory, instanceID):
    getImportantMetrics()

    availableMetrics = [ 'CPUCreditUsage', 'CPUCreditBalance', 'CPUSurplusCreditBalance', 'NetworkPacketsIn',
                        'NetworkPacketsOut', 'DiskReadBytes', 'DiskWriteBytes', 'DiskReadOps', 'DiskWriteOps',
                        'MetadataNoToken', 'StatusCheckFailed_System', 'StatusCheckFailed_Instance', 'StatusCheckFailed']

    for metric in availableMetrics:
        opts = MetricWidgetOptions([Metric(metric, instanceID, metric)], f"Graph of {metric}")
        downloadMetricsWidget(opts, directory, metric)
    

def get_target_groups():
    client = boto3.client('ec2')
    ans = []

    for i in range(2):
        response = boto3.instances.filter( Filters=[{'Name': 'tag:Cluster', 'Values': [ str(i) ] }] )

        ans.append({
            'name' : 'cluster' + str(i),
            'instances' : [ instance.id for instance in response ]
        })

    return ans

def main():
    import os
    url = os.getenv("AWS_URL")
    logger = SimpleLogger('log.txt')

    if url is None:
        logger.log("ERROR: No AWS_URL env variable specified.")
        return
  
    #benchmark(url, logger)
    cwd = os.getcwd()
    getMetrics(os.path.join(cwd, 'images/'), 'i-027cd9d606db7e17a')
    

main()