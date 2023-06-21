FROM alpine:3.17

ARG USER_UID=1000
ARG USER_GID=1000

RUN apk add \
    build-base \
    cargo \
    chromium \
    chromium-chromedriver \
    dbus-x11 \
    font-bakoma-ttf \
    gcc \
    gfortran \
    git \
    gvfs \
    imagemagick \
    inkscape \
    linux-headers \
    openblas \
    py3-pandas \
    py3-pip \
    py3-pyqt5-sip \
    py3-qt5 \
    py3-scipy \
    py3-zstandard \
    python3 \
    python3-dev \
    shadow \
    sudo \
    texlive-full \
    wget

COPY requirements.txt /tmp
RUN pip3 install -r /tmp/requirements.txt

# create user "user"
RUN groupadd -g ${USER_GID} user
RUN useradd -s /bin/bash -u ${USER_UID} -g ${USER_GID} -m user
WORKDIR "/home/user"

USER user
ENV PATH="${PATH}:/home/user/.cargo/bin"
RUN cargo install svgcleaner

USER root
RUN fc-cache -fv
ENV BASEDIR="/home/user/hoedur-experiments"
COPY entry.sh /entry.sh
ENTRYPOINT [ "/entry.sh" ]
