# MineColab Modded

Servidor de **Minecraft Java con mods en Google Colab** para sesiones cortas
(~2 h). Basado en [thecoder-001/MineColab](https://github.com/thecoder-001/MineColab),
reescrito porque el original quedó viejo (Paper API v2, Java 17 fijo, versiones
hasta 1.19).

**Archivo principal:** [`MineColab_Mods.ipynb`](MineColab_Mods.ipynb)

- Elige loader y versión: `fabric`, `neoforge`, `forge`, `paper`, `vanilla`.
- Elige la versión de Minecraft (1.12.2 → 26.x) y detecta sola la Java necesaria.
- Mods desde **Modrinth** por slug, con **dependencias automáticas**, filtro de
  mods de cliente y limpieza de los que quitas.
- Mundo, mods y configuración persisten en **Google Drive**.
- Túnel para amigos: **playit.gg** (dirección fija) o **bore.pub** (sin cuenta).
- Autoguardado cada 10 min, backup del mundo y **apagado automático** a las 2 h.

---

## 1. Puesta en marcha

1. Descarga `MineColab_Mods.ipynb`.
2. Entra en <https://colab.research.google.com> → **Archivo → Subir notebook**.
3. Ejecuta las celdas **en orden** (▶ o `Ctrl+Enter`):

| Celda | Qué hace | Tiempo |
|-------|----------|--------|
| 1 | Configuración (loader, versión, RAM, horas) | — |
| 1b | Lista de mods y ajustes | — |
| 2 | Monta Drive + instala la Java correcta | ~1 min |
| 3 | Descarga e instala el servidor | 1–3 min |
| 4 | Descarga mods de Modrinth | 10 s–2 min |
| 5 | `server.properties`, whitelist, admins | — |
| 6 | **Arranca servidor + túnel** (se queda corriendo) | — |
| 7 | Buscador de mods (opcional) | — |
| 8 | Guardar ya / backups / restaurar / ver log | — |

La primera vez que ejecutes la celda 2, Google te pedirá permiso para que Colab
acceda a tu Drive. Se crea la carpeta `Mi unidad/MineColab/`.

> La celda 6 **no termina** mientras juegas: es el servidor. No la pares hasta
> que quieras cerrar la sesión.

---

## 2. Configuración

### 2.1 Versión y loader (celda 1)

| Loader | Cuándo usarlo |
|--------|----------------|
| `fabric` | Recomendado para mods. Necesita Fabric API (se añade solo). |
| `neoforge` | Modpacks modernos (1.20.2+). |
| `forge` | Modpacks clásicos (1.12.2, 1.16.5, 1.20.1…). |
| `paper` | Sin mods; plugins y muy optimizado. |
| `vanilla` | Servidor oficial, sin mods ni plugins. |

Versiones que funcionan hoy (verificado contra Mojang/Paper/Fabric/NeoForge/Forge):
`1.21.1`, `1.21.4`, `1.21.8`, `26.1`, `26.3`… cualquiera que exista en el
manifiesto de Mojang y tenga build del loader.

> **Para mods, 1.21.1 es la apuesta segura**: es la versión con más mods
> actualizados. Si eliges la última (26.x), muchos mods todavía no tendrán
> versión y la celda 4 te dirá exactamente cuáles fallan.

La RAM se elige en `RAM_GB`. El plan gratuito de Colab tiene ~12 GB en total:
usa **6–8 GB** para un servidor con mods, **2–4 GB** para vanilla/paper.
El notebook comprueba la RAM real de la VM y **baja el heap solo** si te has
pasado (así Colab no mata la sesión a mitad de la generación del mundo).

### 2.2 Mods (celda 1b)

```python
MODS = [
    "lithium",        # slug de Modrinth
    "ferrite-core",
    "https://ejemplo.com/algun-mod.jar",   # URL directa
]
```

- El **slug** es lo que aparece al final de la URL de Modrinth:
  `modrinth.com/mod/lithium` → `lithium`.
- La celda 7 tiene un buscador: escribe "create", copia el slug y pégalo.
- Se bajan **dependencias obligatorias** automáticamente.
- Se omiten los mods `client_only` (minimapa, shaders, etc.).
- Si quitas un mod de la lista, la próxima ejecución borra su `.jar`.
- **Mods que no están en Modrinth**: súbelos a `Mi unidad/MineColab/server/mods/`
  desde la web de Drive. El notebook no los toca.
- Los mods deben estar **también en el cliente** de cada jugador, en la misma
  versión y loader.

### 2.3 Túnel

**playit.gg (recomendado, dirección fija)**
1. Ejecuta la celda 6.
2. En el log sale un enlace `https://playit.gg/claim/…`. Ábrelo y aprueba el
   agente (solo la primera vez).
3. En el panel de playit.gg crea un túnel **Minecraft Java** → `127.0.0.1:25565`.
4. Te da una dirección tipo `algo.playit.gg` que **no cambia** entre sesiones.
   El notebook también la detecta y la imprime en el log.
5. La clave del agente se guarda en tu Drive; la próxima sesión arranca ya
   vinculada, sin volver a reclamar.

> **Nota de versión:** desde playit 1.0 el binario `playit-linux-amd64` es solo
> el *daemon* (`playitd`) y se queda esperando a un frontend: no imprime el
> enlace de claim ni abre túnel. Por eso el notebook usa **v0.17.1**, que la
> propia documentación de playit marca como soportada y funciona sola.
> Si ves `Waiting for frontend secret provisioning over IPC`, estás con el
> binario equivocado (o con un notebook viejo).

**bore.pub (cero configuración)**
- Pon `TUNNEL = "bore"`. En 5 segundos tendrás `bore.pub:12345`.
- Sin cuenta, pero la dirección **cambia en cada sesión** y el relay es público
  y gratuito: úsalo para partidas puntuales, no para uso intensivo.

**ngrok**: su plan gratuito ya no incluye túneles TCP. Queda como opción legada.

**ninguno**: el servidor solo existe dentro de la VM de Colab.

Si playit muere o no conecta en ~2 minutos, el notebook cambia solo a bore para
que no te quedes sin partida (la dirección de bore te la imprime en el log).

---

## 3. Dónde queda todo

```
Mi unidad/MineColab/
├── server/                 # se copia a /content/mcserver en cada sesión
│   ├── world/              # tu mundo (¡y el nether/end!)
│   ├── mods/  o plugins/
│   ├── config/
│   └── server.properties
├── backups/                # 3 últimos .tar.gz del mundo
└── playit/                 # credenciales del agente
```

El servidor corre en el disco local de Colab (rápido) y se sincroniza con Drive
al arrancar, cada 10 minutos y al apagar. **No edites archivos dentro de
`/content/mcserver`** esperando que persistan: edita en Drive y reinicia la
sesión (o usa la celda 8 para guardar).

---

## 4. Problemas típicos

| Síntoma | Causa / solución |
|---------|------------------|
| "El servidor terminó antes de arrancar" | Mira las últimas líneas del log con la celda 8. Suele ser un mod incompatible o RAM insuficiente. |
| Un mod no aparece en la celda 4 | No tiene versión para tu `MC_VERSION`/loader. Baja de versión (1.21.1) o quita el mod. |
| Playit se queda en `Waiting for frontend secret provisioning over IPC` | Estás usando el binario 1.x, que es solo el daemon. Descarga el notebook actualizado (usa v0.17.1) o pon `TUNNEL = "bore"`. |
| Amigos no pueden entrar | Comprueba que el túnel esté vivo y que usen la dirección exacta (`bore.pub:PUERTO` cambia cada sesión). |
| "Incompatible client" / crash al entrar | El cliente necesita los mismos mods y la misma versión. |
| Colab dice "runtime disconnected" | Se recicló la máquina. Vuelve a ejecutar 2→6; el mundo está en Drive. |
| Se queda sin memoria | Baja `RAM_GB` o pon `VIEW_DISTANCE = 6`. |
| Colab se desconecta generando el mundo | Casi siempre RAM: pon `RAM_GB = 4` y prueba antes `SERVER_TYPE="vanilla"`, `MODS=[]`, `TUNNEL="ninguno"`. Si el aviso de Colab dice "se perdió la conexión" (no "RAM"), es la pestaña/red: deja Colab visible y sin dormir. El notebook guarda `Mi unidad/MineColab/arranque.log` durante el arranque para ver hasta dónde llegó. |
| La sesión se corta a las 2 h | Es el `MAX_HORAS` que pediste. Súbelo si quieres más (máx. práctico ~10 h). |
| Quiero restaurar el mundo de ayer | Celda 8 → `ACCION = "restaurar backup"` + nombre del `.tar.gz`. |

---

## 5. Límites honestos

- Colab es gratuito **para uso interactivo**, no es un hosting. Google puede
  limitar o cortar sesiones, y usar varias cuentas para saltarse los límites
  puede hacer que te restrinjan el acceso. Para algo permanente, usa un VPS.
- Sesión máxima real: ~12 h (y el plan gratuito suele reciclar antes).
- Sin GPU no hace falta: el servidor va a CPU.
- El mundo es tuyo: haz backups antes de cambiar de versión o de loader.

---

## 6. Seguridad

Lo que el notebook hace para no exponerte:

- **Todo se verifica por hash** antes de ejecutarse: Mojang (SHA-1), Paper
  (SHA-256), Fabric (SHA-256), Forge/NeoForge (SHA-1), Modrinth (SHA-512),
  Temurin (SHA-256), playit y bore (SHA-256). Si un byte no coincide, el archivo
  se borra y no se ejecuta.
- **Solo se descarga de dominios oficiales**: `piston-meta.mojang.com`,
  `fill.papermc.io`, `meta.fabricmc.net`, `maven.fabricmc.net`,
  `maven.neoforged.net`, `maven.minecraftforge.net`, `api.modrinth.com`,
  `api.adoptium.net` y los releases de GitHub de playit y bore.
- **Nombres y versiones saneados**: `MC_VERSION` y las versiones de loader se
  validan con regex y se citan con `shlex.quote`; los slugs de Modrinth también.
  No se puede inyectar un comando desde la celda de configuración.
- **Sin path traversal**: las URLs directas de mods solo se aceptan si el
  archivo es un `.jar` simple (se rechazan `..`, `%2F` y rutas absolutas), y los
  `.tar.gz` se extraen con comprobación de rutas y sin enlaces simbólicos.
- **Sin descargas silenciosas**: si un enlace directo o un mod falla, se omite y
  se explica; nunca se ejecuta a medias.

Lo que **no** puede protegerte, y conviene que sepas:

- **Los mods son código de terceros sin sandbox.** Un mod de Modrinth corre
  dentro del servidor con permisos de root en la VM de Colab. Modrinth filtra
  malware, pero no es una garantía. Usa mods populares y revisa el autor.
- **Montar Drive da acceso a toda tu unidad.** `drive.mount()` monta tu Google
  Drive completo en la VM; cualquier código que corras ahí puede leerlo. Usa una
  cuenta dedicada para el servidor, no tu cuenta personal.
- **El túnel ve el tráfico, pero no lo entiende.** playit y bore son relays:
  con `ONLINE_MODE = true` el tráfico de Minecraft va cifrado de extremo a
  extremo, así que el relay no puede leer contraseñas ni chat.
- **Abre solo a quien conozcas.** Sin `WHITELIST`, cualquiera con la dirección
  puede entrar. Con `ONLINE_MODE = false` cualquiera puede suplantar a otro
  jugador: déjalo en `true` salvo que sepas exactamente por qué lo cambias.
- **Colab no es un hosting.** No guardes secretos reales en el notebook: las
  celdas y las salidas pueden quedar en el historial de tu cuenta.

Recomendación mínima: `ONLINE_MODE = true`, `WHITELIST` con tus amigos, cuenta
de Google dedicada y `TUNNEL = "playit"` o `"bore"`.

---

## 7. Desarrollo

El notebook se genera desde las celdas sueltas de `cells/`:

```bash
python3 build.py          # reescribe MineColab_Mods.ipynb
python3 test_local.py     # prueba real: instala fabric 1.21.1, baja mods y arranca
```

`test_local.py` necesita Java 21 (o define `MCCOLAB_JAVA`) y usa
`/private/tmp/opencode` como Drive simulado. Los tests `test_loaders*.py`
verifican Paper, Forge y NeoForge.
