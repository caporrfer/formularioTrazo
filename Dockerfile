FROM nginx:alpine

LABEL org.opencontainers.image.title="Formulario Trazo"
LABEL org.opencontainers.image.description="Formulario web estatico de Trazo"
LABEL org.opencontainers.image.created="2026-08-06"

COPY app/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=6 \
  CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
