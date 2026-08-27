# Conectar Trazo con Supabase

La app ya incluye Google OAuth, acceso por enlace mágico, guardado de briefs, adjuntos y propuestas de textos. Mientras `app/assets/supabase-config.js` esté vacío, mantiene el backend Docker actual como fallback.

## 1. Crear el proyecto y la base de datos

1. Crea un proyecto en Supabase.
2. Abre **SQL Editor** y ejecuta `supabase/migrations/202608270001_initial_trazo.sql`.
3. Comprueba en **Table Editor** que existen `briefs` y `text_revisions`, y en **Storage** el bucket privado `brief-files`.

La migración activa RLS. Cada usuario solo puede leer, insertar y actualizar sus propias filas; una sesión anónima no recibe permisos. La clave `service_role` evita RLS: no debe aparecer nunca en HTML o JavaScript del navegador.

## 2. Configurar la app

En **Project Settings → API**, copia la Project URL y la clave pública/publishable (o `anon` en proyectos antiguos) en `app/assets/supabase-config.js`:

```js
window.TRAZO_SUPABASE = {
  url: 'https://TU-PROYECTO.supabase.co',
  anonKey: 'sb_publishable_...',
  requireAuth: true
};
```

La clave pública puede estar en el navegador porque RLS aplica la autorización. No uses aquí la clave secreta ni `service_role`.

## 3. Activar enlaces mágicos

En **Authentication → URL Configuration**:

- Define **Site URL** con la URL pública definitiva.
- Añade como **Redirect URLs** la URL pública, la ruta `/textos/` y las URLs locales que uses para probar, por ejemplo `http://localhost:4173/**`.

El código llama a `signInWithOtp` y usa la página actual como `emailRedirectTo`.

## 4. Activar Google

1. En Google Auth Platform crea un proyecto y configura Branding, Audience y Data Access (`openid`, email y profile).
2. Crea un cliente OAuth de tipo **Web application**.
3. En **Authorized JavaScript origins**, añade el origen público de Trazo y el origen local de desarrollo.
4. En **Authorized redirect URIs**, añade exactamente la callback que muestra **Supabase → Authentication → Providers → Google**: `https://TU-PROYECTO.supabase.co/auth/v1/callback`.
5. Copia Client ID y Client Secret en el proveedor Google de Supabase y actívalo.

## 5. Administración

El panel Python actual continúa viendo los envíos del SQLite local. Cuando Supabase sea el origen definitivo hay dos opciones:

- Primera fase: revisar `briefs` y `text_revisions` desde Supabase Studio.
- Fase recomendada: convertir `/admin/` en un panel autenticado y asignar un rol `staff` mediante custom claims; sus políticas RLS permitirían al equipo leer todos los proyectos. Ese rol debe asignarse desde un entorno servidor con `service_role`, nunca desde el cliente.

Antes de retirar SQLite, prueba Google, enlace mágico, subida de archivos, separación entre dos usuarios y el flujo de textos. Conserva el volumen Docker hasta haber exportado los envíos históricos.

Documentación oficial: [Google Auth](https://supabase.com/docs/guides/auth/social-login/auth-google), [Redirect URLs](https://supabase.com/docs/guides/auth/redirect-urls), [Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security) y [Storage Access Control](https://supabase.com/docs/guides/storage/security/access-control).
