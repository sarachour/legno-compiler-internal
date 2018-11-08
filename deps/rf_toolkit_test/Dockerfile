FROM ubuntu:latest
MAINTAINER Sara Achour

RUN apt-get update
RUN apt-get install -y python python-pip wget python-tk
RUN apt-get install -y ngspice
RUN pip install pyspice 
ADD . /home/sim

WORKDIR /home
