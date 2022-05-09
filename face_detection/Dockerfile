FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get -y install python3-pip
RUN apt-get -y install build-essential
RUN apt-get -y install python-dev
RUN pip3 install --upgrade pip

COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt

RUN apt-get install python3-dev libopencv-dev python3-opencv libatlas-base-dev -y
RUN apt install libopencv-dev python3-opencv

COPY templates ./templates
COPY static ./static
COPY videoapp.py ./videoapp.py
COPY videoapp.ini ./videoapp.ini

ENV LABELLED_STREAM_PORT=8082
ENV PEOPLE_DETECTION_URL='http://[RPI_IP_ADDR]:8082/?action=stream_0'
CMD sed -i "s,labelled_stream_port,${LABELLED_STREAM_PORT},g" ./videoapp.ini;sed -i "s,people_detection_url,${PEOPLE_DETECTION_URL},g" ./templates/index.html; uwsgi --ini videoapp.ini --pyargv ${PEOPLE_DETECTION_URL}

EXPOSE ${LABELLED_STREAM_PORT}
