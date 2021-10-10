from loadtest import SimpleLogger, LoadTester
import os
from metric_downloader import MetricsDownloader
import time


def benchmark(url, logger):
    paths = [ '/cluster1', '/cluster2' ]

    for path in paths:
        cluster = url + path
        tester = LoadTester(cluster, logger)
        logger.log("Starting benchmark for {}".format(url))
        tester.benchmark()
        logger.log('Benchmark done')


def createOutputDir():
    outputDir = os.path.join(os.getcwd(), 'docker-output/')
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)
    return outputDir

def main():
    url = os.getenv("AWS_URL")
    outputDir = createOutputDir()
    logger = SimpleLogger(os.path.join(outputDir, 'log.txt'))

    if url is None:
        logger.log("ERROR: No AWS_URL env variable specified.")
        return
  
    benchmark(url, logger)
    logger.log('Benchmark done, waiting for metrics to be updated...')
    time.sleep(60)
    logger.log('Downloading metrics...')
    metrics = MetricsDownloader(os.path.join(outputDir, 'images/'))
    metrics.getMetricsForClusters()
    metrics.getELBMetrics()
    logger.log('Done')
    

if __name__ == '__main__':
    main()