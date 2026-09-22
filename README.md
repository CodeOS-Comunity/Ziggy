# Ziggy

## Ziggy the new and improved AI for CodeOS

A Qt chat app for CodeOS. `QtZiggyWidget` renders a chat window; every
prompt is sent to the AI running inside the kernel via `ai_query()`
(`SYSCALL_AI_QUERY`), and the reply is printed back in the transcript.

## Pieces

```
ziggy.cpp    — the Qt chat frontend (quick replies, tones, send box)
kernel/ai.c  — the in-kernel AI backend: an ELIZA-style keyword-matching
               engine (not neural/ML) that pattern-matches the prompt and
               returns a keyed response
kernel/ai.h  — ai_query() interface (ai_query(prompt, buf, len))
```

## Building

Built as part of the CodeOS tree. The `qt6/panels` Qt frontend compiles
`ziggy.cpp` (from `pkgs/extra/qt_apps/`) into the kernel image, and the
kernel links `ai.c`. The app is launched from the launcher — type a
message and it is answered by the in-kernel AI.

These files compile inside the kernel's Qt app set and include CodeOS
kernel headers (mouse/keyboard/input/fb/mm/... + the Qt app panel
headers), so they are not standalone-buildable; build them from the
CodeOS tree.

## Mirror status

Kept in sync with the CodeOS tree: `pkgs/extra/qt_apps/ziggy.cpp`
(app) and `kernel/kernel/ai.c` + `kernel/kernel/ai.h` (backend).