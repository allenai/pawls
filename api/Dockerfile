FROM python:3.7.2

# Setup a spot for the api code
WORKDIR /usr/local/src/skiff/app/api

ARG GITHUB_ACCESS_TOKEN

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel
COPY requirements.txt .
RUN pip install -r requirements.txt

# This will live here, separately, because installing it via requirements.txt makes
# pip try to install it via a binary wheel, which is not supported by the openapi client
# generator which was used to create this api. The install doesn't fail (it installs via
# a method that will be deprecated in some future pip version), but it makes a lot of scary
# noise in the build.
RUN pip install git+https://${GITHUB_ACCESS_TOKEN}@github.com/allenai/s2-pdf-structure-service@master#egg=pkg&subdirectory=clients/python

# Copy over the source code
COPY app app/
COPY main.py main.py

# Kick things off
ENTRYPOINT [ "uvicorn" ]
CMD ["main:app", "--host", "0.0.0.0"]
