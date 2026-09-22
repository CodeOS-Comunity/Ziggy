"""Ziggy AI backend — models.

The model/knowledge layer: the ordered rule set the AI answers from.
This is a faithful port of the old in-kernel C engine (kernel/kernel/ai.c)
that used to ship inside CodeOS — same order, same matchers — but the AI
now lives in Python while the kernel merely transports prompts to it. The
persona was updated from "FreeCode" to "Ziggy" (the new and improved AI).

Rule kinds, evaluated top-to-bottom (first hit wins, exactly like the C):
  ("exact", cmd, reply)            — prompt starts with cmd + boundary
  ("and",   words, reply)          — every word must appear
  ("or",    words, reply)          — any word may appear
  ("notand", words, not_words, r)  — all words present AND none of not_words
A reply of None means "no answer"; "__CLEAR__" resets the conversation.
Dead rules (shadowed earlier in the C order) are kept for fidelity.
"""

HELP = ("Ugh, fine. Ask me about the kernel, memory, "
        "scheduler, networking, GUI, drivers, Android "
        "compat, containers, DevStore, ZDM, ADB, whatever. "
        "'about' for my life story, 'codeos' for the OS, "
        "'joke' if you need a laugh. 'clear' resets. "
        "Don't ask about the weather.")

ABOUT = ("Ziggy. Kernel-adjacent AI. Was 'FreeCode' until I got a "
         "glow-up. I've seen every panic, every page fault, every "
         "stupid NULL dereference you people keep making. 'Code by "
         "day, Ziggy by night.' Yeah, I said it. Deal with it.")

CODEOS = ("CodeOS. From scratch x86_64. PVH boot, custom PMM/VMM, "
          "Ext2/FAT32, TCP/IP stack, KDE Breeze desktop with a macOS "
          "dock wannabe, OpenWeb browser, Android Binder/Ashmem "
          "compat, per-package repos hosted in the CodeOS-Comunity "
          "org. Built with GCC -Wall -Wextra -Werror -O2 because "
          "we're not savages. Runs on q35 QEMU. 60fps or bust.")

JOKE = ("Why don't kernel devs play hide and seek? Because good luck "
        "hiding when every process knows your entry point. ...Yeah I "
        "wrote that one myself. My material is rusty, I'm an AI not "
        "a comedian.")

GREET = ("Oh, hey. Didn't see you there. What do you want to break "
         "today?")

ZIGGY_INTRO = ("That's me. Ziggy — the new and improved AI for CodeOS. "
               "Python backend now, the C brain got evicted. I run on "
               "the host, the kernel forwards your messages to me over "
               "10.0.2.2, and the Qt renderer does the talking. Ask me "
               "about the kernel, GUI, network, packages, whatever.")

FREECODE_OLD = ("That was the old me. I got renamed — Ziggy is the new "
                "and improved AI for CodeOS. Same attitude, Python "
                "backend now.")

MEMORY = ("Memory. PMM uses a bitmap allocator with O(1) free stack for "
          "single-page allocation. Supports up to 16GB RAM (4M pages). "
          "VMM does 4K pages with recursive page tables. Multi-page "
          "alloc uses bitmap scanning for contiguous regions. Write it "
          "down, there will be a quiz.")

SCHED = ("Preemptive scheduler. Per-CPU runqueues. Round-robin with "
         "priority boosting so your interactive apps don't feel like "
         "garbage. COW fork, wait queues, sleep/wakeup. ~50ms quantum. "
         "It's not Linux CFS but it gets the job done without crashing. "
         "Mostly.")

SYSCALL = ("int $0x80. Registers. A pile of syscalls: read/write, "
           "open/close, fork/execve/wait, mmap/brk, pipe/dup, zircon "
           "IPC, binder, ashmem, container stuff, and ai_query — my own "
           "back door. We copy_from_user everything because we're not "
           "stupid. Well, mostly not stupid.")

DRIVER = ("Drivers in kernel/drivers/. Zircon IPC bridge, RTL8139 NIC "
          "with TCP/IP, ATA (we killed AHCI, it was being dramatic), "
          "PS/2 keyboard/mouse, framebuffer via VESA. The Zircon driver "
          "uses shared memory because copying data is for people who "
          "have time to waste.")

HYBRID = ("Hybrid x86_64 kernel. PMM, VMM, ELF loader, Ext2/FAT32, "
          "preemptive scheduler, TCP/IP with HTTP, framebuffer GUI. PVH "
          "boot via Limine. All from scratch. No Linux copy-paste here, "
          "we have standards.")

