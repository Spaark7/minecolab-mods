#@title 🧰 2. Preparar entorno (Drive + Java) { display-mode: "form" }
#@markdown Monta Drive, crea las carpetas, detecta la Java que pide tu versión y trae el servidor. ~1 min.

import os, sys, re, json, glob, time, shutil, socket, hashlib, tarfile, subprocess, threading
import urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path

try:
    from google.colab import drive
    IN_COLAB = True
except Exception:
    IN_COLAB = False

if IN_COLAB:
    if not os.path.ismount("/content/drive"):
        drive.mount("/content/drive")
    DRIVE_ROOT = Path("/content/drive/MyDrive/MineColab")
    SERVER_DIR = Path("/content/mcserver")
else:
    DRIVE_ROOT = Path(os.environ.get("MCCOLAB_DRIVE", str(Path.home() / "MineColab")))
    SERVER_DIR = Path(os.environ.get("MCCOLAB_SERVER", "/private/tmp/opencode/mcserver"))
    print("ℹ️  Fuera de Colab: usando carpetas locales (modo prueba).")

DRIVE_SERVER = DRIVE_ROOT / "server"
BACKUP_DIR = DRIVE_ROOT / "backups"
for _p in (DRIVE_SERVER, BACKUP_DIR, SERVER_DIR):
    _p.mkdir(parents=True, exist_ok=True)

UA = {"User-Agent": "MineColab-Modded/2.0 (Google Colab notebook)"}


