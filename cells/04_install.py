#@title 📦 3. Instalar el servidor { display-mode: "form" }
#@markdown Descarga el loader elegido. Es idempotente: si ya está instalado, no vuelve a bajar nada.

import json, re, shlex, shutil, glob
from pathlib import Path

STATE_FILE = SERVER_DIR / ".minecolab_state.json"
EULA_FILE = SERVER_DIR / "eula.txt"


def ram_disponible_gb():
    """RAM real de la VM (cgroup de Colab), no la del host."""
    candidatos = []
    for ruta in ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"):
        try:
            valor = Path(ruta).read_text().strip()
            if valor.isdigit():
                candidatos.append(int(valor) / 1e9)
        except Exception:
            pass
    try:
        for linea in Path("/proc/meminfo").read_text().splitlines():
            if linea.startswith("MemTotal:"):
                candidatos.append(int(linea.split()[1]) / 1e6)
                break
    except Exception:
        pass
    candidatos = [c for c in candidatos if 1 < c < 100000]
    return min(candidatos) if candidatos else None


def jvm_flags():
    global RAM_EFECTIVA_GB
    gb = int(RAM_GB)
    limite = ram_disponible_gb()
    if limite:
        seguro = max(2, int(limite - 2))
        if gb > seguro:
            print(f"⚠️  RAM_GB={gb} no cabe en esta VM ({limite:.1f} GB). Bajo a {seguro} GB.")
            gb = seguro
    RAM_EFECTIVA_GB = gb
    flags = [
        f"-Xms{min(gb, 2)}G", f"-Xmx{gb}G",
        "-XX:+UseG1GC", "-XX:+ParallelRefProcEnabled", "-XX:MaxGCPauseMillis=200",
        "-XX:+UnlockExperimentalVMOptions", "-XX:+DisableExplicitGC",
        "-XX:+ExitOnOutOfMemoryError",
        "-XX:G1NewSizePercent=30", "-XX:G1MaxNewSizePercent=40", "-XX:G1HeapRegionSize=8M",
        "-XX:G1ReservePercent=20", "-XX:G1HeapWastePercent=5", "-XX:G1MixedGCCountTarget=4",
        "-XX:InitiatingHeapOccupancyPercent=15", "-XX:G1MixedGCLiveThresholdPercent=90",
        "-XX:G1RSetUpdatingPauseTimePercent=5", "-XX:SurvivorRatio=32",
        "-XX:+PerfDisableSharedMem", "-XX:MaxTenuringThreshold=1",
    ]
    if EXTRA_JVM_ARGS.strip():
        flags += EXTRA_JVM_ARGS.split()
    return flags


def vkey(v):
    return tuple(int(x) for x in re.findall(r"\d+", v))


# ── Resolución de descargas (url, detalle, hashes) ──────────────────────────
def resolve_vanilla(mc):
    meta = mc_meta(mc)
    server = meta["downloads"]["server"]
    return server["url"], "oficial", {"sha1": server["sha1"]}


def resolve_paper(mc):
    data = get_json(f"https://fill.papermc.io/v3/projects/paper/versions/{mc}/builds")
    if not isinstance(data, list) or not data:
        raise RuntimeError(f"Paper no tiene builds para {mc} (prueba 1.21.8, 1.21.1, 26.3…).")
    builds = [b for b in data if b.get("channel") == "STABLE"] or data
    b = builds[0]
    jar = b["downloads"]["server:default"]
    return jar["url"], f"build {b['id']}", {"sha256": jar["checksums"]["sha256"]}


def resolve_fabric(mc):
    inst = next(i for i in get_json("https://meta.fabricmc.net/v2/versions/installer") if i.get("stable"))
    loaders = get_json(f"https://meta.fabricmc.net/v2/versions/loader/{urllib.parse.quote(mc)}")
    if not loaders:
        raise RuntimeError(f"Fabric no soporta {mc} todavía.")
    return inst["url"], loaders[0]["loader"]["version"], {"sha256": fetch_text(inst["url"] + ".sha256")}


def resolve_neoforge(mc):
    prefix = "47." if mc == "1.20.1" else (mc[2:] if mc.startswith("1.") else mc) + "."
    versions = get_json(
        "https://maven.neoforged.net/api/maven/versions/releases/net/neoforged/neoforge"
    )["versions"]
    cands = sorted({v for v in versions if v.startswith(prefix) and "-" not in v}, key=vkey)
    if not cands:
        raise RuntimeError(f"NeoForge no tiene versión para {mc} (prueba 1.21.1, 1.21.8, 26.3…).")
    v = cands[-1]
    url = f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{v}/neoforge-{v}-installer.jar"
    return url, v, {"sha1": fetch_text(url + ".sha1")}


def resolve_forge(mc):
    promos = get_json("https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json")["promos"]
    fv = promos.get(f"{mc}-recommended") or promos.get(f"{mc}-latest")
    if not fv:
        raise RuntimeError(
            f"Forge no publica para {mc}. Usa neoforge/fabric o una versión clásica (1.12.2, 1.16.5, 1.20.1)."
        )
    url = f"https://maven.minecraftforge.net/net/minecraftforge/forge/{mc}-{fv}/forge-{mc}-{fv}-installer.jar"
    return url, fv, {"sha1": fetch_text(url + ".sha1")}


