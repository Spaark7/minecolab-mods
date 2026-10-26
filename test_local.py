#!/usr/bin/env python3
"""Prueba local de las celdas del notebook (sin Colab): instala fabric 1.21.1,
descarga mods de Modrinth, escribe server.properties y arranca el servidor ~1 min."""

import os, sys
from pathlib import Path

os.environ["MCCOLAB_DRIVE"] = "/private/tmp/opencode/mcdrive"
os.environ["MCCOLAB_SERVER"] = "/private/tmp/opencode/mcserver-test"
os.environ["MCCOLAB_JAVA"] = "/private/tmp/opencode/java21/jdk-21.0.13+9-jre/Contents/Home/bin/java"
os.environ["SSL_CERT_FILE"] = "/etc/ssl/cert.pem"

CELLS = Path(__file__).parent / "cells"
ns = {"__name__": "__main__"}


def run_cell(name):
    print(f"\n{'=' * 70}\n▶ {name}\n{'=' * 70}")
    code = (CELLS / name).read_text()
    exec(compile(code, name, "exec"), ns)


run_cell("01_config.py")
run_cell("02_mods_config.py")

ns.update(
    SERVER_TYPE="fabric",
    MC_VERSION="1.21.1",
    TUNNEL="ninguno",
    RAM_GB=2,
    MAX_HORAS=0.001,
    MODS=["fabric-api", "lithium"],
    VIEW_DISTANCE=4,
    BACKUP_MIN=1,
    MOTD="test local",
)

run_cell("03_setup.py")
run_cell("04_install.py")
run_cell("05_mods.py")
run_cell("06_props.py")
run_cell("07_run.py")
run_cell("08_search.py")
run_cell("09_utils.py")
print("\nTEST COMPLETO")
