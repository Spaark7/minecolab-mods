#@title 🧩 4. Descargar mods desde Modrinth { display-mode: "form" }
#@markdown Resuelve la versión compatible con tu `MC_VERSION` + loader, baja dependencias y limpia las que ya no uses.

import json, hashlib, re, urllib.parse
from pathlib import Path

MODRINTH = "https://api.modrinth.com/v2"
LOADER_TAGS = {
    "fabric": ["fabric"],
    "forge": ["forge"],
    "neoforge": ["neoforge"],
    "paper": ["paper", "bukkit", "spigot"],
    "vanilla": [],
}
LOADERS = LOADER_TAGS.get(SERVER_TYPE, [])
IS_PLUGIN_SERVER = SERVER_TYPE == "paper"
MOD_DIR = SERVER_DIR / ("plugins" if IS_PLUGIN_SERVER else "mods")
MOD_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_FILE = SERVER_DIR / ".minecolab_mods.json"


def modrinth_pick(project_id):
    query = urllib.parse.urlencode({
        "game_versions": json.dumps([MC_VERSION]),
        "loaders": json.dumps(LOADERS),
    })
    versions = get_json(f"{MODRINTH}/project/{project_id}/version?{query}")
    if not versions:
        return None
    for kind in ("release", "beta", "alpha"):
        pool = [v for v in versions if v.get("version_type") == kind]
        if pool:
            return sorted(pool, key=lambda v: v["date_published"])[-1]
    return None


def primary_file(ver):
    files = ver.get("files") or []
    preferred = [f for f in files if f.get("primary")] or files
    return preferred[0]


def resolve(key):
    """Devuelve (proyecto, versión) o lanza RuntimeError con el motivo."""
    key = str(key).strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", key):
        raise RuntimeError("nombre de proyecto no válido (usa el slug de Modrinth)")
    project = get_json(f"{MODRINTH}/project/{urllib.parse.quote(key, safe='')}")
    if project.get("project_type") == "modpack":
        raise RuntimeError("es un modpack, no un mod suelto")
    if project.get("server_side") == "unsupported":
        raise RuntimeError("solo funciona en el cliente")
    ver = modrinth_pick(project["id"])
    if not ver:
        raise RuntimeError(f"sin versión para {MC_VERSION}/{SERVER_TYPE}")
    if ver.get("environment") == "client_only":
        raise RuntimeError("solo funciona en el cliente")
    return project, ver


MODS = globals().get("MODS", [])
PLUGINS = globals().get("PLUGINS", [])

wanted = [str(m).strip() for m in MODS if str(m).strip()]
if IS_PLUGIN_SERVER:
    wanted += [str(p).strip() for p in PLUGINS if str(p).strip()]
if SERVER_TYPE == "fabric" and not any(m.lower() in ("fabric-api", "fabric_api") for m in wanted):
    wanted.insert(0, "fabric-api")
    print("ℹ️  Añadido fabric-api (obligatorio en Fabric).")

direct_urls = [m for m in wanted if m.startswith("http")]
wanted = [m for m in wanted if not m.startswith("http")]

if SERVER_TYPE == "vanilla" and (wanted or direct_urls):
    print("⚠️  vanilla no admite mods ni plugins: se ignora la lista. Usa fabric/neoforge/forge/paper.")
    wanted, direct_urls = [], []

chosen, skipped = {}, []


def add_with_deps(key, depth=0):
    if depth > 4:
        return
    try:
        project, ver = resolve(key)
    except Exception as exc:
        skipped.append((key, str(exc)))
        return
    if project["id"] in chosen:
        return
    chosen[project["id"]] = (project, ver)
    for dep in ver.get("dependencies", []):
        if dep.get("dependency_type") == "required" and dep.get("project_id"):
            add_with_deps(dep["project_id"], depth + 1)


for key in wanted:
    add_with_deps(key)

managed = set()
print(f"\n📦 {len(chosen)} proyecto(s) resueltos:\n")
for project, ver in chosen.values():
    f = primary_file(ver)
    dest = MOD_DIR / f["filename"]
    expected = (f.get("hashes") or {}).get("sha512")
    if dest.exists() and expected and hashlib.sha512(dest.read_bytes()).hexdigest() == expected:
        print(f"   = {project['slug']:<24} {ver['version_number']}")
    else:
        print(f"   + {project['slug']:<24} {ver['version_number']}")
        try:
            download(f["url"], dest, sha512=expected)
        except Exception as exc:
            skipped.append((project["slug"], str(exc)))
            continue
    managed.add(f["filename"])

for url in direct_urls:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        skipped.append((url, "solo se permiten enlaces http/https"))
        continue
    # El nombre debe ser un .jar simple: nada de "..", barras ni rutas codificadas.
    decoded = urllib.parse.unquote(parsed.path).replace("\\", "/")
    name = decoded.rsplit("/", 1)[-1]
    target = (MOD_DIR / name).resolve()
    if (
        ".." in decoded
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ._+()\[\]-]{0,120}\.jar", name, re.IGNORECASE)
        or target.parent != MOD_DIR.resolve()
    ):
        skipped.append((url, "el nombre del archivo no es un .jar válido"))
        continue
    if not target.exists():
        print(f"   + (url) {name}  (sin hash: confías en ese enlace)")
        try:
            download(url, target)
        except Exception as exc:
            target.unlink(missing_ok=True)
            skipped.append((url, f"no se pudo descargar ({exc})"))
            continue
    managed.add(name)

# Quitar mods que gestionamos antes y ya no están en la lista
old_managed = set()
if MANIFEST_FILE.exists():
    try:
        old_managed = set(json.loads(MANIFEST_FILE.read_text()))
    except Exception:
        pass
for name in sorted(old_managed - managed):
    target = MOD_DIR / name
    if target.exists():
        target.unlink()
        print(f"   🗑️  quitado {name}")
MANIFEST_FILE.write_text(json.dumps(sorted(managed), indent=2))

if skipped:
    print("\n⚠️  Omitidos:")
    for name, why in skipped:
        print(f"   · {name}: {why}")
if not chosen and not direct_urls:
    print("\n(No hay mods configurados. Edita la celda 1b cuando quieras.)")

print(f"\n📂 {MOD_DIR} → {len(managed)} archivo(s)")
print("Recuerda: los mods de cliente (shaders, minimapa) van solo en cada cliente.")
