#@title 🔎 7. Buscar mods compatibles en Modrinth { display-mode: "form" }
#@markdown Busca por nombre y copia el *slug* que te guste en `MODS` (celda 1b). No instala nada.

import json, urllib.parse

MODRINTH = globals().get("MODRINTH", "https://api.modrinth.com/v2")
QUERY = "create" #@param {type:"string"}
CANTIDAD = 10 #@param {type:"slider", min:5, max:25, step:5}

facets = [["project_type:mod"], [f"versions:{MC_VERSION}"]]
loader_tag = {"fabric": "fabric", "forge": "forge", "neoforge": "neoforge", "paper": "paper"}.get(SERVER_TYPE)
if loader_tag:
    facets.append([f"categories:{loader_tag}"])

query = urllib.parse.urlencode({"query": QUERY, "limit": CANTIDAD, "facets": json.dumps(facets)})
results = get_json(f"{MODRINTH}/search?{query}")["hits"]

print(f"Resultados para '{QUERY}' en {SERVER_TYPE} {MC_VERSION}:\n")
for hit in results:
    server_side = {"required": "servidor", "optional": "ambos", "unsupported": "solo cliente"}.get(
        hit.get("server_side"), "?"
    )
    print(f"  {hit['slug']:<28} {hit['title'][:34]:<34} {hit['downloads']:>10,} descargas · {server_side}")

print("\nCopia los slugs en MODS (celda 1b) y vuelve a ejecutar la celda 4.")
