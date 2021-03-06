FROM python:3.6-alpine

WORKDIR /
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

WORKDIR /app
COPY job-service.py ./
COPY start-worker.sh ./

ENTRYPOINT ["./start-worker.sh"]
