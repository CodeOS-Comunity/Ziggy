# Ziggy — the new and improved AI for CodeOS

Ziggy is CodeOS's AI. The brain runs **outside the kernel** as a Python
backend on the dev host; the in-kernel Qt panel is just a renderer that
ships the prompt over HTTP and prints the reply.

```
┌─────────────── CodeOS guest (QEMU) ───────────────┐   ┌── dev host ──────────────┐
│  Qt chat widget (renderer/ziggy.cpp)               │   │  Python AI backend        │
│        │                                           │   │  (backend/, :8975)        │
│        v                                           │   │                           │
│  kernel ai_query() (kernel/ai.c: http_post shim)   │   │   models.py  — the rules  │
│        │                                           │   │   engine.py   — matcher   │
│        └── QEMU user-net ──► 10.0.2.2:8975 ───────┼──►│   server.py   — HTTP POST  │
└────────────────────────────────────────────────────┘   └───────────────────────────┘
```

The Python engine is an **order-faithful port** of the old in-kernel C
ELIZA (`get_ai_response()`): the same interleaved AND/OR rule order and
the same word-boundary matching. Where the C code checked `"kernel"`
before `"system monitor"`, so does the Python. Only the persona updated
(FreeCode → Ziggy) and a few Python-backend facts were swapped in.

## Pieces

```
renderer/ziggy.cpp  — the Qt chat frontend (quick replies, tones, send
                      box). Pure renderer: calls ai_query() and prints.
kernel/ai.c         — in-kernel transport shim. POSTs the prompt to the
                      host loopback (10.0.2.2 = QEMU user-net gateway)
                      at ZIGGY_AI_PORT (8975); returns the reply.
kernel/ai.h         — ai_query() interface + ZIGGY_AI_HOST / ZIGGY_AI_PORT
backend/models.py   — the rule set (exact / and / or / notand) as data
backend/engine.py   — the rule engine (C-order matched, boundary rules)
backend/server.py   — stdlib-only ThreadingHTTPServer, POST /query
backend/tests/      — 22 unittest cases (parity + protocol)
```

## Running

1. Start the backend on the host:

   ```sh
   cd backend
   python3 server.py --host 0.0.0.0   # default 127.0.0.1:8975; 0.0.0.0
                                      # makes it reachable from the guest
   ```

2. Boot CodeOS in QEMU with user-net networking (e1000):

   ```sh
   qemu-system-x86_64 -machine q35 -m 2G \
       -netdev user,id=net0 -device e1000,netdev=net0 \
       -cdrom codeos-1-kernel.iso -boot order=d
   ```

3. Open the Ziggy panel and type. Prompts travel kernel-http →
   `10.0.2.2:8975` → Python brain → reply back to the panel.

`__CLEAR__` replies reset the conversation; empty/204 replies ("no
answer" — e.g. `quit`, `exit`) make the renderer show its fallback.

## Protocol

```
POST /query            Content-Type: text/plain
  body:  the prompt
  200   reply text (body)            — normal answer
  200   body == "__CLEAR__"          — renderer clears the transcript
  204   empty body                   — "no answer", keep the fallback
```

## Tests

```sh
cd backend
python3 -m unittest discover -s tests -t .            # from backend/
python3 -m unittest discover -s backend/tests -t backend   # from repo root
```

## Mirror status

Kept in sync with the CodeOS tree:

| Ziggy repo      | CodeOS tree                              |
|-----------------|------------------------------------------|
| renderer/ziggy.cpp | `pkgs/extra/qt_apps/ziggy.cpp`        |
| kernel/ai.c     | `kernel/kernel/ai.c` (in the `kernel/` Makefile tree: `kernel/ai.c`) |
| kernel/ai.h     | `kernel/kernel/ai.h`                     |