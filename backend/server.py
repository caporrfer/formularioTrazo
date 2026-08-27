import hashlib
import hmac
import html
import json
import os
import re
import secrets
import shutil
import sqlite3
from datetime import datetime, timezone
from email.parser import BytesParser
from email.policy import default
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse


DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
DB_PATH = DATA_DIR / "trazo.sqlite3"
UPLOAD_DIR = DATA_DIR / "uploads"
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
PUBLIC_ADMIN_PATH = "/admin/"
CONTENT_DIR = Path(os.getenv("CONTENT_DIR", "/app/content"))
MAX_REQUEST = 30 * 1024 * 1024
SESSIONS = set()


def db():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with db() as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                payload TEXT NOT NULL,
                attachments TEXT NOT NULL DEFAULT '[]',
                remote_ip TEXT
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS content_revisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference TEXT NOT NULL UNIQUE,
                client_identifier TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload TEXT NOT NULL,
                remote_ip TEXT
            )"""
        )


def content_catalog(identifier):
    if not re.fullmatch(r"[a-z0-9-]{2,40}", identifier or ""):
        return None
    source = CONTENT_DIR / f"{identifier}.md"
    if not source.is_file():
        return None
    section = "General"
    entries = []
    pattern = re.compile(r"^\d+\. \*\*([A-Z]+-\d+) — ([^*]+):\*\*\s*(.*)$")
    for raw_line in source.read_text(encoding="utf-8").splitlines():
        if raw_line.startswith("## "):
            section = raw_line[3:].strip()
        elif raw_line.startswith("### "):
            section = raw_line[4:].strip()
        else:
            match = pattern.match(raw_line)
            if match:
                entries.append({"id": match.group(1), "label": match.group(2).strip(), "text": match.group(3).strip(), "section": section})
    return entries


def esc(value):
    return html.escape(str(value or ""))


def nested(payload, *keys):
    value = payload
    for key in keys:
        if not isinstance(value, dict):
            return ""
        value = value.get(key, "")
    return value


def format_value(value):
    if isinstance(value, bool):
        return "Sí" if value else "No"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "—"
    if isinstance(value, dict):
        return " · ".join(f"{key}: {format_value(item)}" for key, item in value.items() if item not in ("", [], None)) or "—"
    return str(value) if value not in ("", None) else "—"


LABELS = {
    "client": "Cliente y negocio",
    "identity": "Identidad visual",
    "content": "Contenido",
    "features": "Funcionalidades",
    "social": "Redes sociales",
    "launch": "Lanzamiento y soporte",
    "businessName": "Negocio",
    "contactName": "Contacto",
    "email": "Correo",
    "phone": "Teléfono",
    "businessType": "Actividad",
    "story": "Historia",
    "logoStatus": "Estado del logo",
    "paletteMode": "Elección de colores",
    "primaryColor": "Color principal",
    "secondaryColor": "Color secundario",
    "colorPalette": "Paleta",
    "styles": "Estilos",
    "typography": "Tipografía",
    "references": "Referencias",
    "sections": "Secciones",
    "photosStatus": "Fotografías",
    "instagram": "Instagram",
    "facebook": "Facebook",
    "tiktok": "TikTok",
    "other": "Otra red",
    "domain": "Dominio",
    "domainHelp": "Ayuda con dominio",
    "legal": "Textos legales",
    "maintenance": "Mantenimiento",
    "timeline": "Plazo",
    "notes": "Notas",
    "responsive": "Diseño responsive",
    "availability": "Disponibilidad",
}


def page(title, body):
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Trazo</title><style>
:root{{--ink:#25352f;--paper:#f4efe6;--accent:#b6533b;--line:#d8d0c3}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 system-ui,sans-serif}}
header{{background:var(--ink);color:white;padding:18px 5vw;display:flex;align-items:center;justify-content:space-between}}
header a{{color:white;text-decoration:none}}main{{width:min(1120px,92vw);margin:34px auto}}
h1{{font:700 clamp(28px,4vw,46px)/1.1 Georgia,serif;margin:0 0 10px}}h2{{font:700 23px Georgia,serif}}
.muted{{color:#68736e}}.card{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:22px;margin:18px 0;box-shadow:0 5px 20px #25352f0d}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}}.field{{padding:12px;background:#faf8f3;border-radius:9px}}
.field small{{display:block;color:#777;text-transform:uppercase;font-size:10px;letter-spacing:.08em}}.field div{{white-space:pre-wrap;overflow-wrap:anywhere;margin-top:4px}}
table{{width:100%;border-collapse:collapse;background:white;border-radius:12px;overflow:hidden}}th,td{{text-align:left;padding:13px;border-bottom:1px solid var(--line)}}th{{font-size:11px;text-transform:uppercase;color:#68736e}}
.button,button{{display:inline-block;border:0;border-radius:8px;background:var(--accent);color:white;padding:10px 15px;text-decoration:none;cursor:pointer}}.button.secondary{{background:#e7e1d7;color:var(--ink)}}
input{{width:100%;padding:11px;border:1px solid var(--line);border-radius:7px;margin:5px 0 14px}}label{{font-weight:650}}.login{{max-width:400px;margin:10vh auto}}.error{{color:#a12b23}}.files a{{display:block;margin:8px 0}}
@media(max-width:650px){{table thead{{display:none}}table tr,table td{{display:block}}table tr{{padding:12px;border-bottom:1px solid var(--line)}}table td{{border:0;padding:4px 8px}}}}
</style></head><body>{body}</body></html>"""


