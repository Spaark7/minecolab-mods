#@title 🧩 1b. Mods y ajustes finos
#@markdown Escribe los **slugs de Modrinth** (la celda de búsqueda del final te ayuda a encontrarlos).
#@markdown También puedes pegar URLs directas a un `.jar` (CurseForge, GitHub, etc.).

# ── Mods del servidor (slugs de Modrinth o URLs .jar) ───────────────────────
MODS = [
    # "fabric-api",      # se añade automáticamente en fabric
    # "lithium",         # optimización de ticks (servidor + cliente)
    # "ferrite-core",    # menos uso de RAM
    # "chunky",          # pre-generar chunks sin lag
    # "spark",           # profiler: /spark tps
    # "https://ejemplo.com/mi-mod.jar",
]

# En paper/vanilla esto se descarga en plugins/ o se ignora.
PLUGINS = [
    # "luckperms",
    # "essentialsx",
]

# ── Red y jugadores ────────────────────────────────────────────────────────
MOTD = "MineColab — sesión de 2h"
MAX_PLAYERS = 10
VIEW_DISTANCE = 8            # 6–10 va bien en Colab; más = más lag
ONLINE_MODE = True           # False solo si usas clientes no oficiales
WHITELIST = []               # ["TuNombre", "Amigo123"]
OPS = []                     # admins: ["TuNombre"]
BACKUP_MIN = 10              # autoguardado a Drive cada N minutos
SEED = ""                    # "" = aleatoria

# ── Túnel (solo si TUNNEL == "ngrok") ─────────────────────────────────────
NGROK_AUTHTOKEN = ""         # https://dashboard.ngrok.com/get-started/your-authtoken

EXTRA_JVM_ARGS = ""          # p. ej. "-Dfml.queryResult=confirm"

print(f"Mods configurados: {len(MODS)} · plugins: {len(PLUGINS)}")
