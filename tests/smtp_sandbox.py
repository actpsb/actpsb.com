"""Local-only SMTP sandbox for backend tests. Synthetic messages only; it never relays anything.

Speaks just enough SMTP (EHLO, STARTTLS, AUTH PLAIN/LOGIN, MAIL, RCPT, DATA, QUIT) for PHPMailer,
with TLS from a throwaway self-signed certificate generated per run. Accepted messages are kept in memory.
"""
import base64
import socketserver
import ssl
import subprocess
import threading
from pathlib import Path


def make_cert(directory: Path):
    key, crt = directory / "key.pem", directory / "cert.pem"
    subprocess.run(
        ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", str(key), "-out", str(crt),
         "-days", "2", "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost"],
        check=True, capture_output=True)
    return key, crt


class Sandbox:
    def __init__(self, directory: Path, user="synthetic-user", password="synthetic-pass",
                 allowed_rcpt=("inbox@sandbox.test",), implicit_tls=False):
        self.key, self.crt = make_cert(directory)
        self.user, self.password = user, password
        self.allowed_rcpt = set(allowed_rcpt)
        self.implicit_tls = implicit_tls
        self.messages = []  # dicts: mail_from, rcpts, data
        self.auth_failures = 0
        self.rcpt_rejections = 0
        self.plaintext_auth_attempts = 0
        outer = self
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(str(self.crt), str(self.key))
        self.ctx = ctx

        class H(socketserver.StreamRequestHandler):
            def handle(self):
                try:
                    outer._session(self)
                except (OSError, ssl.SSLError, ValueError):
                    pass

        class S(socketserver.ThreadingTCPServer):
            allow_reuse_address = True
            daemon_threads = True

            def get_request(self):
                sock, addr = super().get_request()
                if outer.implicit_tls:
                    sock = outer.ctx.wrap_socket(sock, server_side=True)
                return sock, addr

            def handle_error(self, request, client_address):
                pass

        self.server = S(("127.0.0.1", 0), H)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()

    def _session(self, h):
        tls = self.implicit_tls
        rfile, wfile = h.rfile, h.wfile

        def send(line):
            wfile.write((line + "\r\n").encode())
            wfile.flush()

        send("220 sandbox ESMTP")
        mail_from, rcpts, authed = None, [], False
        while True:
            raw = rfile.readline()
            if not raw:
                return
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            cmd = line.upper()
            if cmd.startswith("EHLO") or cmd.startswith("HELO"):
                send("250-sandbox")
                if not tls:
                    send("250-STARTTLS")
                else:
                    send("250-AUTH PLAIN LOGIN")
                send("250 8BITMIME")
            elif cmd == "STARTTLS" and not tls:
                send("220 ready")
                tsock = self.ctx.wrap_socket(h.request, server_side=True)
                rfile, wfile = tsock.makefile("rb"), tsock.makefile("wb")
                tls = True
            elif cmd.startswith("AUTH"):
                if not tls:
                    self.plaintext_auth_attempts += 1
                    send("530 Must issue STARTTLS first")
                    continue
                parts = line.split()
                if parts[1].upper() == "PLAIN":
                    blob = parts[2] if len(parts) > 2 else None
                    if blob is None:
                        send("334 ")
                        blob = rfile.readline().decode().strip()
                    creds = base64.b64decode(blob).split(b"\0")
                    u, p = creds[1].decode(), creds[2].decode()
                else:
                    send("334 " + base64.b64encode(b"Username:").decode())
                    u = base64.b64decode(rfile.readline().strip()).decode()
                    send("334 " + base64.b64encode(b"Password:").decode())
                    p = base64.b64decode(rfile.readline().strip()).decode()
                if (u, p) == (self.user, self.password):
                    authed = True
                    send("235 Authentication successful")
                else:
                    self.auth_failures += 1
                    send("535 Authentication credentials invalid")
            elif cmd.startswith("MAIL FROM"):
                if not authed:
                    send("530 Authentication required")
                    continue
                mail_from, rcpts = line[10:].strip(), []
                send("250 OK")
            elif cmd.startswith("RCPT TO"):
                addr = line[8:].strip().split()[0].strip("<>")
                if addr in self.allowed_rcpt:
                    rcpts.append(addr)
                    send("250 OK")
                else:
                    self.rcpt_rejections += 1
                    send("550 5.7.1 Relaying denied")
            elif cmd == "DATA":
                if not rcpts:
                    send("554 no valid recipients")
                    continue
                send("354 End data with <CR><LF>.<CR><LF>")
                buf = []
                while True:
                    l = rfile.readline()
                    if l in (b".\r\n", b""):
                        break
                    buf.append(l[1:] if l.startswith(b"..") else l)
                self.messages.append({"mail_from": mail_from, "rcpts": rcpts,
                                      "data": b"".join(buf).decode("utf-8", "replace")})
                send("250 OK queued")
            elif cmd == "RSET":
                mail_from, rcpts = None, []
                send("250 OK")
            elif cmd == "NOOP":
                send("250 OK")
            elif cmd == "QUIT":
                send("221 Bye")
                return
            else:
                send("502 not implemented")
