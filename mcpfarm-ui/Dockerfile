FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM caddy:2-alpine
COPY --from=build /app/dist /srv/ui
COPY Caddyfile /etc/caddy/Caddyfile
EXPOSE 3000
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile"]
