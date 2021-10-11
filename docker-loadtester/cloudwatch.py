import json

class MetricWidgetOptions:
    def __init__(self, metrics, title, statType = 'Average'):
        self.metrics = [metric.toArray() for metric in metrics]
        self.title = title
        self.view = 'timeSeries'
        self.stat = statType
        self.period = 60
        self.stacked = False
        self.yAxis = { 'left': { 'min': 0} }
        self.region = 'us-east-1'
        self.liveData = False
        self.start = '-PT30M'
        self.end = 'P0D'
        self.timezone = '-0400'

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=False, indent=4)
        

class MetricWidget:
    def __init__(self, options):
        self.options = options

    def saveImage(self, dest, client):
        response = client.get_metric_widget_image(
            MetricWidget = self.options.toJSON(),
            OutputFormat='png'
        )

        with open(dest, "wb") as file:
                file.write(response['MetricWidgetImage'])


class MetricSource:
    EC2 = 'AWS/EC2'
    APPLICATION_LOAD_BALANCER = 'AWS/ApplicationELB'

class MetricIdentifierType:
    EC2_INSTANCEID = 'InstanceId'
    LOAD_BALANCER = 'LoadBalancer'
    TARGET_GROUP = 'TargetGroup'

class Metric:
    def __init__(self, source, name, identifierType, instanceID, label, *args, yAxisSide = 'left'):
        self.data = [source, name, identifierType, instanceID, *args, { 'label': label, 'yAxis' : yAxisSide }]

    def toJSON(self):
        return json.dumps(self.data)

    def toArray(self):
        return self.data


