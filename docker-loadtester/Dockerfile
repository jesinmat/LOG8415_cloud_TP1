FROM python:3.8.12-slim

ADD loadtest.py /

RUN pip install aiohttp

ENTRYPOINT [ "python", "./loadtest.py" ]
