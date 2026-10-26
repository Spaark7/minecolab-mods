#!/usr/bin/env python3
"""Re-prueba NeoForge (ya instalado) y Forge desde cero, además de plugins en Paper."""

import os, subprocess, threading
from pathlib import Path

os.environ["SSL_CERT_FILE"] = "/etc/ssl/cert.pem"
os.environ["MCCOLAB_JAVA"] = "/private/tmp/opencode/java21/jdk-21.0.13+9-jre/Contents/Home/bin/java"
os.environ["MCCOLAB_DRIVE"] = "/private/tmp/opencode/mcdrive"


def boot(kind, server_dir, mods=(), plugins=(), version="1.21.1"):
    print(f"\n{'#' * 70}\n# {kind} {version}  →  {server_dir}\n{'#' * 70}", flush=True)
    os.environ["MCCOLAB_SERVER"] = server_dir
    ns = {"__name__": "__main__"}
    for name in ("01_config.py", "02_mods_config.py"):
        exec(compile((Path("cells") / name).read_text(), name, "exec"), ns)
    ns.update(SERVER_TYPE=kind, MC_VERSION=version, TUNNEL="ninguno", RAM_GB=2,
              MAX_HORAS=0.001, MODS=list(mods), PLUGINS=list(plugins), VIEW_DISTANCE=4)
    for name in ("03_setup.py", "04_install.py", "05_mods.py", "06_props.py"):
        exec(compile((Path("cells") / name).read_text(), name, "exec"), ns)

    argv = ns["launch_argv"]()
    print("🚀", " ".join(argv[:4]), "…", flush=True)
    proc = subprocess.Popen(argv, cwd=server_dir, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    ready = threading.Event()

    def pump():
        tail = []
        for line in iter(proc.stdout.readline, ""):
            if not line:
                break
            tail.append(line.rstrip())
            if "Done (" in line:
                print("   >>", line.rstrip()[:150], flush=True)
                ready.set()
        if not ready.is_set():
            print("\n".join("   ! " + t[:200] for t in tail[-15:]), flush=True)

    threading.Thread(target=pump, daemon=True).start()
    ok = ready.wait(600) and proc.poll() is None
    print("   ✅ arrancó" if ok else "   ❌ no arrancó", flush=True)
    if proc.poll() is None:
        proc.stdin.write("stop\n")
        proc.stdin.flush()
        try:
            proc.wait(timeout=120)
        except subprocess.TimeoutExpired:
            proc.kill()
    print("   código de salida:", proc.returncode, flush=True)
    return ok


r = {}
r["neoforge (reintento)"] = boot("neoforge", "/private/tmp/opencode/mc-neoforge")
r["forge"] = boot("forge", "/private/tmp/opencode/mc-forge")
r["paper+plugins"] = boot("paper", "/private/tmp/opencode/mc-paper", plugins=["luckperms", "spark"])
print("\nRESULTADOS:", r)
