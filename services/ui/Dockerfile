FROM node:16.15 AS build

WORKDIR /home/node/app

COPY package*.json ./
RUN npm install

COPY . .
RUN PORT=80 npm run build \
    && cp -rv node_modules/@uswds/uswds/dist/fonts build/client/_app/assets/

FROM node:16.15

ENV NODE_ENV=production
WORKDIR /home/node/app

COPY --from=build /home/node/app/package.json /home/node/app/
COPY --from=build /home/node/app/build /home/node/app/build
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && npm install --ignore-scripts \
    && npm cache clean --force

ENV PORT=80
EXPOSE 80

CMD ["node", "build"]
