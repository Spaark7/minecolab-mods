#!/usr/bin/env python3
"""Ensambla MineColab_Mods.ipynb a partir de las celdas en ./cells."""

import json
from pathlib import Path

HERE = Path(__file__).parent
CELLS_DIR = HERE / "cells"

ORDER = [
    ("md", "00_intro.md"),
    ("code", "01_config.py"),
    ("code", "02_mods_config.py"),
    ("code", "03_setup.py"),
    ("code", "04_install.py"),
    ("code", "05_mods.py"),
    ("code", "06_props.py"),
    ("code", "07_run.py"),
    ("code", "08_search.py"),
    ("code", "09_utils.py"),
]

cells = []
for index, (kind, name) in enumerate(ORDER):
    source = (CELLS_DIR / name).read_text(encoding="utf-8")
    cell_type = "markdown" if kind == "md" else "code"
    cell = {
        "cell_type": cell_type,
        "metadata": {"id": f"cell-{index:02d}-{name.split('_', 1)[0]}"},
        "source": source.splitlines(keepends=True),
    }
    if cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    cells.append(cell)

notebook = {
    "nbformat": 4,
    "nbformat_minor": 0,
    "metadata": {
        "colab": {
            "name": "MineColab_Mods.ipynb",
            "provenance": [],
            "toc_visible": True,
            "accelerator": "None",
        },
        "kernelspec": {
            "display_name": "Python 3",
            "name": "python3",
            "language": "python",
        },
        "language_info": {
            "name": "python",
            "version": "3.11",
            "mimetype": "text/x-python",
            "file_extension": ".py",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
        },
    },
    "cells": cells,
}

out = HERE / "MineColab_Mods.ipynb"
out.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"escrito {out} ({len(cells)} celdas, {out.stat().st_size / 1024:.1f} KB)")
