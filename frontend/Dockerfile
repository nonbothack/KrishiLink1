FROM node:24-alpine AS build
WORKDIR /app
ARG PUBLIC_SITE_URL
ARG PUBLIC_PRERENDER_API_BASE_URL
ARG VITE_PUBLIC_SUPPORT_PHONE
ARG VITE_PUBLIC_SUPPORT_EMAIL
ENV PUBLIC_SITE_URL=$PUBLIC_SITE_URL \
    VITE_PUBLIC_SITE_URL=$PUBLIC_SITE_URL \
    PUBLIC_PRERENDER_API_BASE_URL=$PUBLIC_PRERENDER_API_BASE_URL \
    VITE_PUBLIC_SUPPORT_PHONE=$VITE_PUBLIC_SUPPORT_PHONE \
    VITE_PUBLIC_SUPPORT_EMAIL=$VITE_PUBLIC_SUPPORT_EMAIL
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginxinc/nginx-unprivileged:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget -qO- http://127.0.0.1:8080/health || exit 1
