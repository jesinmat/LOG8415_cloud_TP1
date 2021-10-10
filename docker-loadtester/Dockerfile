FROM python:3.8.12-slim

ADD loadtest.py /
ADD launch.py /
ADD cloudwatch.py /

RUN pip install aiohttp

ENTRYPOINT [ "python", "./loadtest.py" ]