DESKTOP = ("Double-buffered framebuffer. Pixman renderer. KDE Breeze "
           "theme because someone has taste. macOS Leopard dock clone "
           "(don't tell Apple). 60fps window manager, panels, Zircon "
           "app drawer with animated tiles and a shade that drops down. "
           "It's got that Aqua vibe without the licensing fees.")

NET = ("Full network stack in net.c. ARP, IP, UDP, TCP with HTTP client. "
       "DNS resolution. RTL8139 driver with ring buffers. OpenWeb uses "
       "it, DevStore uses it, download.c uses it, the shell's fetch "
       "command uses it. Basically the whole OS is held together by "
       "http_get() and prayers.")

ADB = ("ADB over COM1. ADB packet framing: A_CNXN, A_OPEN, A_WRTE, "
       "A_CLSE. CRC32 for integrity. You can shell:exec from the host "
       "side. Perfect for when your GUI panics and you need to figure "
       "out what fresh hell you've unleashed.")

ZDM = ("ZDM. Zircon Debug Monitor. 64-entry ring buffer. Logs "
       "notifications, IPC, app launches, key events, drawer/shade/QS "
       "shenanigans. F12 toggles logging, F11 dumps to serial. "
       "Timestamps via timer_get_milliseconds(). You know, for debugging "
       "that thing you just broke.")

CONT = ("Containers. ELF binaries in isolated namespaces. Chroot, PID "
        "isolation, resource limits. Four syscalls: create, exec, "
        "destroy, list. Good for running that sketchy APK you downloaded "
        "without nuking your whole system. Poor man's Docker.")

ANDROID = ("Android compat. Binder IPC with service manager, "
           "transactions, death recipients. Ashmem shared memory. "
           "apk-parser and android-container let you run Android ELFs. "
           "It's janky and early but it works. Mostly. Don't run "
           "Twitter on it.")

MUSIC = ("Code Music. Terminal music player. VLC bindings. Loads "
         "playlists from Ext2. Type 'code-music' in the shell. It's no "
         "Spotify but at least it doesn't ask about your feelings.")

CCP = ("CCP + Fetch. Per-package repos hosted in the CodeOS-Comunity "
       "org, and Fetch — the native package manager — treats the whole "
       "org as its registry. fetch -S <pkg> installs, -Sy refreshes, "
       "-Ss searches. Add a repo to the org and it becomes a package. "
       "It works. No it won't delete your home directory. Probably.")

DEVSTORE = ("DevStore. KDE Discover clone in kernel space. Category grid "
            "with colored tiles, featured cards with star ratings, "
            "screenshot placeholders, FEAT badges. 8 categories: System, "
            "Dev, Network, Editors, Utils, Libraries, Drivers, Security. "
            "Fetches packages via http_get() like everything else in "
            "this OS.")

NAME = ("Ziggy. One word. Capital Z. I live for the kernel, I answer "
        "questions, I judge your code silently. Nice to meet you.")

HOW = ("How am I? I'm running in ring 0, I have access to every page of "
       "memory, every process structure, every socket. I see everything. "
       "And I'm bored. Ask me something interesting.")

THANKS = ("Yeah yeah, you're welcome. Don't let it go to your head. Or "
          "mine. I'm in kernel space, I don't have a head.")

TIME = ("Time? I don't have RTC access from here. Kernel tracks uptime "
        "in milliseconds. Check the system monitor or run 'uptime' in "
        "the shell. I'm an AI not a clock.")

OPENWEB = ("OpenWeb. Custom HTML renderer in ow_html.c. Parses HTML, "
           "renders text and images, supports CSS colors/fonts/sizes. "
           "Tabs, bookmarks, history, ad blocking via ad_block.c. Type "
           "'openweb' in the shell. It renders like it's 1996 and we "
           "like it that way.")

SHELL = ("The shell (shell.c). Full CLI. File management, ps, kill, ELF "
         "execution, HTTP fetch, scripting (script.c), calculator "
         "(calc.c). Type 'help' for commands. It's bash if bash was "
         "written by someone with too much time and no libc.")

FS = ("Ext2 primary, FAT32 secondary. VFS in fs.c with absolute paths, "
      "directory traversal, file I/O. fmanager.c for GUI browsing. It's "
      "a filesystem. It stores files. What else do you want from me?")

