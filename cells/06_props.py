#@title 🛠️ 5. Ajustes del servidor { display-mode: "form" }
#@markdown Escribe `server.properties` conservando lo que ya tengas, y aplica whitelist/ops al arrancar.

from pathlib import Path
import re

PROPS = SERVER_DIR / "server.properties"


def clean_name_list(names):
    """Solo nombres de Minecraft válidos (evita inyectar comandos en la consola)."""
    valid, bad = [], []
    for name in names:
        text = str(name).strip()
        (valid if re.fullmatch(r"[A-Za-z0-9_]{1,16}", text) else bad).append(text)
    if bad:
        print(f"⚠️  Ignorados (nombre no válido): {bad}")
    return valid


WHITELIST = clean_name_list(globals().get("WHITELIST", []))
OPS = clean_name_list(globals().get("OPS", []))
MOTD = re.sub(r"[\r\n]+", " ", str(MOTD))[:120]
SEED = re.sub(r"[\r\n]+", "", str(SEED))[:64]

FORCE = {
    "server-port": "25565",
    "motd": MOTD,
    "max-players": str(MAX_PLAYERS),
    "view-distance": str(VIEW_DISTANCE),
    "simulation-distance": str(max(4, VIEW_DISTANCE - 2)),
    "online-mode": "true" if ONLINE_MODE else "false",
    "enforce-secure-profile": "true" if ONLINE_MODE else "false",
    "allow-flight": "true",
    "enable-command-block": "true",
    "max-tick-time": "-1",
    "spawn-protection": "0",
    "sync-chunk-writes": "false",
    "enable-status": "true",
    "prevent-proxy-connections": "false",
}
if WHITELIST:
    FORCE["white-list"] = "true"
    FORCE["enforce-whitelist"] = "true"
if SEED:
    FORCE["level-seed"] = str(SEED)


def read_props(path):
    data = {}
    if path.exists():
        for line in path.read_text(errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    return data


props = read_props(PROPS)
created = not props
props.update(FORCE)
PROPS.write_text("#Minecraft server properties\n" + "\n".join(f"{k}={v}" for k, v in props.items()) + "\n")

print(("🆕 Creado" if created else "✏️  Actualizado") + f" {PROPS.name}")
for key in ("server-port", "motd", "max-players", "view-distance", "online-mode", "white-list", "level-seed"):
    if key in props:
        print(f"   {key:<18} = {props[key]}")

if WHITELIST:
    print(f"\n🔐 whitelist: {', '.join(WHITELIST)} (se aplica al arrancar)")
if OPS:
    print(f"👑 admins: {', '.join(OPS)} (se aplican al arrancar)")
print("\n➡️  Siguiente: celda 6, la que arranca el servidor.")
