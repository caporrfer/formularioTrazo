# Formulario Trazo — GitHub Pages

Versión estática del formulario de inicio y de la página de modelos de venta, preparada para publicarse desde la raíz de la rama `main` con GitHub Pages.

## Publicación

En GitHub, abre **Settings → Pages** y selecciona:

- Source: **Deploy from a branch**
- Branch: **main**
- Folder: **/ (root)**

La web quedará disponible en `https://caporrfer.github.io/formularioTrazo/`.

## Recepción de formularios

GitHub Pages no ejecuta servidores ni guarda datos. Mientras no se configure un servicio externo, al finalizar se descarga un archivo JSON que el cliente puede enviar al estudio.

Para recibir los formularios automáticamente, crea un endpoint en Formspree, Web3Forms o un servicio equivalente y colócalo en `index.html`:

```html
<body data-submit-endpoint="https://formspree.io/f/TU_ID">
```

Si se configura el endpoint, el formulario enviará los datos directamente y dejará de descargar el archivo JSON.

