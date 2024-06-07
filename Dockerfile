FROM docker.io/ubuntu:22.04 AS build_image
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Prague
RUN apt-get update \
    && apt-get install --no-install-recommends --fix-missing -y \
    python3-dev python3-venv python3-pip python3-requests python3-packaging git curl nano jq build-essential apt-transport-https \
    ca-certificates maven openjdk-21-jdk wget default-libmysqlclient-dev pkg-config
ENV PATH /root/.local/bin:/root/.poetry/bin:${PATH}
RUN mkdir -p /root/.local/bin \
    && ln -s $(which python3) /root/.local/bin/python \
    && curl -sSL https://install.python-poetry.org | python3 -
ENV PIP_CACHE_DIR=/cache/pip


# Todo consider clean image and running without necessary dependencies for smaller image...
FROM build_image as cbio_importer

ENV PORTAL_HOME=/cbioportal-core
RUN git clone https://github.com/cBioPortal/cbioportal-core.git "${PORTAL_HOME}" \
    && cd "${PORTAL_HOME}" \
    && mvn -DskipTests clean install

COPY . /cbio_importer
WORKDIR /cbio_importer
RUN poetry install && poetry build
CMD ["bash"]
ENTRYPOINT ["/cbio_importer/cbio_importer/init.sh"]
