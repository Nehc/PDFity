FROM ubuntu:latest

ENV DEBIAN_FRONTEND noninteractive

LABEL maintainer="Nehcy <cibershaman@gmail.com>"

ARG NB_USER="wald"
ARG NB_UID="1000"
ARG NB_GID="100"
ARG NB_DIR="work"

RUN apt-get update --yes && apt-get upgrade --yes && \
    apt-get install --yes software-properties-common 

RUN add-apt-repository ppa:alex-p/jbig2enc && apt-get update --yes && \
    apt-get install --yes --no-install-recommends \
    locales poppler-utils swig3.0 build-essential \
    python-is-python3 python3-dev python3-pip \
    ocrmypdf wkhtmltopdf jbig2enc optipng && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=en_US.UTF-8

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8
ENV LC_ALL en_US.UTF-8

ADD https://github.com/tesseract-ocr/tessdata/raw/main/rus.traineddata \
    /usr/share/tesseract-ocr/4.00/tessdata/

# Create NB_USER with name NB_USER user with UID=1000 and in the 'users' group
#chmod g+w /etc/passwd && \

RUN useradd -l -m -s /bin/bash -N -u "${NB_UID}" "${NB_USER}" # && \
    chown "${NB_USER}:${NB_GID}" "/home/${NB_USER}/"
 
USER "${NB_UID}"

WORKDIR "/home/${NB_USER}/"

ENV PATH="$PATH:/home/${NB_USER}/.local/bin"

COPY requirements.txt ./

RUN python -m pip install --upgrade pip wheel && \
    pip install --user -r requirements.txt && \
    python -m pip cache purge

WORKDIR "./${NB_DIR}"

COPY app.py ./
ADD https://github.com/Nehc/OCRmyPDF_tgtqdm/blob/main/plugin.py ./
ADD https://github.com/bakwc/JamSpell-models/raw/master/ru.tar.gz ./

# Configure container startup: if not use compose
# if use doker standalone uncomemnt next 
#ENTRYPOINT ["python", "app.py"]
