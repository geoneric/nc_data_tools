FROM geoneric/nc_base:latest

MAINTAINER Kor de Jong <k.dejong@geoneric.eu>

RUN set -x && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        libgdal-dev \
        gdal-bin && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /
RUN pip install numpy==1.12.0 && \
    pip install -r requirements.txt

COPY cmd.sh server.py server_development.py server_production.py /
COPY nc_data_tools /nc_data_tools
COPY test /test

CMD ["/cmd.sh"]
