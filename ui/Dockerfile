# NOTE: This Dockerfile is only used in development. It provides a runtime
# environment where the JavaScript build process can run. In production the
# files built by this process are served from disk, while in development a HTTP
# server that's distributed with the UI build tools is used.
FROM node:10.15.2

# Setup a spot for our code
WORKDIR /usr/local/src/skiff/app/ui

# Install dependencies
COPY package.json yarn.lock ./
RUN yarn install

# Copy in the source code
COPY . .

# This tells build scripts and libraries that we're in development, so they
# can include stuff that's helpful for debugging even if it's a tad slower.
ARG NODE_ENV=development
ENV NODE_ENV $NODE_ENV
ARG BABEL_ENV=development
ENV BABEL_ENV $BABEL_ENV

# Build the UI
RUN yarn build

# Tell `react-scripts` that it's not supposed to open a browser for us, since
# it's not running on the host machine.
ENV BROWSER none

ENTRYPOINT [ "yarn" ]
CMD [ "start" ]
