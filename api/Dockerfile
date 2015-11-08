FROM ubuntu:14.04
MAINTAINER Mitch Anderson <mitch@metauser.net>

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install -y python python-pip python-virtualenv gunicorn libpq-dev python-dev

# Setup flask application
RUN mkdir -p /opt/yoked/api
COPY . /opt/yoked/api/
RUN pip install -r /opt/yoked/api/requirements.txt
WORKDIR /opt/yoked/api

EXPOSE 5000

# Start gunicorn
CMD ["/usr/bin/gunicorn", "-w", "2", "-b", ":3000", "api:app"]