def get_json(url, timeout=45):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def download(url, dest, sha512=None, sha256=None, sha1=None, label=None):
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=600) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)
    expected = sha512 or sha256 or sha1
    if expected:
        algo = hashlib.sha512 if sha512 else (hashlib.sha256 if sha256 else hashlib.sha1)
        got = algo(dest.read_bytes()).hexdigest()
        if got.lower() != expected.lower():
            dest.unlink(missing_ok=True)
            raise RuntimeError(f"Hash incorrecto en {dest.name}: esperaba {expected[:16]}… y llegó {got[:16]}…")
        print(f"   🔒 hash {algo().name} verificado")
    print(f"   ↓ {label or dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
    return dest


def fetch_text(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace").strip().split()[0]


def github_sha256(repo, tag, asset_name):
    """GitHub publica el sha256 de cada asset de release; si falla, seguimos sin hash."""
    try:
        suffix = "latest" if tag == "latest" else f"tags/{tag}"
        release = get_json(f"https://api.github.com/repos/{repo}/releases/{suffix}")
        for asset in release.get("assets", []):
            if asset.get("name") == asset_name:
                digest = (asset.get("digest") or "").replace("sha256:", "")
                return digest or None
    except Exception as exc:
        print(f"   (no pude consultar el hash de {asset_name}: {exc})")
    return None


def safe_extract(archive, dest):
    """Extrae un tar.gz comprobando que ninguna entrada salga del destino."""
    dest = Path(dest).resolve()
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            target = (dest / member.name).resolve()
            if target != dest and not str(target).startswith(str(dest) + os.sep):
                raise RuntimeError(f"entrada sospechosa en {Path(archive).name}: {member.name}")
            if member.issym() or member.islnk():
                raise RuntimeError(f"enlace sospechoso en {Path(archive).name}: {member.name}")
        try:
            tar.extractall(dest, filter="data")
        except TypeError:
            tar.extractall(dest)


def sh(cmd, check=False, quiet=True):
    r = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if r.returncode != 0:
        if check:
            print(r.stdout[-3000:])
            print(r.stderr[-3000:])
            raise RuntimeError(f"Falló el comando: {cmd}")
        if not quiet:
            print(r.stdout[-2000:], r.stderr[-2000:])
    return r


# ── Metadatos oficiales de Mojang (versión + Java requerida) ────────────────
_MANIFEST = None


def mc_manifest():
    global _MANIFEST
    if _MANIFEST is None:
        _MANIFEST = get_json("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json")
    return _MANIFEST


def mc_meta(version):
    for v in mc_manifest()["versions"]:
        if v["id"] == version:
            return get_json(v["url"])
    raise RuntimeError(f"Minecraft {version} no existe. Revisa MC_VERSION (ej: 1.21.1, 26.3).")


def _java_major(exe):
    try:
        out = subprocess.run([exe, "-version"], capture_output=True, text=True).stderr
        m = re.search(r'version "(\d+)(?:\.(\d+))?', out)
        if not m:
            return None
        major = int(m.group(1))
        return 8 if major == 1 else major
    except Exception:
        return None


def ensure_java(major):
    major = int(major)
    if sys.platform != "linux":
        exe = shutil.which("java")
        print("ℹ️  Sistema no Linux: uso la Java del sistema.", exe or "")
        return exe or "java"
    candidates = [f"/usr/lib/jvm/java-{major}-openjdk-amd64/bin/java"]
    if major == 8:
        candidates.append("/usr/lib/jvm/java-8-openjdk-amd64/bin/java")
    for c in candidates:
        if os.path.exists(c) and _java_major(c) == major:
            return c
    current = shutil.which("java")
    if current and _java_major(current) == major:
        return current
    if shutil.which("apt-get"):
        print(f"   Instalando Java {major} con apt…")
        sh("sudo apt-get update -qq")
        pkg = "openjdk-8-jre-headless" if major == 8 else f"openjdk-{major}-jre-headless"
        sh(f"sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq {pkg}")
        for c in candidates:
            if os.path.exists(c) and _java_major(c) == major:
                return c
    print(f"   Descargando Java {major} (Eclipse Temurin)…")
    assets = get_json(
        f"https://api.adoptium.net/v3/assets/latest/{major}/hotspot"
        "?architecture=x64&image_type=jre&os=linux&vendor=eclipse"
    )
    package = assets[0]["binary"]["package"]
    tgz = Path(f"/tmp/temurin-{major}.tar.gz")
    download(package["link"], tgz, sha256=package["checksum"])
    out = Path(f"/opt/temurin-{major}")
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True, exist_ok=True)
    safe_extract(tgz, out)
    exe = glob.glob(f"{out}/*/bin/java")[0]
    os.chmod(exe, 0o755)
    return exe


# ── Sincronización Drive ⇄ disco local ─────────────────────────────────────
HAS_RSYNC = shutil.which("rsync") is not None
if not HAS_RSYNC and shutil.which("apt-get"):
    sh("sudo apt-get update -qq && sudo apt-get install -y -qq rsync")
    HAS_RSYNC = shutil.which("rsync") is not None
if not HAS_RSYNC:
    print("ℹ️  rsync no está disponible: usaré copia directa (más lenta).")

RSYNC_OPTS = "--no-perms --no-owner --no-group --no-times --exclude logs --exclude cache --exclude crash-reports"


def sync_from_drive(clean=False):
    if clean:
        shutil.rmtree(SERVER_DIR, ignore_errors=True)
        SERVER_DIR.mkdir(parents=True, exist_ok=True)
    if not HAS_RSYNC:
        shutil.copytree(DRIVE_SERVER, SERVER_DIR, dirs_exist_ok=True)
        return
    r = sh(f'rsync -r {RSYNC_OPTS} "{DRIVE_SERVER}/" "{SERVER_DIR}/"')
    if r.returncode not in (0, 23, 24):
        print("⚠️  rsync avisó de un problema al copiar desde Drive.")


def sync_to_drive():
    print("📤 Guardando en Drive…")
    if not HAS_RSYNC:
        shutil.copytree(SERVER_DIR, DRIVE_SERVER, dirs_exist_ok=True)
        print("   ✅ guardado")
        return
    r = sh(f'rsync -r --delete {RSYNC_OPTS} --exclude "*.log" "{SERVER_DIR}/" "{DRIVE_SERVER}/"')
    print("   ✅ guardado" if r.returncode in (0, 23, 24) else "   ⚠️  revisa el aviso de rsync")


def sync_worlds():
    for w in sorted(SERVER_DIR.glob("world*")):
        if not w.is_dir():
            continue
        if HAS_RSYNC:
            sh(f'rsync -r --delete --no-perms --no-owner --no-group --no-times "{w}" "{DRIVE_SERVER}/"')
        else:
            shutil.copytree(w, DRIVE_SERVER / w.name, dirs_exist_ok=True)


def backup_world(tag="manual"):
    worlds = [w for w in SERVER_DIR.glob("world*") if w.is_dir()]
    if not worlds:
        return None
    out = BACKUP_DIR / f"world-{tag}-{datetime.now():%Y%m%d-%H%M%S}.tar.gz"
    with tarfile.open(out, "w:gz") as t:
        for w in worlds:
            t.add(w, arcname=w.name)
    for old in sorted(BACKUP_DIR.glob("world-*.tar.gz"))[:-3]:
        old.unlink(missing_ok=True)
    print(f"💾 backup: {out.name} ({out.stat().st_size / 1e6:.0f} MB)")
    return out


# ── Puesta a punto ─────────────────────────────────────────────────────────
def assert_stopped():
    """Evita tocar archivos mientras el servidor está escribiendo el mundo."""
    proc = globals().get("SERVER_PROC")
    if proc is not None and proc.poll() is None:
        raise RuntimeError("Hay un servidor corriendo. Para la celda 6 antes de continuar.")


assert_stopped()
if not re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z._+-]{0,31}", str(MC_VERSION)):
    raise RuntimeError(f"MC_VERSION='{MC_VERSION}' tiene caracteres no válidos.")
META = mc_meta(MC_VERSION)
JAVA_MAJOR = int(META["javaVersion"]["majorVersion"])
print(f"🎮 Minecraft {MC_VERSION} pide Java {JAVA_MAJOR}")
JAVA = os.environ.get("MCCOLAB_JAVA") or ensure_java(JAVA_MAJOR)
os.environ["JAVA_HOME"] = str(Path(JAVA).resolve().parent.parent)
os.environ["PATH"] = str(Path(JAVA).resolve().parent) + os.pathsep + os.environ.get("PATH", "")
print(f"☕ Java: {JAVA}")

first_time = not (SERVER_DIR / "server.properties").exists()
sync_from_drive(clean=first_time)
print(f"📁 Servidor local: {SERVER_DIR}")
print(f"☁️  Persistencia:   {DRIVE_ROOT}")
print("\n➡️  Siguiente: ejecuta la celda 3 para instalar el servidor.")
