FROM node:24.5.0 AS build

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist/ChatBot /usr/share/nginx/html

COPY ./nginx.conf /etc/nginx/conf.d/default.conf    