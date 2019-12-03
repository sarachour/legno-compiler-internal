FROM ubuntu:18.04

RUN apt-get update
RUN apt-get install -y python3-pip libatlas-base-dev git graphviz
ADD keys/ /ssh-keys
RUN eval `ssh-agent` && \
    mkdir ~/.ssh && \ 
    cp /ssh-keys/* ~/.ssh/ && \
    ssh-add ~/.ssh/aec_key && \
    ssh-keyscan github.com >> ~/.ssh/known_hosts && \ 
    echo yes yes | git clone git@github.com:sendyne/legno-compiler.git /root/legno-compiler
WORKDIR /root/legno-compiler
RUN git checkout artifact
RUN pip3 install -r packages-legno.list
RUN pip3 install -r packages-grendel.list
ADD state.db device-state/state.db
ADD run_all.py .
RUN cp util/config_local.py util/config.py
RUN make models-maxfit
RUN make models-minerr