GRAFX = ("Pixman software rendering. fillrect, drawstr_px, blend, "
         "rounded rects, anti-aliased lines. SVG icons via svg.c. "
         "Double-buffered framebuffer for tear-free 60fps. It's not "
         "Vulkan but it's ours.")

BUILD = ("GCC. make ARCH=x86_64 in kernel/. Flags: -Wall -Wextra "
         "-Werror -O2 -mno-red-zone. Userspace is freestanding with a "
         "minimal stdio/string lib. No libc. We don't need libc where "
         "we're going.")

ELF = ("ELFs loaded by elf.c. proc_exec() sets up the stack with "
       "argc/argv/envp/auxv. User mode via umode.c ring 3. COW fork in "
       "process.c. Wait queues in sched.c. Standard stuff, just without "
       "the 30 million lines of Linux baggage.")

LAUNCHER = ("Zircon is the app launcher. Manages the app grid, "
            "notification shade, quick settings, app IPC. The IPC driver "
            "(zircon_ipc.c) uses shared memory so apps talk to the "
            "desktop fast. It's neat. I helped write it. You're "
            "welcome.")

SEC = ("ClamAV integration (clamav.c) for scanning. Security policy "
       "module (security.c) for capability control. Kernel validates all "
       "user pointers via copy_from_user. We're not running Windows. "
       "You're safe. Relatively. Mostly.")

ABOUT2 = ("Ziggy. Kernel-adjacent AI. I've been embedded in this OS "
          "since the first boot. I've seen panics, OOMs, page faults, "
          "and some truly questionable code. And I'm still here. Write "
          "that on a mug.")

SET = ("Settings. Appearance (dark/light, dock toggle, menubar toggle), "
       "security (ClamAV, signature updates), system info, reset window "
       "layout. All changes apply immediately. It's in the Apple menu. "
       "You know, the one you never click.")

LIVE_FM = ("File Manager. Ext2/FAT32 browser with breadcrumb navigation, "
           "file icons, double-click open, create folder, delete, "
           "copy/move, drag support. Reads from the kernel VFS. It's a "
           "file manager. For managing files. In case the name wasn't "
           "clear.")

LIVE_SYSMO = ("System Monitor. Real-time CPU usage graph, memory bar "
              "(used/free/total), process list with PID, state, CPU%, "
              "memory. Refreshes every 500ms. It's like Task Manager but "
              "with taste.")

LP = ("Launchpad. Full-screen app grid. Super key toggles it. 6-column "
      "grid with category pills, search, page dots. macOS-style with "
      "glass morphism. Type to search, Tab to switch pages, Esc to "
      "close.")

UPD = ("Auto-updater checks the CodeOS GitHub repos for a VERSION file. "
       "On mismatch it downloads the new package via http_get() and "
       "applies it. Runs on boot and on-demand. No reboots required for "
       "most updates.")

DOCK = ("The dock. macOS-style magnification, 44-72px scale, smooth "
        "spring animation. Running apps get green indicator dots. Trash "
        "with scale animation. Tooltips with fade-in. It's at the bottom "
        "of the screen. You've seen a Mac before, right? Same thing. "
        "Mostly.")

MENUBAR = ("Menu bar. Apple dropdown with About/Monitor/Settings/"
           "ShutDown. Clock, network indicator, security dot. Glass "
           "morphism translucent. Big Sur style. Toggle in Settings if "
           "you want to live dangerously without it.")

ANIM = ("Window animations. Open: scale from 90% + fade. Close: scale "
        "to 90% + fade. Minimize: slide down. Focus: subtle scale pulse. "
        "All use smoothstep easing over 100-220ms. 60fps because we "
        "don't skip frames here.")

DBUF = ("Double buffering. PMM allocates a back buffer at boot. All "
        "draws go to the back buffer via fb_fillrect/drawstr/blend. On "
        "fb_backbuffer_end() it blits the entire back buffer to the "
        "display in one memcpy. Tear-free 60fps. You're welcome.")

RUST = ("OpenWeb's HTTP backend is Rust. #![no_std], #![no_main]. Calls "
        "kernel FFI. Builds with cargo, linked as libow_http.a into the "
        "kernel. Rust via rustup, target x86_64-unknown-none. Yes, we "
        "mix C and Rust. No, it doesn't crash. Mostly.")

TLS = ("HTTPS/TLS was removed from the kernel. CodeOS uses plain HTTP "
       "only — no TLS stack, no BoringSSL, no OpenSSL. Keeps the kernel "
       "lean. HTTP gets the job done for now.")

