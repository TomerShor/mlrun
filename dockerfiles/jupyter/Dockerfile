# Copyright 2023 Iguazio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

ARG MLRUN_PYTHON_VERSION=3.9
ARG MLRUN_UV_IMAGE=ghcr.io/astral-sh/uv:latest

FROM ${MLRUN_UV_IMAGE} AS uv-image

FROM quay.io/mlrun/jupyter-scipy-notebook:python-${MLRUN_PYTHON_VERSION}

USER root
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get -y upgrade && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update  \
    && apt-get install --no-install-recommends -y \
      graphviz \
      curl \
      apt-transport-https \
      unzip \
    && rm -rf /var/lib/apt/lists/*

# Download and install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/

USER $NB_UID

## Install it via mamba to overcome installing jupyterlab not being able to install the latest version
## on the current image distribution.
RUN mamba install --channel conda-forge --yes jupyterlab~=4.3

ARG MLRUN_PIP_VERSION=25.0
RUN python -m pip install --upgrade pip~=${MLRUN_PIP_VERSION} && \
    conda update --all --yes

WORKDIR $HOME

COPY --chown=$NB_UID:$NB_GID ./docs/tutorials $HOME/tutorials
COPY --chown=$NB_UID:$NB_GID ./docs/_static/images/MLRun-logo.png $HOME/_static/images/MLRun-logo.png
COPY --chown=$NB_UID:$NB_GID ./dockerfiles/jupyter/README.ipynb $HOME
COPY --chown=$NB_UID:$NB_GID ./dockerfiles/jupyter/mlrun.env $HOME
COPY --chown=$NB_UID:$NB_GID ./dockerfiles/jupyter/mlce-start.sh /usr/local/bin/mlce-start.sh

ENV UV_SYSTEM_PYTHON=true UV_LINK_MODE=copy

# no-deps to ignore existing dependencies, just add the locked requirements
# mainly because of how the jupyter image is built with conda
# can be removed once we have newer jupyter image
RUN --mount=from=uv-image,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=dockerfiles/jupyter/locked-requirements.txt,target=locked-requirements.txt \
    uv pip install --no-deps --require-hashes -r locked-requirements.txt

# ensure we have the latest source code to be installed
COPY --chown=$NB_UID:$NB_GID . /tmp/mlrun

RUN --mount=from=uv-image,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    cd /tmp/mlrun && uv pip install '.[complete]'

# cleanup, source code is not needed anymore
RUN rm -rf /tmp/mlrun

# This will usually cause a cache miss - so keep it in the last layers
ARG MLRUN_CACHE_DATE=initial

# Use 1.7.x version from mlrun/demos to update the demos(do not update version).
RUN git clone --branch 1.7.x https://github.com/mlrun/demos.git $HOME/demos && \
    ./demos/update_demos.sh --user=jovyan --path=/home/jovyan/demos --no-backup && \
    git clone --branch master https://github.com/mlrun/functions.git $HOME/functions

ENV JUPYTER_ENABLE_LAB=yes \
    MLRUN_HTTPDB__DATA_VOLUME=$HOME/data \
    MLRUN_HTTPDB__DSN='sqlite:////home/jovyan/data/mlrun.db?check_same_thread=false' \
    MLRUN_HTTPDB__LOGS_PATH=$HOME/data/logs \
    MLRUN_ENV_FILE=$HOME/mlrun.env \
    MLRUN_HTTPDB__PORT=8080

# backup home since it will be deleted when using pvc
RUN mkdir data && tar -cvf /tmp/basehome.tar $HOME

# use tini as entrypoint to allow signal handling
# and avoid zombie processes
ENTRYPOINT ["tini", "--"]

CMD echo "1" > "${HOME}/.intdata" && /usr/local/bin/mlce-start.sh
