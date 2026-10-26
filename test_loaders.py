#!/usr/bin/env python3
"""Instala y arranca Paper y NeoForge de verdad, espera 'Done (' y apaga."""

import os, subprocess, threading, time
from pathlib import Path

os.environ["SSL_CERT_FILE"] = "/etc/ssl/cert.pem"
os.environ["MCCOLAB_JAVA"] = "/private/tmp/opencode/java21/jdk-21.0.13+9-jre/Contents/Home/bin/java"
os.environ["MCCOLAB_DRIVE"] = "/private/tmp/opencode/mcdrive"


def boot(kind, server_dir, mods=(), plugins=()):
    print(f"\n{'#' * 70}\n# {kind}  →  {server_dir}\n{'#' * 70}")
    os.environ["MCCOLAB_SERVER"] = server_dir
    ns = {"__name__": "__main__"}
    for name in ("01_config.py", "02_mods_config.py"):
        exec(compile((Path("cells") / name).read_text(), name, "exec"), ns)
    ns.update(SERVER_TYPE=kind, MC_VERSION="1.21.1", TUNNEL="ninguno", RAM_GB=2,
              MAX_HORAS=0.001, MODS=list(mods), PLUGINS=list(plugins), VIEW_DISTANCE=4)
    for name in ("03_setup.py", "04_install.py", "05_mods.py", "06_props.py"):
        exec(compile((Path("cells") / name).read_text(), name, "exec"), ns)

    argv = ns["launch_argv"]()
    print("🚀", " ".join(argv[:3]), "…")
    proc = subprocess.Popen(argv, cwd=server_dir, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    ready = threading.Event()

    def pump():
        for line in iter(proc.stdout.readline, ""):
            if not line:
                break
            if "Done (" in line or "For help, type" in line:
                print("   >>", line.rstrip()[:160])
                ready.set()

    threading.Thread(target=pump, daemon=True).start()
    ok = ready.wait(420) and proc.poll() is None
    print("   ✅ arrancó" if ok else "   ❌ no arrancó")
    proc.stdin.write("stop\n")
    proc.stdin.flush()
    try:
        proc.wait(timeout=120)
    except subprocess.TimeoutExpired:
        proc.kill()
    print("   código de salida:", proc.returncode)
    return ok


results = {}
results["paper"] = boot("paper", "/private/tmp/opencode/mc-paper")
results["neoforge"] = boot("neoforge", "/private/tmp/opencode/mc-neoforge")
print("\nRESULTADOS:", results)
