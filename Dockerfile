# Self-contained simulation workbench. Flask integration is a separate milestone.
FROM node:22-alpine AS frontend
ARG VITE_LAB_MODE=server
ENV VITE_LAB_MODE=$VITE_LAB_MODE
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM nginx:stable-alpine
COPY deployment/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend /app/build /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -q -O /dev/null http://127.0.0.1/health || exit 1
