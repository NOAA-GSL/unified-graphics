FROM node:16.15 AS build

WORKDIR /home/node/app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:1.21
COPY --from=build /home/node/app/build /usr/share/nginx/html
COPY default.conf.template /etc/nginx/templates/
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*
