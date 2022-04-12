FROM python:3.8.12


# Setup a spot for the api code
WORKDIR /usr/local/src/skiff/app/api

ARG GITHUB_ACCESS_TOKEN

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel
COPY requirements.txt .

RUN pip install -r requirements.txt

########## COPYING SOURCE CODE FROM HERE ON ##########

# Copy over the source code
COPY app app/
COPY config config/
COPY main.py main.py

# Kick things off
ENTRYPOINT [ "uvicorn" ]
CMD ["main:app", "--host", "0.0.0.0"]