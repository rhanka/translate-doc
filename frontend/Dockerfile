# syntax=docker/dockerfile:1
FROM node:20-alpine AS base

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

FROM base AS dev

COPY . .

CMD ["npm", "run", "dev"]

FROM base AS build

COPY . .
RUN npm run build

FROM nginx:alpine AS prod

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
