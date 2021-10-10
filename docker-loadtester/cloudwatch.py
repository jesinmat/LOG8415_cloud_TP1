import boto3
import json

client = boto3.client('cloudwatch')

class MetricWidgetOptions:
    def __init__(self, metrics, title):
        self.metrics = [metric.toArray() for metric in metrics]
        self.title = title
        self.view = 'timeSeries'
        self.stat = 'Maximum'
        self.period = 60
        self.stacked = False
        self.yAxis = { 'left': { 'min': 0} }
        self.region = 'us-east-1'
        self.liveData = False
        self.start = '-PT15M'
        self.end = 'P0D'
        self.timezone = '-0400'

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=False, indent=4)
        

class MetricWidget:
    def __init__(self, options):
        self.options = options

    def saveImage(self, dest):
        response = client.get_metric_widget_image(
            MetricWidget = self.options.toJSON(),
            OutputFormat='png'
        )

        with open(dest, "wb") as file:
                file.write(response['MetricWidgetImage'])


class Metric:
    def __init__(self, name, instanceID, label, yAxisSide = 'left'):
        self.data = ['AWS/EC2', name, 'InstanceId', instanceID, { 'label': label, 'yAxis' : yAxisSide }]

    def toJSON(self):
        return json.dumps(self.data)

    def toArray(self):
        return self.data


def main():
    cpuutil = Metric('CPUUtilization', 'i-027cd9d606db7e17a', 'CPU Usage', 'right')
    netin = Metric('NetworkIn', 'i-027cd9d606db7e17a', 'Net in')
    opts = MetricWidgetOptions([cpuutil, netin], "Testing title")
    MetricWidget(opts).saveImage('test.png')

main()
