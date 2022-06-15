FROM node:16.15.0 AS build

WORKDIR /home/node/app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build \
    && cp -rv node_modules/@uswds/uswds/dist/fonts build/_app/assets/

FROM nginx:1.21
COPY --from=build /home/node/app/build /usr/share/nginx/html
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*
