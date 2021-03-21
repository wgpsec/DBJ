FROM ubuntu:18.04

RUN sed -i s@/archive.ubuntu.com/@/mirrors.aliyun.com/@g /etc/apt/sources.list
RUN apt-get update
RUN apt-get -y install  python3
RUN apt-get -y install  python3-pip
RUN apt -y install mongodb
RUN apt -y install redis
ADD requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
ADD . /DBJ/
WORKDIR /DBJ/
RUN chmod +x start.sh
RUN /DBJ/start.sh