"""Ziggy AI backend — HTTP service.

Runs on the dev host and answers Ziggy chat prompts from the CodeOS
kernel. The in-kernel Qt renderer sends the prompt over HTTP (via the
kernel's http_post()); this service replies with the AI's plain-text
answer. Stdlib-only (ThreadingHTTPServer) — no pip packages required.

Protocol:
    POST /query
    Content-Type: text/plain; charset=utf-8
    Body: the raw prompt text

    Response body: the AI's plain-text reply (200).
    A 200 with an empty body means "no answer" (the kernel maps that to
    its own fallback text).

Run:  python3 server.py            (binds 127.0.0.1:8975)
      python3 server.py --port N
      python3 server.py --host 0.0.0.0   (reach the guest via 10.0.2.2)
"""

import argparse
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:
    from . import engine
    from .engine import response as engine_response
except ImportError:  # running as a plain script (python3 server.py)
    import engine
    from engine import response as engine_response

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8975  # must match ZIGGY_AI_PORT in the kernel's ai.h


class ZiggyHandler(BaseHTTPRequestHandler):
    """Serves POST /query: prompt in, plain-text reply out."""

    server_version = "ZiggyBackend/1.0"

    def do_POST(self):
        if self.path != "/query":
            self.send_error(404, "unknown endpoint (use POST /query)")
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            length = 0
        if length <= 0:
            self._reply(b"", 204)
            return

        body = self.rfile.read(length)
        prompt = body.decode("utf-8", "replace")
        answer = engine_response(prompt)

        if answer is None:
            self._reply(b"", 204)  # "no answer" — kernel shows its fallback
            return
        if answer == "__CLEAR__":
            # Control reply; send verbatim so the renderer resets.
            self._reply(answer.encode("utf-8"), 200)
            return
        self._reply(answer.encode("utf-8"), 200)

    def do_GET(self):
        # Not an API — only POST /query exists. 404 (not 501) so a
        # kernel probe or browser hitting the port sees "no endpoint".
        self.send_error(404, "unknown endpoint (use POST /query)")

    def _reply(self, data, code):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        if data:
            self.wfile.write(data)

    def log_message(self, fmt, *args):
        sys.stderr.write("ziggy: %s\n" % (fmt % args))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Ziggy AI backend for CodeOS")
    ap.add_argument("--host", default=DEFAULT_HOST,
                    help="bind address (0.0.0.0 to accept from the QEMU guest)")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT,
                    help="bind port (default %d)" % DEFAULT_PORT)
    args = ap.parse_args(argv)

    server = ThreadingHTTPServer((args.host, args.port), ZiggyHandler)
    print("Ziggy AI backend listening on %s:%d (POST /query)" %
          (args.host, args.port), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nZiggy backend stopped.", flush=True)
    return 0


# Invoke as a module: python3 -m backend.server
if __name__ == "__main__":
    sys.exit(main())