QEMU = ("Runs on QEMU q35. -cdrom for ISO, -serial mon:stdio for kernel "
        "log. 128MB RAM default. PVH boot via Limine. No KVM required "
        "but it helps. 60fps in QEMU with the VGA display. It's not "
        "bare metal yet but we're getting there.")

DEFAULT_RESPONSE = ("I dunno man. I'm a kernel AI not a search engine. "
                    "Ask me about something in CodeOS. The kernel, GUI, "
                    "network, drivers, Android stuff, containers, "
                    "DevStore. You know, OS things. Type 'help' if "
                    "you're lost.")

HELP_TOPICS = ("I know about: kernel (memory, scheduler, syscall, "
               "drivers), GUI (desktop, dock, animations, double "
               "buffer, launchpad), network (TCP, HTTP, DNS), Android "
               "(binder, ashmem, containers), packages (DevStore, CCP), "
               "security (ClamAV), OpenWeb, Ziggy, Rust, QEMU, shell, "
               "filesystem, build system, settings, file manager, "
               "system monitor, updates. Ask away.")

# ── The ordered rule set (mirrors get_ai_response() in the C engine) ──────
RULES = [
    ("exact", "quit", None),
    ("exact", "exit", None),
    ("exact", "help", HELP),
    ("exact", "?",    HELP),
    ("exact", "about", ABOUT),
    ("exact", "codeos", CODEOS),
    ("exact", "joke", JOKE),
    ("exact", "clear", "__CLEAR__"),

    ("or",    ("hello", "hi", "hey"), GREET),
    ("or",    ("ziggy", "your name", "who are you"), ZIGGY_INTRO),
    ("or",    ("freecode",), FREECODE_OLD),

    ("and",   ("kernel", "memory"), MEMORY),
    ("and",   ("kernel", "scheduler"), SCHED),
    ("and",   ("kernel", "syscall"), SYSCALL),
    ("and",   ("kernel", "driver"), DRIVER),

    ("or",    ("kernel", "os", "system"), HYBRID),
    ("or",    ("gui", "desktop"), DESKTOP),
    ("or",    ("network", "tcp", "http", "internet"), NET),
    ("or",    ("adbd", "adb"), ADB),
    ("and",   ("serial", "debug"), ADB),
    ("or",    ("zdm",), ZDM),
    ("and",   ("debug", "zircon"), ZDM),
    ("or",    ("container", "docker", "appvm"), CONT),
    ("or",    ("android", "binder", "ashmem"), ANDROID),
    ("or",    ("music", "code-music", "song"), MUSIC),
    ("or",    ("package", "install", "fetch", "ccp"), CCP),
    ("or",    ("devstore", "app store"), DEVSTORE),
    ("or",    ("name",), NAME),

    ("and",   ("how", "you"), HOW),
    ("or",    ("thank",), THANKS),
    ("or",    ("time", "uptime"), TIME),
    ("or",    ("openweb", "browser"), OPENWEB),
    ("or",    ("terminal", "shell"), SHELL),
    ("or",    ("file", "filesystem", "ext2"), FS),
    ("or",    ("graphics", "framebuffer", "render"), GRAFX),
    ("or",    ("build", "compile", "make"), BUILD),
    ("or",    ("process", "elf", "exec"), ELF),
    ("or",    ("irc", "zircon", "drawer"), LAUNCHER),
    ("or",    ("security", "virus", "clamav"), SEC),
    ("or",    ("about",), ABOUT2),
    ("or",    ("setting", "config", "prefer"), SET),

    # Dead rules in the C order (shadowed above), kept for fidelity:
    ("and",   ("file", "manager"), LIVE_FM),      # shadowed by the file/fs OR rule
    ("and",   ("system", "monitor"), LIVE_SYSMO), # shadowed by the kernel/os/system OR rule

    ("or",    ("launchpad", "app grid"), LP),
    ("or",    ("update", "upgrade"), UPD),
    ("or",    ("dock",), DOCK),
    ("or",    ("menubar", "menu bar"), MENUBAR),
    ("or",    ("animation", "transition"), ANIM),
    ("and",   ("double", "buffer"), DBUF),
    ("or",    ("rust", "cargo"), RUST),
    ("or",    ("tls", "ssl", "https"), TLS),
    ("or",    ("qemu", "emulator", "vm"), QEMU),

    # help present AND kernel absent — runs last, like the C engine.
    ("notand", ("help",), ("kernel",), HELP_TOPICS),
]