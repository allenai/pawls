FROM python:3.7.2


# Setup a spot for the api code
WORKDIR /usr/local/src/skiff/app/api

ARG GITHUB_ACCESS_TOKEN

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel
COPY api/requirements.txt .

RUN pip install -r requirements.txt

# we need to install the pawls CLI, but we do so
# by first moving the code to a temp location.
COPY cli /tmp/pawls-cli/
RUN pip install -r /tmp/pawls-cli/requirements.txt
RUN pip install /tmp/pawls-cli

# Copy over the source code
COPY api/app app/
COPY api/config config/
COPY api/main.py main.py

# Kick things off
ENTRYPOINT [ "uvicorn" ]
CMD ["main:app", "--host", "0.0.0.0"]
