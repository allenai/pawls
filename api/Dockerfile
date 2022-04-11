FROM python:3.8.12

# installing rust to huggingface tokenizers
WORKDIR /tmp
RUN curl https://sh.rustup.rs -sSf > rustup.sh
RUN chmod 755 rustup.sh
RUN ./rustup.sh -y --default-toolchain 1.59
RUN rm /tmp/rustup.sh
ENV PATH="/root/.cargo/bin:${PATH}"

# Setup a spot for the api code
WORKDIR /usr/local/src/skiff/app/api

ARG GITHUB_ACCESS_TOKEN

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel
COPY api/requirements.txt .

RUN pip install -r requirements.txt


# dependecies for MMDA; we need to install them here cuz
# they are not version-locked on github
RUN apt-get update && \
    apt-get install -y curl ffmpeg libsm6 libxext6 poppler-utils
RUN pip install --upgrade torch==1.9.0
RUN pip install --upgrade torchvision==0.10.0
RUN pip install PyPDF2==1.26.0
RUN pip install layoutparser==0.3.2
RUN pip install transformers==4.5
RUN pip install vila==0.2.1

# Installing MMDA
RUN pip install 'mmda[lp_predictors,vila_predictors] @ https://github.com/allenai/mmda/archive/refs/tags/0.0.5.zip'

# additional package for for app/mmda_utils.py
RUN pip install PyPDF2==1.26.0

# avoid unnecessary forking with the huggingface tokenizer
ENV TOKENIZERS_PARALLELISM="false"

########## COPYING SOURCE CODE FROM HERE ON ##########

# Copy over the source code
COPY api/app app/
COPY api/config config/
COPY api/main.py main.py

# Kick things off
ENTRYPOINT [ "uvicorn" ]
CMD ["main:app", "--host", "0.0.0.0"]