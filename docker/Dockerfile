FROM openmicroscopy/omero-server:latest

USER root

# https://docs.openmicroscopy.org/omero/5.6.3/sysadmins/in-place-import.html
RUN adduser importer
RUN usermod -aG omero-server importer
RUN chgrp -R importer /OMERO/ManagedRepository/
RUN chmod -R g+rws /OMERO/ManagedRepository/

USER importer
ENV PATH /opt/omero/server/OMERO.server/bin/:$PATH
ENV PATH /opt/omero/server/venv3/bin:$PATH

ENV PYTHONPATH /home/importer/.local/lib/python3.6/site-packages:/home/importer/impomero-main/:$PYTHONPATH
RUN echo "source /opt/omero/server/venv3/bin/activate" >> /home/importer/.bashrc
WORKDIR /home/importer
RUN echo "Python version: "
RUN python  -c "import sys; print(sys.version)"

RUN wget https://github.com/centuri-engineering/impomero/archive/refs/heads/main.zip
RUN unzip main.zip
WORKDIR impomero-main
RUN python -m pip install --user -r requirements.txt

USER omero-server
WORKDIR /opt/omero
