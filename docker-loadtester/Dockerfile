FROM python:3.8.12-slim

ADD loadtest.py /
ADD launch.py /
ADD cloudwatch.py /
ADD metric_downloader.py /

RUN pip -qqq install aiohttp boto3

ENTRYPOINT [ "python", "./launch.py" ]
