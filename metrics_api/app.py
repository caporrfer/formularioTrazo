#!/usr/bin/env python3
import json
import os
import psutil
from http.server import HTTPServer, BaseHTTPRequestHandler

import docker


SERVICE_CONTAINERS = {
    'canarias-viaje': ['canarias-viaje'],
    'tracking-casa': ['tracking-casa'],
    'chat-local': ['chat-local'],
    'plex': ['plex'],
    'portainer': ['portainer'],
    'impostor': ['impostor'],
    'finanzas': ['finanzas'],
    'macros': ['macros'],
}


def get_docker_client():
    sock = '/var/run/docker.sock'
    if not os.path.exists(sock):
        return None

    try:
        return docker.DockerClient(base_url=f'unix://{sock}')
    except Exception:
        return None


def get_service_statuses():
    client = get_docker_client()
    statuses = {}

    if client is None:
        for service_name in SERVICE_CONTAINERS:
            statuses[service_name] = {'running': False, 'available': False}
        return statuses

    try:
        containers = {container.name: container for container in client.containers.list(all=True)}
        for service_name, container_names in SERVICE_CONTAINERS.items():
            running = False
            available = False

            for container_name in container_names:
                container = containers.get(container_name)
                if container is None:
                    continue
                available = True
                if container.status == 'running':
                    running = True
                    break

            statuses[service_name] = {'running': running, 'available': available}
    except Exception:
        for service_name in SERVICE_CONTAINERS:
            statuses[service_name] = {'running': False, 'available': False}
    finally:
        client.close()

    return statuses


def get_metrics():
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk_sd = psutil.disk_usage('/hostfs')

    try:
        disk_hdd = psutil.disk_usage('/mnt/media')
        hdd_data = {
            'total': disk_hdd.total,
            'used': disk_hdd.used,
            'free': disk_hdd.free,
            'percent': disk_hdd.percent,
        }
    except Exception:
        hdd_data = None

    return {
        'cpu_percent': cpu,
        'ram': {
            'total': mem.total,
            'used': mem.used,
            'free': mem.available,
            'percent': mem.percent,
        },
        'disk_sd': {
            'total': disk_sd.total,
            'used': disk_sd.used,
            'free': disk_sd.free,
            'percent': disk_sd.percent,
        },
        'disk_hdd': hdd_data,
        'services': get_service_statuses(),
    }


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            data = get_metrics()
            body = json.dumps(data).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress access logs


if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 5000), MetricsHandler)
    server.serve_forever()
