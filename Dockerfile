FROM arm32v7/ubuntu:bionic AS BASE

RUN apt-get update && \
    # apt-get upgrade -y && \
    apt-get install -y python3-pip sudo && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /ruuvitag
WORKDIR /ruuvitag

COPY setup.py README.md ./
COPY ruuvitag_sensor ruuvitag_sensor

RUN pip3 install -e .

FROM BASE

CMD ["python3", "ruuvitag_sensor", "-s"]