def header():
    return f'<header><a href="{PUBLIC_ADMIN_PATH}"><strong>TRAZO</strong> · Administración</a><nav><a href="{PUBLIC_ADMIN_PATH}">Briefs</a> · <a href="{PUBLIC_ADMIN_PATH}texts">Cambios de textos</a> · <a href="{PUBLIC_ADMIN_PATH}logout">Cerrar sesión</a></nav></header>'


class Handler(BaseHTTPRequestHandler):
    server_version = "TrazoAdmin/1.0"

    def log_message(self, fmt, *args):
        print(f"{self.client_address[0]} - {fmt % args}", flush=True)

    def send_bytes(self, status, data, content_type="text/html; charset=utf-8", headers=None):
        if isinstance(data, str):
            data = data.encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, location, headers=None):
        self.send_response(303)
        self.send_header("Location", location)
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()

    def authenticated(self):
        jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
        token = jar.get("trazo_session")
        return bool(token and token.value in SESSIONS)

    def require_auth(self):
        if self.authenticated():
            return True
        self.redirect(PUBLIC_ADMIN_PATH + "login")
        return False

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            return self.send_bytes(200, "ok", "text/plain")
        if parsed.path == "/api/content-editor":
            return self.get_content_editor(parse_qs(parsed.query))
        if parsed.path == "/admin/login":
            return self.login_page()
        if parsed.path == "/admin/logout":
            jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
            if jar.get("trazo_session"):
                SESSIONS.discard(jar["trazo_session"].value)
            return self.redirect(PUBLIC_ADMIN_PATH + "login", {"Set-Cookie": "trazo_session=; Path=/admin; Max-Age=0; HttpOnly; SameSite=Lax"})
        if parsed.path == "/admin/file":
            if not self.require_auth(): return
            return self.download_file(parse_qs(parsed.query))
        if parsed.path in ("/admin", "/admin/"):
            if not self.require_auth(): return
            query = parse_qs(parsed.query)
            return self.detail(query["id"][0]) if "id" in query else self.list_submissions()
        if parsed.path == "/admin/texts":
            if not self.require_auth(): return
            query = parse_qs(parsed.query)
            return self.content_revision_detail(query["id"][0]) if "id" in query else self.list_content_revisions()
        self.send_bytes(404, "No encontrado", "text/plain")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/submissions":
            return self.create_submission()
        if parsed.path == "/api/content-editor":
            return self.create_content_revision()
        if parsed.path == "/admin/login":
            return self.login()
        self.send_bytes(404, "No encontrado", "text/plain")

    def get_content_editor(self, query):
        identifier = query.get("identifier", [""])[0].strip().lower()
        catalog = content_catalog(identifier)
        if catalog is None:
            return self.send_bytes(404, json.dumps({"error": "No existe ningún proyecto con ese identificador."}, ensure_ascii=False), "application/json")
        project = "IBHOLA Trail Running" if identifier == "ibhola" else identifier
        self.send_bytes(200, json.dumps({"identifier": identifier, "project": project, "texts": catalog}, ensure_ascii=False), "application/json")

    def create_content_revision(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 2 * 1024 * 1024:
                return self.send_bytes(413, json.dumps({"error": "El envío está vacío o es demasiado grande."}), "application/json")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            identifier = str(payload.get("identifier", "")).strip().lower()
            catalog = content_catalog(identifier)
            changes = payload.get("changes")
            additions = payload.get("additions", [])
            if catalog is None or not isinstance(changes, list) or not isinstance(additions, list):
                return self.send_bytes(400, json.dumps({"error": "Los datos enviados no son válidos."}), "application/json")
            known_ids = {item["id"] for item in catalog}
            clean_changes = []
            for item in changes:
                item_id = str(item.get("id", ""))
                text = str(item.get("text", "")).strip()
                if item_id in known_ids and text and len(text) <= 5000:
                    clean_changes.append({"id": item_id, "text": text})
            clean_additions = []
            for item in additions:
                title = str(item.get("title", "")).strip()
                text = str(item.get("text", "")).strip()
                location = str(item.get("location", "")).strip()
                if title and text and max(len(title), len(location)) <= 300 and len(text) <= 5000:
                    clean_additions.append({"title": title, "text": text, "location": location})
            if not clean_changes and not clean_additions:
                return self.send_bytes(400, json.dumps({"error": "No has realizado ningún cambio."}), "application/json")
            now = datetime.now(timezone.utc)
            reference = "TXT-" + now.strftime("%Y%m%d-") + secrets.token_hex(3).upper()
            stored = {"identifier": identifier, "changes": clean_changes, "additions": clean_additions}
            with db() as connection:
                connection.execute("INSERT INTO content_revisions(reference, client_identifier, created_at, payload, remote_ip) VALUES(?,?,?,?,?)", (reference, identifier, now.isoformat(), json.dumps(stored, ensure_ascii=False), self.headers.get("X-Real-IP", self.client_address[0])))
            self.send_bytes(201, json.dumps({"reference": reference}, ensure_ascii=False), "application/json")
        except (json.JSONDecodeError, ValueError):
            self.send_bytes(400, json.dumps({"error": "Los datos enviados no son válidos."}), "application/json")
        except Exception as error:
            print(f"content revision error: {error}", flush=True)
            self.send_bytes(500, json.dumps({"error": "No se han podido guardar los cambios."}), "application/json")

    def login_page(self, error=""):
        body = f"""<main class="login"><div class="card"><h1>Administración</h1><p class="muted">Accede para revisar los formularios recibidos.</p>
        {'<p class="error">Usuario o contraseña incorrectos.</p>' if error else ''}
        <form method="post" action="{PUBLIC_ADMIN_PATH}login"><label>Usuario<input name="username" autocomplete="username" required autofocus></label>
        <label>Contraseña<input name="password" type="password" autocomplete="current-password" required></label><button>Entrar</button></form></div></main>"""
        self.send_bytes(401 if error else 200, page("Acceso", body))

    def login(self):
        length = int(self.headers.get("Content-Length", "0"))
        form = parse_qs(self.rfile.read(min(length, 8192)).decode("utf-8", "replace"))
        username = form.get("username", [""])[0]
        password = form.get("password", [""])[0]
        if not (hmac.compare_digest(username, ADMIN_USER) and hmac.compare_digest(password, ADMIN_PASSWORD)):
            return self.login_page(True)
        token = secrets.token_urlsafe(32)
        SESSIONS.add(token)
        self.redirect(PUBLIC_ADMIN_PATH, {"Set-Cookie": f"trazo_session={token}; Path=/admin; HttpOnly; SameSite=Lax"})

    def create_submission(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_REQUEST:
                return self.send_bytes(413, json.dumps({"error": "El envío está vacío o supera 30 MB"}), "application/json")
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" not in content_type:
                return self.send_bytes(415, json.dumps({"error": "Formato de envío no válido"}), "application/json")
            raw = self.rfile.read(length)
            message = BytesParser(policy=default).parsebytes(
                f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode() + raw
            )
            payload = None
            uploads = []
            pending_files = []
            for part in message.iter_parts():
                name = part.get_param("name", header="content-disposition")
                filename = part.get_filename()
                content = part.get_payload(decode=True) or b""
                if name == "payload" and not filename:
                    payload = json.loads(content.decode("utf-8"))
                elif name == "files" and filename:
                    pending_files.append((filename, part.get_content_type(), content))
            if not isinstance(payload, dict) or not nested(payload, "client", "businessName") or not nested(payload, "client", "email"):
                return self.send_bytes(400, json.dumps({"error": "Faltan datos obligatorios"}), "application/json")
            now = datetime.now(timezone.utc)
            reference = "WEB-" + now.strftime("%Y%m%d-") + secrets.token_hex(3).upper()
            target_dir = UPLOAD_DIR / reference
            for filename, mime, content in pending_files:
                safe = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(filename).name).strip(".-") or "archivo"
                candidate = safe
                counter = 2
                while (target_dir / candidate).exists():
                    candidate = f"{Path(safe).stem}-{counter}{Path(safe).suffix}"
                    counter += 1
                target_dir.mkdir(parents=True, exist_ok=True)
                (target_dir / candidate).write_bytes(content)
                uploads.append({"name": candidate, "originalName": filename, "type": mime, "size": len(content)})
            with db() as connection:
                connection.execute(
                    "INSERT INTO submissions(reference, created_at, payload, attachments, remote_ip) VALUES(?,?,?,?,?)",
                    (reference, now.isoformat(), json.dumps(payload, ensure_ascii=False), json.dumps(uploads, ensure_ascii=False), self.headers.get("X-Real-IP", self.client_address[0])),
                )
            self.send_bytes(201, json.dumps({"reference": reference}, ensure_ascii=False), "application/json")
        except (json.JSONDecodeError, ValueError):
            self.send_bytes(400, json.dumps({"error": "Los datos del formulario no son válidos"}), "application/json")
        except Exception as error:
            print(f"submission error: {error}", flush=True)
            self.send_bytes(500, json.dumps({"error": "No se ha podido guardar el formulario"}), "application/json")

    def list_submissions(self):
        with db() as connection:
            rows = connection.execute("SELECT id, reference, created_at, payload FROM submissions ORDER BY id DESC").fetchall()
        entries = []
        for row in rows:
            payload = json.loads(row["payload"])
            client = payload.get("client", {})
            date = row["created_at"].replace("T", " ")[:16]
            entries.append(f"<tr><td><a href=\"?id={row['id']}\"><strong>{esc(row['reference'])}</strong></a></td><td>{esc(client.get('businessName'))}</td><td>{esc(client.get('contactName'))}<br><small>{esc(client.get('email'))}</small></td><td>{esc(date)} UTC</td><td><a class=\"button\" href=\"?id={row['id']}\">Ver</a></td></tr>")
        empty = '<div class="card"><p>Todavía no se ha recibido ningún formulario.</p></div>'
        table = f'<table><thead><tr><th>Referencia</th><th>Negocio</th><th>Contacto</th><th>Fecha</th><th></th></tr></thead><tbody>{"".join(entries)}</tbody></table>' if entries else empty
        body = header() + f'<main><h1>Formularios recibidos</h1><p class="muted">{len(rows)} formulario(s) guardado(s)</p>{table}</main>'
        self.send_bytes(200, page("Formularios", body))

    def list_content_revisions(self):
        with db() as connection:
            rows = connection.execute("SELECT id, reference, client_identifier, created_at, payload FROM content_revisions ORDER BY id DESC").fetchall()
        entries = []
        for row in rows:
            payload = json.loads(row["payload"])
            total = len(payload.get("changes", [])) + len(payload.get("additions", []))
            date = row["created_at"].replace("T", " ")[:16]
            entries.append(f'<tr><td><a href="texts?id={row["id"]}"><strong>{esc(row["reference"])}</strong></a></td><td>{esc(row["client_identifier"])}</td><td>{total} propuesta(s)</td><td>{esc(date)} UTC</td><td><a class="button" href="texts?id={row["id"]}">Ver</a></td></tr>')
        empty = '<div class="card"><p>Todavía no se ha recibido ninguna propuesta de textos.</p></div>'
        table = f'<table><thead><tr><th>Referencia</th><th>Proyecto</th><th>Cambios</th><th>Fecha</th><th></th></tr></thead><tbody>{"".join(entries)}</tbody></table>' if entries else empty
        body = header() + f'<main><h1>Cambios de textos</h1><p class="muted">{len(rows)} envío(s) guardado(s)</p>{table}</main>'
        self.send_bytes(200, page("Cambios de textos", body))

    def content_revision_detail(self, revision_id):
        try:
            numeric_id = int(revision_id)
        except ValueError:
            return self.send_bytes(404, "No encontrado", "text/plain")
        with db() as connection:
            row = connection.execute("SELECT * FROM content_revisions WHERE id=?", (numeric_id,)).fetchone()
        if not row:
            return self.send_bytes(404, "No encontrado", "text/plain")
        payload = json.loads(row["payload"])
        catalog = content_catalog(row["client_identifier"]) or []
        originals = {item["id"]: item for item in catalog}
        changes = []
        for item in payload.get("changes", []):
            original = originals.get(item["id"], {})
            changes.append(f'<section class="card"><p class="muted">{esc(item["id"])} · {esc(original.get("section"))} · {esc(original.get("label"))}</p><div class="grid"><div class="field"><small>Texto actual</small><div>{esc(original.get("text"))}</div></div><div class="field"><small>Texto propuesto</small><div>{esc(item["text"])}</div></div></div></section>')
        additions = [f'<section class="card"><p class="muted">Texto nuevo · {esc(item.get("location"))}</p><h2>{esc(item.get("title"))}</h2><div class="field"><div>{esc(item.get("text"))}</div></div></section>' for item in payload.get("additions", [])]
        body = header() + f'<main><a class="button secondary" href="texts">← Volver</a><h1>{esc(row["reference"])}</h1><p class="muted">Proyecto {esc(row["client_identifier"])} · {esc(row["created_at"].replace("T", " ")[:16])} UTC</p>{"".join(changes + additions)}</main>'
        self.send_bytes(200, page(row["reference"], body))

    def detail(self, submission_id):
        try:
            numeric_id = int(submission_id)
        except ValueError:
            return self.send_bytes(404, "No encontrado", "text/plain")
        with db() as connection:
            row = connection.execute("SELECT * FROM submissions WHERE id=?", (numeric_id,)).fetchone()
        if not row:
            return self.send_bytes(404, "No encontrado", "text/plain")
        payload = json.loads(row["payload"])
        attachments = json.loads(row["attachments"])
        sections = []
        for group, values in payload.items():
            if isinstance(values, dict):
                fields = "".join(f'<div class="field"><small>{esc(LABELS.get(key, key))}</small><div>{esc(format_value(value))}</div></div>' for key, value in values.items())
            else:
                fields = f'<div class="field"><div>{esc(format_value(values))}</div></div>'
            sections.append(f'<section class="card"><h2>{esc(LABELS.get(group, group))}</h2><div class="grid">{fields}</div></section>')
        file_links = "".join(f'<a href="file?id={row["id"]}&name={quote(item["name"])}">📎 {esc(item.get("originalName", item["name"]))} ({item["size"] // 1024 + 1} KB)</a>' for item in attachments)
        files = f'<section class="card files"><h2>Archivos adjuntos</h2>{file_links or "<p>Sin archivos adjuntos.</p>"}</section>'
        body = header() + f'<main><a class="button secondary" href="./">← Volver</a><h1>{esc(nested(payload,"client","businessName"))}</h1><p class="muted">{esc(row["reference"])} · {esc(row["created_at"].replace("T"," ")[:16])} UTC</p>{"".join(sections)}{files}</main>'
        self.send_bytes(200, page(row["reference"], body))

    def download_file(self, query):
        try:
            submission_id = int(query.get("id", [""])[0])
            requested = Path(query.get("name", [""])[0]).name
        except ValueError:
            return self.send_bytes(404, "No encontrado", "text/plain")
        with db() as connection:
            row = connection.execute("SELECT reference, attachments FROM submissions WHERE id=?", (submission_id,)).fetchone()
        if not row:
            return self.send_bytes(404, "No encontrado", "text/plain")
        metadata = next((item for item in json.loads(row["attachments"]) if item["name"] == requested), None)
        path = UPLOAD_DIR / row["reference"] / requested
        if not metadata or not path.is_file():
            return self.send_bytes(404, "No encontrado", "text/plain")
        self.send_bytes(200, path.read_bytes(), metadata.get("type") or "application/octet-stream", {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(metadata.get('originalName', requested))}"})


if __name__ == "__main__":
    init_db()
    print("Trazo backend listening on :8000", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
