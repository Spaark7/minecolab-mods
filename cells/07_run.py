#@title ▶️ 6. Arrancar servidor + túnel { display-mode: "form" }
#@markdown Deja esta celda corriendo. A las `MAX_HORAS` se apaga sola, guarda en Drive y libera la sesión.

import json, time, threading, subprocess, re, sys, tarfile, urllib.request, urllib.error
from pathlib import Path

SERVER_PROC = None
TUNNEL_PROC = None
STOP = threading.Event()
READY = threading.Event()
SEND_LOCK = threading.Lock()
session_start = time.time()
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def stream(proc, prefix="", on_line=None):
    try:
        for line in iter(proc.stdout.readline, ""):
            if not line:
                break
            clean = ANSI.sub("", line.rstrip())
            print(prefix + clean)
            if on_line:
                on_line(clean)
            if "Done (" in clean:
                READY.set()
    except Exception:
        pass


def send(cmd):
    with SEND_LOCK:
        if SERVER_PROC and SERVER_PROC.poll() is None:
            try:
                SERVER_PROC.stdin.write(cmd + "\n")
                SERVER_PROC.stdin.flush()
                print(f"⌨️  > {cmd}")
            except Exception as exc:
                print(f"(no pude enviar {cmd!r}: {exc})")


def _bore():
    """Túnel público sin cuenta: bore.pub:PUERTO (la dirección cambia cada sesión)."""
    global TUNNEL_PROC
    import platform
    machine = platform.machine().lower()
    arch = "aarch64" if machine in ("arm64", "aarch64") else "x86_64"
    target = "apple-darwin" if sys.platform == "darwin" else "unknown-linux-musl"
    url = (f"https://github.com/ekzhang/bore/releases/download/v0.6.0/"
           f"bore-v0.6.0-{arch}-{target}.tar.gz")
    exe = Path("/content/bore") if IN_COLAB else Path("/private/tmp/opencode/bore")
    if not exe.exists():
        tgz = Path("/tmp/bore.tgz")
        asset = url.rsplit("/", 1)[-1]
        download(url, tgz, sha256=github_sha256("ekzhang/bore", "v0.6.0", asset))
        safe_extract(tgz, exe.parent)
        built = exe.parent / "bore"
        if built != exe and built.exists():
            built.rename(exe)
        exe.chmod(0o755)

    shown = set()

    def watch(line):
        match = re.search(r"listening at (bore\.pub:\d+)", line)
        if match and "addr" not in shown:
            shown.add("addr")
            print("\n" + "=" * 62)
            print("🔗 DIRECCIÓN PARA TUS AMIGOS:  " + match.group(1))
            print("=" * 62 + "\n")

    TUNNEL_PROC = subprocess.Popen(
        [str(exe), "local", "25565", "--to", "bore.pub"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )
    threading.Thread(target=stream, args=(TUNNEL_PROC, "[bore] "),
                     kwargs={"on_line": watch}, daemon=True).start()
    print("🔗 bore.pub: túnel temporal, sin cuenta ni configuración.")


PLAYIT_VERSION = "v0.17.1"
PLAYIT_SHA256 = "e78d463d93aa1e3ec36a06ded5a1f4fe879905fdceb865df8f4cef6124f8a555"


def _playit_secret(path):
    """Lee la clave del agente desde el playit.toml guardado en Drive."""
    try:
        text = Path(path).read_text()
    except Exception:
        return None
    match = re.search(r'secret_key\s*=\s*"([0-9a-fA-F]+)"', text)
    if match:
        return match.group(1)
    text = text.strip()
    return text if re.fullmatch(r"[0-9a-fA-F]{16,}", text) else None


def _playit_address(secret):
    """Pregunta a la API de playit la dirección pública de tus túneles."""
    body = b"{}"
    warned = False
    hinted = False
    for _ in range(60):
        if STOP.wait(5):
            return
        try:
            req = urllib.request.Request(
                "https://api.playit.gg/v1/agents/rundata",
                data=body,
                headers={
                    "Authorization": "Agent-Key " + secret,
                    "Content-Type": "application/json",
                    "User-Agent": "MineColab/1.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                reply = json.load(r)
        except urllib.error.HTTPError as exc:
            try:
                reply = json.loads(exc.read().decode("utf-8", "replace"))
            except Exception:
                reply = {"status": "error", "data": {}}
        except Exception:
            continue
        if reply.get("status") != "success":
            if not warned:
                warned = True
                detail = (reply.get("data") or {}).get("message", "clave no válida")
                print(f"   (playit todavía no acepta la clave: {detail}; reintentando…)")
            continue
        payload = reply.get("data") or {}
        tunnels = [t for t in payload.get("tunnels") or [] if t.get("display_address")]
        if tunnels:
            print("\n" + "=" * 62)
            for t in tunnels:
                label = t.get("name") or t.get("tunnel_type_display") or "túnel"
                print(f"🔗 DIRECCIÓN DE PLAYIT ({label}): {t['display_address']}")
            print("=" * 62)
            print("   Si no ves el túnel de Minecraft, créalo en playit.gg:"
                  " 'Minecraft Java' → 127.0.0.1:25565\n")
            return
        if not hinted:
            hinted = True
            print("\nℹ️  Tu agente de playit está conectado pero aún no tiene túneles.")
            print("   Entra en playit.gg → tu agente → crea un túnel 'Minecraft Java'")
            print("   apuntando a 127.0.0.1:25565. La dirección saldrá aquí en ~10 s.\n")
        if payload.get("pending"):
            print("⏳ playit está creando el túnel…")


def _playit():
    """playit.gg: dirección fija. La clave del agente vive en tu Drive."""
    global TUNNEL_PROC
    cfg = DRIVE_ROOT / "playit"
    cfg.mkdir(parents=True, exist_ok=True)
    secret_file = cfg / "playit.toml"

    # Migración: si ya tenías la config en la sesión anterior dentro de ~/.config, la traemos.
    old = Path.home() / ".config" / "playit_gg" / "playit.toml"
    if not secret_file.exists() and old.exists():
        shutil.copy(old, secret_file)

    # OJO: desde v1.0 el binario 'playit-linux-amd64' es solo el daemon y no imprime
    # el enlace de claim. Usamos v0.17.1, que sigue soportada y funciona sola.
    exe = (Path("/content") if IN_COLAB else Path("/private/tmp/opencode")) / "playit-0.17.1"
    if not exe.exists():
        url = (f"https://github.com/playit-cloud/playit-agent/releases/download/"
               f"{PLAYIT_VERSION}/playit-linux-amd64")
        download(url, exe, sha256=github_sha256("playit-cloud/playit-agent",
                                                PLAYIT_VERSION, "playit-linux-amd64")
                                  or PLAYIT_SHA256)
        exe.chmod(0o755)

    state = {"claim": False, "tunnel": False}

    def watch(line):
        match = re.search(r"https://playit\.gg/claim/[0-9a-fA-F]+", line)
        if match and not state["claim"]:
            state["claim"] = True
            print("\n" + "=" * 62)
            print("🔗 VINCULA EL AGENTE (solo la 1ª vez): " + match.group(0))
            print("   Ábrelo, aprueba el agente y espera; luego crea un túnel")
            print("   'Minecraft Java' → 127.0.0.1:25565 en playit.gg")
            print("=" * 62 + "\n")
        if "tunnel running" in line and not state["tunnel"]:
            state["tunnel"] = True
            print("✅ playit conectado. Buscando tu dirección pública…")
            key = _playit_secret(secret_file)
            if key:
                threading.Thread(target=_playit_address, args=(key,), daemon=True).start()

    # -s = logs planos (sin la interfaz de pantalla completa, que en Colab no se ve).
    # --secret_path = la clave se guarda en Drive y sobrevive entre sesiones.
    TUNNEL_PROC = subprocess.Popen(
        [str(exe), "-s", "--secret_path", str(secret_file)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )
    threading.Thread(target=stream, args=(TUNNEL_PROC, "[playit] "),
                     kwargs={"on_line": watch}, daemon=True).start()
    print("🔗 playit.gg arrancando…")
    print("   · 1ª vez: abre el enlace 'claim' de abajo y aprueba el agente.")
    print("   · Luego crea un túnel 'Minecraft Java' → 127.0.0.1:25565.")
    print("   · La clave del agente se guarda en tu Drive para la próxima sesión.\n")

    def supervise():
        waited = 0
        while waited < 120 and not STOP.wait(5):
            waited += 5
            if TUNNEL_PROC.poll() is not None:
                break
            if state["claim"] or state["tunnel"]:
                return  # hay progreso: esperamos a que el usuario apruebe
        if TUNNEL_PROC.poll() is not None or not state["tunnel"]:
            print("\n⚠️  playit no llegó a conectar. Paso automáticamente a bore…")
            try:
                _bore()
            except Exception as exc:
                print("   tampoco pude abrir bore:", exc)

    threading.Thread(target=supervise, daemon=True).start()


def start_tunnel():
    if TUNNEL == "ninguno":
        print("🔌 Sin túnel: solo accesible dentro de la sesión.")
        return
    try:
        if TUNNEL == "bore":
            _bore()
        elif TUNNEL == "ngrok":
            sh("pip -q install pyngrok", check=True)
            from pyngrok import conf, ngrok
            if not NGROK_AUTHTOKEN:
                raise RuntimeError("Falta NGROK_AUTHTOKEN en la celda 1b.")
            conf.get_default().auth_token = NGROK_AUTHTOKEN
            tunnel = ngrok.connect(25565, "tcp")
            print("\n🔗 DIRECCIÓN PARA TUS AMIGOS: " + str(tunnel.public_url).replace("tcp://", "") + "\n")
        else:
            _playit()
    except Exception as exc:
        print(f"\n⚠️  El túnel '{TUNNEL}' falló: {exc}")
        if TUNNEL != "bore":
            print("   Probando bore como alternativa…")
            _bore()


def backup_loop():
    while not STOP.wait(BACKUP_MIN * 60):
        send("save-off")
        send("save-all flush")
        time.sleep(3)
        try:
            sync_worlds()
            print("   💾 mundo sincronizado con Drive")
        finally:
            send("save-on")


def mirror_startup_log():
    """Copia el log a Drive mientras arranca, para saber qué pasó si Colab se cae."""
    origen = SERVER_DIR / "logs" / "latest.log"
    destino = DRIVE_ROOT / "arranque.log"
    while not READY.is_set() and not STOP.wait(15):
        try:
            if origen.exists():
                shutil.copy(origen, destino)
        except Exception:
            pass


def reportar_fallo():
    """Si el servidor murió solo, muestra y guarda las últimas líneas del log."""
    code = SERVER_PROC.returncode if SERVER_PROC else None
    if code in (None, 0) or STOP.is_set():
        return
    origen = SERVER_DIR / "logs" / "latest.log"
    if not origen.exists():
        return
    print(f"\n❌ El servidor terminó con código {code}. Últimas líneas de su log:\n")
    lineas = origen.read_text(errors="replace").splitlines()[-40:]
    print("\n".join(lineas))
    if "OutOfMemoryError" in "\n".join(lineas):
        print("\n🧠 Es falta de RAM: baja RAM_GB o quita mods pesados.")
    try:
        shutil.copy(origen, DRIVE_ROOT / "ultimo-error.log")
        print(f"\n📄 Log completo guardado en {DRIVE_ROOT / 'ultimo-error.log'}")
    except Exception:
        pass


def watchdog():
    deadline = time.time() + float(MAX_HORAS) * 3600
    while not STOP.wait(20):
        if time.time() >= deadline:
            send("say El servidor se apagará en 60 s (límite de sesión de Colab).")
            print(f"\n⏰ {MAX_HORAS} h cumplidas: apagando y guardando…")
            time.sleep(60)
            send("stop")
            return


try:
    if not (SERVER_DIR / "eula.txt").exists():
        raise RuntimeError("Falta la instalación. Ejecuta antes las celdas 2 y 3.")

    argv = launch_argv()
    print("🚀 " + " ".join(argv))
    SERVER_PROC = subprocess.Popen(
        argv, cwd=str(SERVER_DIR), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, bufsize=1,
    )
    threading.Thread(target=stream, args=(SERVER_PROC, ""), daemon=True).start()
    threading.Thread(target=mirror_startup_log, daemon=True).start()

    mark = time.time()
    while not READY.wait(1):
        if SERVER_PROC.poll() is not None:
            print("\n❌ El servidor terminó antes de arrancar. Mira el log de arriba.")
            break
        if time.time() - mark > 600:
            print("⏳ Sigue arrancando… (la 1ª vez se descargan librerías)")
            mark = time.time()

    if SERVER_PROC.poll() is None:
        start_tunnel()
        time.sleep(3)
        for name in WHITELIST:
            if re.fullmatch(r"[A-Za-z0-9_]{1,16}", str(name)):
                send(f"whitelist add {name}")
        for name in OPS:
            if re.fullmatch(r"[A-Za-z0-9_]{1,16}", str(name)):
                send(f"op {name}")

        print("\n" + "─" * 60)
        print(f"✅ Servidor arriba (Java {JAVA_MAJOR}, {globals().get('RAM_EFECTIVA_GB', RAM_GB)} GB, {SERVER_TYPE} {MC_VERSION})")
        print(f"   Se apagará solo a las {MAX_HORAS} h o cuando pares esta celda.")
        print("   Comparte la dirección del túnel con tus amigos y deja la pestaña abierta.")
        if TUNNEL != "ninguno" and not WHITELIST:
            print("   ⚠️  Sin whitelist: cualquiera con la dirección puede entrar.")
            print("      Añade nombres en WHITELIST (celda 1b) para cerrarlo.")
        if not ONLINE_MODE:
            print("   ⚠️  online-mode=false: cualquiera puede usar el nombre de otro jugador.")
        print("─" * 60 + "\n")

        threading.Thread(target=backup_loop, daemon=True).start()
        threading.Thread(target=watchdog, daemon=True).start()

        while SERVER_PROC.poll() is None:
            time.sleep(1)
        print(f"\nℹ️  El servidor terminó con código {SERVER_PROC.returncode}.")
except KeyboardInterrupt:
    print("\n⌨️  Interrumpido desde el notebook.")
finally:
    reportar_fallo()
    STOP.set()
    if SERVER_PROC and SERVER_PROC.poll() is None:
        print("\n🛑 Deteniendo el servidor (guardando mundo)…")
        send("stop")
        try:
            SERVER_PROC.wait(timeout=120)
        except subprocess.TimeoutExpired:
            print("   no cerró a tiempo, forzando")
            SERVER_PROC.kill()
    if TUNNEL_PROC:
        TUNNEL_PROC.terminate()
        try:
            TUNNEL_PROC.wait(timeout=10)
        except subprocess.TimeoutExpired:
            TUNNEL_PROC.kill()
    sync_to_drive()
    backup_world("fin")
    print(f"\n✅ Sesión cerrada ({(time.time() - session_start) / 60:.0f} min). Mundo guardado en Drive.")
