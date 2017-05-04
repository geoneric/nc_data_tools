FROM posbank.geoneric.eu:5000/nca/nc_base:latest

MAINTAINER Kor de Jong <k.dejong@geoneric.eu>

RUN \
    cd /opt && \
    wget --progress=bar:force https://cmake.org/files/v3.5/cmake-3.5.2-Linux-x86_64.tar.gz && \
    tar zxf cmake-3.5.2-Linux-x86_64.tar.gz && \
    ln -s cmake-3.5.2-Linux-x86_64 cmake && \
    git clone --recursive https://github.com/geoneric/peacock.git /tmp/peacock && \
    cd /tmp/peacock && \
    git checkout 208bd10182fa32f45a6d57abd6f27841fb88b07d && \
    mkdir /tmp/build && \
    cd /tmp/build && /opt/cmake/bin/cmake \
        -Dpeacock_prefix=/usr/local \
        -Dbuild_gdal=true \
            -Dgdal_version=1.11.5 \
            -Dgdal_build_python_package=FALSE \
            -Dgdal_build_ogr=TRUE \
        /tmp/peacock && \
    /opt/cmake/bin/cmake --build /tmp/build --target all && \
    rm -fr /tmp/build

COPY requirements.txt /

RUN \
    pip install numpy==1.12.0 && \
    GDAL_CONFIG=/usr/local/linux/linux/gcc-4/x86_64/bin/gdal-config \
        pip install -r requirements.txt

ENV PATH="/usr/local/linux/linux/gcc-4/x86_64/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/linux/linux/gcc-4/x86_64/lib:${LD_LIBRARY_PATH}"

COPY cmd.sh server.py /
COPY nc_data_tools /nc_data_tools
COPY test /test

CMD ["/cmd.sh"]
