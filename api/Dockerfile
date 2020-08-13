FROM python:3.7.2

# Setup a spot for the api code
WORKDIR /usr/local/src/skiff/app/api

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy over the source code
COPY app app/
COPY main.py main.py

# Kick things off
ENTRYPOINT [ "uvicorn" ]
CMD ["main:app", "--host", "0.0.0.0"]