#@title 🧰 8. Extras: guardar, backups, restaurar, ver log { display-mode: "form" }
#@markdown Con el servidor parado. `ACCION` hace lo que dice; `BACKUP` es el nombre exacto del archivo.

from pathlib import Path
import re

ACCION = "solo listar" #@param ["solo listar", "guardar ahora", "backup del mundo", "restaurar backup", "ver últimas líneas del log"]
BACKUP = "" #@param {type:"string"}

running = globals().get("SERVER_PROC")
if running is not None and running.poll() is None:
    print("⚠️  El servidor sigue corriendo. Para esta celda primero (o usa /stop).")

if ACCION == "guardar ahora":
    sync_to_drive()
elif ACCION == "backup del mundo":
    backup_world("manual")
    sync_to_drive()
elif ACCION == "restaurar backup":
    if not BACKUP:
        print("Escribe el nombre del backup en el campo BACKUP (mira la lista de abajo).")
    elif not re.fullmatch(r"world-[A-Za-z0-9_.-]+\.tar\.gz", BACKUP):
        print("Nombre de backup no válido.")
    else:
        origin = BACKUP_DIR / BACKUP
        if not origin.exists():
            print("No existe:", origin)
        else:
            trash = SERVER_DIR.parent / ("mundos-viejos-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
            trash.mkdir(parents=True, exist_ok=True)
            for world in SERVER_DIR.glob("world*"):
                if world.is_dir():
                    shutil.move(str(world), str(trash / world.name))
            safe_extract(origin, SERVER_DIR)
            print(f"✅ Restaurado {origin.name} (lo anterior quedó en {trash})")
            sync_to_drive()
elif ACCION == "ver últimas líneas del log":
    log = SERVER_DIR / "logs" / "latest.log"
    print("\n".join(log.read_text(errors="ignore").splitlines()[-60:]) if log.exists() else "Todavía no hay logs.")

backups = sorted(BACKUP_DIR.glob("world-*.tar.gz"))
print("\n💾 Backups en Drive (se conservan los 3 últimos):")
for b in backups:
    print(f"   {b.name:<42} {b.stat().st_size / 1e6:>7.0f} MB")
print(f"\n📁 local: {SERVER_DIR}\n☁️  Drive: {DRIVE_ROOT}")
