# Formulario Trazo

Código fuente de la web **Formulario Trazo**, su panel de administración y el servicio de revisión de textos. El proyecto se ejecuta con Docker Compose.

## Contenido

- `app/`: archivos estáticos de la web.
- `backend/`: API y panel de administración.
- `content/`: inventarios editoriales por cliente.
- `Dockerfile` y `backend/Dockerfile`: imágenes de frontend y backend.
- `compose.yaml`: levanta ambos servicios y, opcionalmente, un túnel temporal de Cloudflare.

La web guarda los formularios y sus adjuntos en una base de datos SQLite persistente. El volumen Docker `formulario-trazo_trazo-data` conserva la informacion aunque se reinicien o reconstruyan los contenedores.

## Administracion

El panel se publica bajo `/formulario-trazo/admin/`. En esta maquina esta disponible en:

```text
http://212.227.163.125/formulario-trazo/admin/
```

Las credenciales iniciales son `admin` / `admin`. Cambialas en `.env` mediante `TRAZO_ADMIN_USER` y `TRAZO_ADMIN_PASSWORD` y recrea el backend con `docker compose up -d --force-recreate backend`.

## Revision de textos por clientes

La ruta `/textos/` permite que cada cliente acceda a su inventario editorial mediante el identificador facilitado por Trazo. El proyecto disponible actualmente es `ibhola`.

El cliente puede buscar entre todos los textos, modificar únicamente los que desee y proponer contenido nuevo indicando su ubicación. Los envíos quedan guardados en SQLite con una referencia `TXT-...` y se revisan desde `/admin/texts`.

Los inventarios se almacenan como Markdown en `content/<identificador>.md`. Para incorporar otro proyecto, añade un documento con el mismo formato numerado y reconstruye los contenedores.

## Instalación

1. Instala Docker con el complemento Docker Compose.
2. Clona este repositorio y entra en el directorio.
3. Arranca los servicios:

   ```sh
   docker compose up -d --build trazo backend
   ```

4. Abre `http://localhost:4173`. Desde otro equipo de la misma red, abre `http://IP_DE_LA_MAQUINA:4173`.

La primera construcción necesita descargar las imágenes base de Nginx y Python.

## Configuracion opcional

Para cambiar el puerto o limitar el acceso a la propia maquina:

```sh
cp .env.example .env
```

Edita `.env` antes de ejecutar `docker compose up -d --build`. Por ejemplo, `TRAZO_BIND=127.0.0.1` evita que la web quede visible en la red local.

## Tunel publico temporal

El tunel es opcional, necesita Internet y publica la web mediante una URL aleatoria de Cloudflare:

```sh
docker compose --profile tunnel up -d
docker compose logs -f tunnel
```

La URL aparece en los logs. Para apagarlo:

```sh
docker compose --profile tunnel down
```

No uses el tunel para informacion sensible sin revisar antes el flujo del formulario y las condiciones del servicio.

## Operacion diaria

```sh
./arrancar.sh
./parar.sh
docker compose logs -f trazo
```
