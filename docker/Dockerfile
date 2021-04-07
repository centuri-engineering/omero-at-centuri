FROM openmicroscopy/omero-server:latest

RUN adduser importer
RUN usermod -aG omero-server importer
RUN chgrp -r importer /OMERO/ManagedRepository/
RUN chmod g+rws importer /OMERO/ManagedRepository/

USER importer
RUN echo "PATH=/opt/omero/server/OMERO.server/bin/:$PATH" >> $HOME/.bashrc
RUN echo "source /opt/omero/server/venv3/bin/activate" >> $HOME/.bashrc
RUN echo "PYTHONPATH=/home/importer/impomero-main/:$PYTHONPATH" >> $HOME/.bashrc
RUN source .bashrc

RUN wget https://github.com/centuri-engineering/impomero/archive/refs/heads/main.zip
RUN unzip main.zip
RUN cd impomero-main
RUN python -m pip install --user -r requirements.txt
