ARG NODE_IMAGE=node:22.13.1-bookworm-slim
ARG NGINX_IMAGE=nginx:1.27.3-alpine
ARG BUILDPLATFORM
ARG TARGETPLATFORM
ARG TARGETOS
ARG TARGETARCH

FROM --platform=$BUILDPLATFORM ${NODE_IMAGE} AS dependencies
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM dependencies AS test
COPY . .
RUN npm run typecheck

FROM test AS build
ENV VITE_API_BASE_URL=/api
RUN npm run build && find dist -name "*.map" -delete && printf "ok\n" > dist/health.txt

FROM --platform=$TARGETPLATFORM ${NGINX_IMAGE} AS runtime
LABEL org.opencontainers.image.title="OrganicAI Compass Frontend" \
      org.opencontainers.image.description="Static OrganicAI Compass frontend runtime" \
      org.opencontainers.image.source="local" \
      org.opencontainers.image.licenses="Proprietary"
COPY runtime-nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/dist /usr/share/nginx/html
RUN rm -f /etc/nginx/conf.d/default.conf \
    && mkdir -p /var/cache/nginx /var/run /tmp/nginx \
    && chown -R nginx:nginx /var/cache/nginx /var/run /tmp/nginx /usr/share/nginx/html
USER nginx
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD wget -qO- http://127.0.0.1:8080/health.txt || exit 1
