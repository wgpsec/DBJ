FROM ubuntu:18.04

LABEL Auther="wgpsec"
LABEL Mail="admin@wgpsec.org"
LABEL Github="https://github.com/wgpsec/DBJ"

ADD . /DBJ/

RUN sed -i s@/archive.ubuntu.com/@/mirrors.aliyun.com/@g /etc/apt/sources.list \
    && apt-get update \
    && chmod +x /DBJ/start.sh \
    && apt-get -o Acquire::BrokenProxy="true" -o Acquire::http::No-Cache="true" -o Acquire::http::Pipeline-Depth="0" -y install  python3 python3-pip mongodb redis-server \
    && pip3 install -r /DBJ/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ \
    && mkdir -p /root/.config \
    && cp -r /DBJ/data/.config/nuclei /root/.config/nuclei \
    && chmod +x /DBJ/data/nuclei \
    && ln -s /DBJ/data/nuclei /usr/bin/nuclei

WORKDIR /DBJ/
ENV LC_ALL=de_DE.utf-8
ENV LANG=de_DE.utf-8
EXPOSE 5000

CMD ["/DBJ/start.sh"]
