# https://github.com/ome/omero-web-docker/blob/master/Dockerfile
FROM openmicroscopy/omero-web-standalone:5

USER root
RUN yum install -y \
    ffmpeg \
    wget \
    unzip

RUN yum groupinstall "Development Tools" -y

RUN yum install -y \
    gmp-devel \
    mpfr-devel \
    libmpc-devel

RUN mkdir /gcc && \
    cd /gcc && \
    wget https://ftp.mpi-inf.mpg.de/mirrors/gnu/mirror/gcc.gnu.org/pub/gcc/snapshots/8.5.0-RC-20210507/gcc-8.5.0-RC-20210507.tar.gz && \
    tar -zxf gcc-8.5.0-RC-20210507.tar.gz && \
    cd gcc-8.5.0-RC-20210507 && \
    ./configure --disable-multilib --enable-languages=c,c++ --prefix=/opt/gcc8 && \
        make -j5 && \
        make -j install

ENV LD_LIBRARY_PATH=/opt/gcc8/lib64/

RUN yum install -y epel-release && \
    yum install -y \
    ocl-icd \
    opencl-headers \
    ocl-icd \
    clinfo && \
    rm -rf /var/cache/yum/*

RUN mkdir -p /etc/OpenCL/vendors && \
    echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd

# nvidia-container-runtime
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility


ENV FIJI_HOME=/usr/local/share/Fiji.app
RUN mkdir $FIJI_HOME
WORKDIR /usr/local/share/
RUN wget https://downloads.imagej.net/fiji/latest/fiji-linux64.zip
RUN unzip fiji-linux64.zip
WORKDIR $FIJI_HOME
RUN ./ImageJ-linux64 --update add-update-site 3Dscript "https://romulus.oice.uni-erlangen.de/updatesite/"
RUN ./ImageJ-linux64 --update add-update-site 3Dscript-server "https://romulus.oice.uni-erlangen.de/imagej/updatesites/3Dscript-server/"
RUN ./ImageJ-linux64 --update update

RUN /opt/omero/web/venv3/bin/python -m pip install omero-3Dscript
USER omero-web
ADD omero-web-apps.omero /opt/omero/web/config/
