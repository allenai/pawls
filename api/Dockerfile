FROM python:3.8.12

# installing rust to huggingface tokenizers
WORKDIR /tmp
RUN curl https://sh.rustup.rs -sSf > rustup.sh
RUN chmod 755 rustup.sh
RUN ./rustup.sh -y
RUN rm /tmp/rustup.sh
ENV PATH="/root/.cargo/bin:${PATH}"

# Setup a spot for the api code
WORKDIR /usr/local/src/skiff/app/api

ARG GITHUB_ACCESS_TOKEN

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel
COPY api/requirements.txt .

RUN pip install -r requirements.txt

# # we need to install the pawls CLI, but we do so
# # by first moving the code to a temp location.
# COPY cli /tmp/pawls-cli/
# RUN pip install -r /tmp/pawls-cli/requirements.txt
# RUN pip install /tmp/pawls-cli

# dependecies for MMDA
RUN apt-get update && \
    apt-get install -y curl ffmpeg libsm6 libxext6 poppler-utils

# Installing MMDA
RUN pip install 'mmda[lp_predictors,vila_predictors] @ git+https://github.com/allenai/mmda.git'

ENV TOKENIZERS_PARALLELISM="false"

########## COPYING SOURCE CODE FROM HERE ON ##########

# Copy over the source code
COPY api/app app/
COPY api/config config/
COPY api/main.py main.py

# Kick things off
ENTRYPOINT [ "uvicorn" ]
CMD ["main:app", "--host", "0.0.0.0"]
