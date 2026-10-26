#@title ⚙️ 1. Configuración del servidor { display-mode: "form" }
#@markdown Elige loader, versión y túnel. Luego baja a la celda siguiente para los mods.

SERVER_TYPE = "fabric" #@param ["fabric", "neoforge", "forge", "paper", "vanilla"]
MC_VERSION = "1.21.1" #@param {type:"string"}
TUNNEL = "playit" #@param ["playit", "bore", "ngrok", "ninguno"]
RAM_GB = 6 #@param [2, 3, 4, 5, 6, 8, 10, 12] {type:"raw"}
MAX_HORAS = 2 #@param {type:"number"}

# ── Notas rápidas ────────────────────────────────────────────────────────────
# fabric    → el mejor para mods. Necesita Fabric API (se añade solo).
# neoforge  → modpacks modernos (1.20.2 en adelante).
# forge     → modpacks clásicos (1.12.2, 1.16.5, 1.20.1…).
# paper     → sin mods, pero plugins y muy optimizado.
# vanilla   → el servidor oficial, sin mods ni plugins.
#
# MC_VERSION debe existir en Mojang y tener build del loader:
#   1.21.1, 1.21.4, 1.21.8, 26.1, 26.3 …
# Si un mod no tiene versión para la tuya, baja a una anterior (1.21.1 es la
# versión con más mods).
#
# TUNNEL: playit.gg = dirección fija y gratis (recomendado, requiere cuenta).
#         bore      = cero configuración, dirección temporal (bore.pub:12345).
#         ngrok     = su plan gratis ya no incluye TCP.
#         ninguno   = solo dentro de la sesión.

print(f"🎮 {SERVER_TYPE} · Minecraft {MC_VERSION} · {RAM_GB} GB de RAM")
print(f"🔗 túnel: {TUNNEL} · ⏱️  apagado automático a las {MAX_HORAS} h")
