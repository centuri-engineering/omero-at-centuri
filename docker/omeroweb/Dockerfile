# https://github.com/ome/omero-web-docker/blob/master/Dockerfile
FROM openmicroscopy/omero-web-standalone:5

USER root
RUN yum install -y \
    ffmpeg \
    wget \
    unzip \
    scl-utils \
    scl-utils-build \
    centos-release-scl

RUN yum install -y \
    devtoolset-8-gcc \
    devtoolset-8-gcc-c++

RUN scl enable devtoolset-8 -- bash
ENV PATH=/opt/rh/devtoolset-8/root/usr/bin/:$PATH
#ENV LD_LIBRARY_PATH=/opt/rh/devtoolset-8/root/usr/bin/
# TODO: change "@/sbin/ldconfig" to "/sbin/ldconfig" in /etc/nvidia-container-runtime/config.toml



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
