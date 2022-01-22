FROM ubuntu:20.04

RUN apt-get update \
    && DEBIAN_FRONTEND="noninteractive" apt-get install -y --no-install-recommends \
        wget gnupg sudo iproute2 ca-certificates


RUN echo "deb http://www.inetsim.org/debian/ binary/" > /etc/apt/sources.list.d/inetsim.list
RUN wget -O - https://www.inetsim.org/inetsim-archive-signing-key.asc | apt-key add -

RUN apt-get update \
    && DEBIAN_FRONTEND="noninteractive" apt-get install -y --no-install-recommends \
        inetsim 

COPY inetsim.conf /etc/inetsim/inetsim.conf
ENTRYPOINT 'inetsim'