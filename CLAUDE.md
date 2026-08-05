# CLAUDE.md — Contexto del proyecto rpi-dashboard

## Qué es este proyecto

Panel de inicio visual para la Raspberry Pi. Página HTML estática que agrupa enlaces a todos los servicios activos, accesible desde cualquier dispositivo de la red local.

## Stack técnico

| Capa | Tecnología |
|------|-----------|
| Servidor web | nginx (vía Dockerfile propio) |
| Frontend | HTML + CSS inline (sin dependencias externas) |
| API de métricas | Python (stdlib + psutil), contenedor `rpi-metrics-api` |
| Despliegue | Docker + Docker Compose (dos servicios) |

## Arquitectura

El proyecto tiene **dos contenedores**:

- **`rpi-dashboard`** — nginx que sirve el HTML estático y hace proxy de `/api/` hacia el contenedor de métricas.
- **`rpi-metrics-api`** — servidor Python en el puerto 5000 (interno) que expone `/metrics` con datos de CPU, RAM y disco en JSON. Monta `/` del host en `/hostfs` (lectura) y `/mnt/media` para leer el disco externo.

El frontend JS llama a `/api/metrics` cada 15 segundos y actualiza las barras de progreso en tiempo real.

### Estructura de archivos

```
rpi-dashboard/
├── index.html               # Frontend y entrada para GitHub Pages
├── nginx.conf               # Proxy /api/ → rpi-metrics-api:5000
├── Dockerfile               # nginx con nginx.conf + html
├── docker-compose.yml       # Orquesta rpi-dashboard + rpi-metrics-api
└── metrics_api/
    ├── app.py               # Servidor de métricas (Python stdlib + psutil)
    ├── requirements.txt     # psutil
    └── Dockerfile           # python:3.12-slim
```

## Despliegue

- **Puerto**: `8888`
- **URL local**: `http://192.168.0.87:8888`
- **Directorio**: `/home/raspberry/docker/rpi-dashboard/`

### Comandos útiles

```bash
# Rebuildar ambos contenedores (tras cualquier cambio)
docker compose -f ~/docker/rpi-dashboard/docker-compose.yml up -d --build

# Ver logs del dashboard (nginx)
docker logs rpi-dashboard -f

# Ver logs de la API de métricas
docker logs rpi-metrics-api -f

# Probar la API de métricas directamente
curl http://localhost:8888/api/metrics
```

> **Importante**: Tanto `index.html` como `metrics_api/app.py` quedan grabados en sus respectivas imágenes. Cualquier cambio requiere **rebuildar con `--build`**, no basta con `docker restart`.

## Servicios registrados en el dashboard

| Nombre | Puerto | Descripción |
|--------|--------|-------------|
| Viaje a Canarias | :8096 | Itinerario, información y documentos PDF del viaje |
| O’Living · Vivienda 6 | :3000 | Seguimiento privado de la compra de vivienda |
| Piso Facturas | :8090 | Gestión de facturas y gastos del piso |
| Chat Local | :8000 | Chat con IA corriendo localmente |
| Nextcloud | :8080 | Almacenamiento en nube privada |
| Plex | :32400 | Servidor multimedia (películas, series, música) |
| Pi-hole | :8081 | Bloqueador de anuncios a nivel DNS |
| Portainer | :9000 | Gestión visual de contenedores Docker |
| n8n | :5678 | Automatización de flujos entre servicios |
| Finanzas | :8091 | Gestión de facturas del piso y patrimonio mensual |

## Cómo añadir un nuevo servicio

Editar `index.html` y añadir un bloque `<a class="card">` dentro del `<div class="grid">`:

```html
<a class="card" href="http://192.168.0.87:PUERTO" target="_blank" rel="noopener">
    <div class="card-icon">🔧</div>
    <div>
        <div class="card-title">Nombre del servicio</div>
        <div class="card-desc">Descripción breve de para qué sirve.</div>
    </div>
    <div class="card-footer">
        <span class="port">:PUERTO</span>
        <span class="arrow">→</span>
    </div>
</a>
```

Después: `docker compose -f ~/docker/rpi-dashboard/docker-compose.yml up -d --build`
