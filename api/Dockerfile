FROM python:3.7.2

# Setup a spot for the api code
WORKDIR /usr/local/src/skiff/app/api

ARG GITHUB_ACCESS_TOKEN

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel
COPY requirements.txt .

# The PDF structure service installs via a method that will be deprecated in some future pip version.
# It does install, but it makes a lot of scary noise in the build.
RUN pip install -r requirements.txt


# Copy over the source code
COPY app app/
COPY config config/
COPY main.py main.py

# Kick things off
ENTRYPOINT [ "uvicorn" ]
CMD ["main:main()", "--host", "0.0.0.0"]
