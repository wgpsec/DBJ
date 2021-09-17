FROM centos:latest

LABEL Auther="wgpsec"
LABEL Mail="admin@wgpsec.org"
LABEL Github="https://github.com/wgpsec/DBJ"
LABEL Build="xrsec"

# ADD . /DBJ/

RUN mkdir /tmp/dbj \
    # MongoDB install
    && echo "[mngodb-org]" > /etc/yum.repos.d/mongodb.repo \
    && echo "name=MongoDB Repository" >> /etc/yum.repos.d/mongodb.repo \
    && echo "baseurl=http://mirrors.aliyun.com/mongodb/yum/redhat/7Server/mongodb-org/4.0/x86_64/" >> /etc/yum.repos.d/mongodb.repo \
    && echo "gpgcheck=0" >> /etc/yum.repos.d/mongodb.repo \
    && echo "enabled=1" >> /etc/yum.repos.d/mongodb.repo \
    # install 
    && yum makecache && yum update -y && yum upgrade -y \
    && yum -y install yum-utils zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel libffi-devel \
    wget gcc make redis ncurses git mongodb-org \
    # Python
    && wget -O /tmp/dbj/Python-3.9.7.tgz https://www.python.org/ftp/python/3.9.7/Python-3.9.7.tgz \
    && tar xf /tmp/dbj/Python-3.9.7.tgz -C /tmp/dbj/ \ 
    && cd /tmp/dbj/Python-3.9.7 && ./configure && make && make install \
    && ln -sf /usr/local/bin/python3.9 /usr/bin/python \
    && wget -O /tmp/dbj/get-pip.py https://bootstrap.pypa.io/get-pip.py \
    && python /tmp/dbj/get-pip.py -i https://pypi.tuna.tsinghua.edu.cn/simple/ \
    && pip install Flask \
    && git clone https://github.com/wgpsec/DBJ.git /DBJ/ \
    && pip install -r /DBJ/requirements.txt \
    && chmod 777 /DBJ/dbj.sh


WORKDIR /DBJ/
ENV LC_ALL=de_DE.utf-8
ENV LANG=de_DE.utf-8
ENV user=admin
ENV pass=admin
ENV hook=http://localhost
EXPOSE 5000

CMD ["mongod","-f", "/etc/mongodb.conf"]
CMD ["redis-server"]
CMD ["/DBJ/dbj.sh"]
