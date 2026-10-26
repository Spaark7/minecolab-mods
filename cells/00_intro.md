# 🎮 MineColab Modded

Servidor de **Minecraft Java con mods** en Google Colab, pensado para sesiones
cortas (~2 h), no para tenerlo 24/7.

Basado en la idea de [thecoder-001/MineColab](https://github.com/thecoder-001/MineColab),
reescrito para versiones actuales (1.21.x, 26.x…), con **selector de versión y
loader**, descarga de **mods desde Modrinth** con sus dependencias, y **túnel**
(playit.gg con dirección fija, o bore.pub sin crear cuenta) para que entren tus
amigos sin abrir puertos.

### Cómo funciona

```
Google Drive (persistente)              Colab (rápido, se borra al terminar)
MineColab/server/  ──copia al inicio──▶  /content/mcserver/  ──▶  java … server.jar
   ├─ mods/                                (el servidor corre aquí)      │
   ├─ world/                                                             ▼
   └─ config/                                                    playit.gg / ngrok
MineColab/backups/  ◀── guardado al apagar / cada 10 min
```

El mundo, los mods y la configuración viven en **tu Drive**, así que puedes
cerrar la sesión y volver otro día sin perder nada.

### Orden de ejecución (una vez por sesión)

| # | Celda | Qué hace |
|---|-------|----------|
| 1 | Configuración | versión, loader, RAM, horas |
| 1b | Mods y ajustes | lista de mods, túnel, whitelist |
| 2 | Preparar entorno | monta Drive, instala Java, copia el servidor |
| 3 | Instalar servidor | descarga el jar/instalador del loader elegido |
| 4 | Mods | resuelve y descarga mods de Modrinth |
| 5 | Ajustes | `server.properties`, whitelist, admins |
| 6 | **Arrancar** | túnel + servidor + autoguardado + apagado a las 2 h |
| 7 | Buscar mods | buscador de Modrinth (opcional) |
| 8 | Extras | guardar ya, backups, restaurar, ver logs |

> ⚠️ **Antes de empezar**
> - Ejecuta las celdas **en orden**. La celda 6 se queda corriendo: mientras
>   esté activa, el servidor vive.
> - Mantén la pestaña de Colab abierta. Si Colab recicla la máquina, el servidor
>   muere (por eso el autoguardado cada 10 min).
> - Colab es gratis para uso interactivo; un servidor de juego consume recursos
>   que no están pensados para esto. Úsalo de forma moderada y no como hosting
>   permanente. Usar varias cuentas para saltarse límites puede hacer que te
>   restrinjan el acceso.
> - RAM del plan gratuito: ~12 GB en total. Deja 6–8 GB para el servidor.
> - Los **mods deben coincidir** en versión y loader entre el servidor y cada
>   cliente (tus amigos). Los mods de cliente (shaders, minimapa) van solo en el
>   cliente; este notebook omite automáticamente los que son `client_only`.
> - ¿Un mod o plugin no está en Modrinth? Sube el `.jar` a `MineColab/server/mods`
>   (o `.../plugins` en paper) desde Google Drive y aparecerá en la próxima sesión.
>   El notebook solo borra los archivos que él mismo descargó.
> - 🔐 **Seguridad:** montar Drive da a la VM acceso a **toda** tu unidad, y los
>   mods son código de terceros que corre como root. Usa una cuenta de Google
>   dedicada para el servidor, deja `ONLINE_MODE = true` y pon una `WHITELIST`.
>   Todo lo que se descarga se verifica por hash antes de ejecutarse (ver README).