def resolve_any(kind, mc):
    fn = {"vanilla": resolve_vanilla, "paper": resolve_paper, "fabric": resolve_fabric,
          "neoforge": resolve_neoforge, "forge": resolve_forge}[kind]
    return fn(mc)


# ── Comando de arranque ────────────────────────────────────────────────────
def launch_argv():
    if SERVER_TYPE in ("vanilla", "paper"):
        return [JAVA, *jvm_flags(), "-jar", "server.jar", "nogui"]
    if SERVER_TYPE == "fabric":
        jar = "fabric-server-launch.jar"
        if not (SERVER_DIR / jar).exists():
            found = sorted(SERVER_DIR.glob("fabric-server-*.jar"))
            if not found:
                raise RuntimeError("No encuentro el lanzador de Fabric. Reinstala la celda 3.")
            jar = found[0].name
        return [JAVA, *jvm_flags(), "-jar", jar, "nogui"]
    if (SERVER_DIR / "run.sh").exists():
        for pattern in (
            "libraries/net/neoforged/neoforge/*/unix_args.txt",
            "libraries/net/minecraftforge/forge/*/unix_args.txt",
        ):
            found = sorted(SERVER_DIR.glob(pattern))
            if found:
                args_file = found[0].relative_to(SERVER_DIR)
                return [JAVA, "@user_jvm_args.txt", "@" + str(args_file), "nogui"]
        return ["bash", "run.sh", "nogui"]
    for pattern in ("forge-*-universal.jar", "neoforge-*-universal.jar"):
        found = sorted(SERVER_DIR.glob(pattern))
        if found:
            return [JAVA, *jvm_flags(), "-jar", found[0].name, "nogui"]
    raise RuntimeError("No encuentro cómo arrancar Forge/NeoForge. Reinstala la celda 3.")


def load_state():
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def save_state(d):
    STATE_FILE.write_text(json.dumps(d, indent=2))


KEEP = {
    "world", "world_nether", "world_the_end", "mods", "plugins", "config", "defaultconfigs",
    "server.properties", "eula.txt", "ops.json", "whitelist.json", "banned-ips.json",
    "banned-players.json", "usercache.json", "server-icon.png", "user_jvm_args.txt",
    ".minecolab_state.json", ".minecolab_mods.json",
}


def clean_old_install():
    for entry in SERVER_DIR.iterdir():
        if entry.name in KEEP:
            continue
        if entry.is_dir():
            shutil.rmtree(entry, ignore_errors=True)
        else:
            entry.unlink(missing_ok=True)


# === INSTALL ===
assert_stopped()
state = load_state()
already = (
    state.get("type") == SERVER_TYPE
    and state.get("mc") == MC_VERSION
    and EULA_FILE.exists()
)
if already:
    try:
        launch_argv()
    except Exception:
        already = False

if already:
    print(f"✅ Ya instalado: {SERVER_TYPE} {MC_VERSION} (nada que descargar)")
else:
    print(f"📦 Instalando {SERVER_TYPE} {MC_VERSION}…")
    clean_old_install()
    url, extra, hashes = resolve_any(SERVER_TYPE, MC_VERSION)
    if SERVER_TYPE in ("fabric", "forge", "neoforge") and not re.fullmatch(
        r"[0-9A-Za-z._+-]{1,64}", str(extra)
    ):
        raise RuntimeError(f"Versión de loader no válida: {extra!r}")
    print(f"   fuente: {url.split('/')[2]} · {extra}")

    if SERVER_TYPE in ("vanilla", "paper"):
        download(url, SERVER_DIR / "server.jar", **hashes)
    elif SERVER_TYPE == "fabric":
        installer = download(url, SERVER_DIR / "fabric-installer.jar", **hashes)
        sh(
            f"cd {shlex.quote(str(SERVER_DIR))} && {shlex.quote(JAVA)} -jar "
            f"{shlex.quote(installer.name)} server -mcversion {shlex.quote(str(MC_VERSION))} "
            f"-loader {shlex.quote(str(extra))} -downloadMinecraft",
            check=True, quiet=False,
        )
    else:
        installer = download(url, SERVER_DIR / "installer.jar", **hashes)
        sh(
            f"cd {shlex.quote(str(SERVER_DIR))} && {shlex.quote(JAVA)} -jar "
            f"{shlex.quote(installer.name)} --installServer",
            check=True, quiet=False,
        )
        installer.unlink(missing_ok=True)
        (SERVER_DIR / "installer.jar.log").unlink(missing_ok=True)

    if SERVER_TYPE in ("forge", "neoforge"):
        # run.sh / unix_args leen los flags de aquí; se reescribe cada vez por si cambias RAM_GB
        (SERVER_DIR / "user_jvm_args.txt").write_text("\n".join(jvm_flags()) + "\n")

    EULA_FILE.write_text(
        "# Al poner eula=true aceptas la EULA de Minecraft: https://aka.ms/MinecraftEULA\n"
        "eula=true\n"
    )
    save_state({"type": SERVER_TYPE, "mc": MC_VERSION, "loader": extra})
    print("✅ Instalación terminada")

if SERVER_TYPE in ("forge", "neoforge"):
    (SERVER_DIR / "user_jvm_args.txt").write_text("\n".join(jvm_flags()) + "\n")

missing = [p for p in ("eula.txt",) if not (SERVER_DIR / p).exists()]
if missing:
    print("⚠️  Falta:", missing)
print("\n➡️  Siguiente: celda 4 (mods) y celda 5 (ajustes).")
