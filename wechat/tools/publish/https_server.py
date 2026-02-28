#!/usr/bin/env python3
"""
HTTPS CORS 本地服务器 — 为微信编辑器提供图片访问。

微信编辑器在 HTTPS 页面，无法 fetch HTTP localhost（mixed content），
所以需要自签证书的 HTTPS 服务器。

使用前：
  1. 生成自签证书（如未生成）：
     openssl req -x509 -newkey rsa:2048 -keyout /tmp/key.pem -out /tmp/cert.pem \
       -days 365 -nodes -subj '/CN=localhost'
  2. 在 Chrome 中访问 https://localhost:18443 接受证书（首次）

用法：
  python https_server.py /path/to/images/dir [port]
"""
import http.server
import os
import ssl
import sys


class CORSHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        print(f"[HTTPS] {args[0]}")


def main():
    if len(sys.argv) < 2:
        print("用法: python https_server.py <images_dir> [port]")
        print("例: python https_server.py ./images 18443")
        sys.exit(1)

    images_dir = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 18443

    cert_file = '/tmp/cert.pem'
    key_file = '/tmp/key.pem'

    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        print("证书不存在，正在生成...")
        os.system(
            f"openssl req -x509 -newkey rsa:2048 -keyout {key_file} -out {cert_file} "
            f"-days 365 -nodes -subj '/CN=localhost' 2>/dev/null"
        )
        print(f"证书已生成: {cert_file}, {key_file}")

    os.chdir(images_dir)
    server = http.server.HTTPServer(('localhost', port), CORSHandler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cert_file, key_file)
    server.socket = ctx.wrap_socket(server.socket, server_side=True)

    print(f"HTTPS server: https://localhost:{port}")
    print(f"Serving: {os.path.abspath(images_dir)}")
    print("Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == '__main__':
    main()
