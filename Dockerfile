FROM ubuntu:18.04

LABEL Auther="wgpsec"
LABEL Mail="admin@wgpsec.org"
LABEL Github="https://github.com/wgpsec/DBJ"

ADD . /DBJ/
ADD start.sh /
RUN sed -i s@/archive.ubuntu.com/@/mirrors.aliyun.com/@g /etc/apt/sources.list
RUN apt-get update
RUN apt-get -o Acquire::BrokenProxy="true" -o Acquire::http::No-Cache="true" -o Acquire::http::Pipeline-Depth="0" -y install  python3 python3-pip mongodb redis-server
RUN pip3 install -r /DBJ/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

WORKDIR /DBJ/
ENV LC_ALL=de_DE.utf-8
ENV LANG=de_DE.utf-8
RUN chmod +x start.sh
EXPOSE 5000
CMD /start.sh
