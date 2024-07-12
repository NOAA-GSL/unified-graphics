FROM node:18 AS build

WORKDIR /home/node/app

COPY package*.json ./
RUN npm clean-install
COPY src/unified_graphics/static/ src/unified_graphics/static/
RUN npm run vendor && npm run build

FROM nginxinc/nginx-unprivileged:1.27

COPY --from=build /home/node/app/build /usr/share/nginx/html/static
COPY docker/webserver/default.conf.template /etc/nginx/templates/

# The default port exposed by the unprivileged image is 8080
EXPOSE 80
