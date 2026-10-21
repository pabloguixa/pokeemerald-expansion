#!/usr/bin/env python3
"""
Randomizer del hack Emerald Nuzlocke.

Uso (desde la carpeta raíz del proyecto pokeemerald-expansion):
    python3 randomizer/randomize.py            # semilla aleatoria
    python3 randomizer/randomize.py 1234       # semilla fija (mismo resultado siempre)

Siempre parte de los archivos originales (se guardan una sola vez en
randomizer/_original/), así que puedes ejecutarlo tantas veces como quieras.
Después: make -j$(nproc)

Partes hechas: 1 · Iniciales  ·  2 · Rival  ·  3 · Rutas  ·  4 · Evoluciones por intercambio  ·  5 · Entrenadores y líderes.
"""
import json
import random
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / "randomizer"
ORIG = HERE / "_original"
OUT = HERE / "output"

# Archivos del juego que toca el randomizer (se respaldan la primera vez).
FILES = [
    "src/starter_choose.c",
    "src/data/trainers.party",
    "src/data/wild_encounters.json",
    "src/caps.c",
] + [f"src/data/pokemon/species_info/gen_{g}_families.h" for g in range(1, 10)]

# 115 líneas evolutivas de 3 etapas (incluye bebés, excluye Cosmog).
STARTER_POOL = [
    "SPECIES_BULBASAUR", "SPECIES_CHARMANDER", "SPECIES_SQUIRTLE", "SPECIES_CATERPIE",
    "SPECIES_WEEDLE", "SPECIES_PIDGEY", "SPECIES_NIDORAN_F", "SPECIES_NIDORAN_M",
    "SPECIES_ZUBAT", "SPECIES_ODDISH", "SPECIES_MANKEY", "SPECIES_POLIWAG",
    "SPECIES_ABRA", "SPECIES_MACHOP", "SPECIES_BELLSPROUT", "SPECIES_GEODUDE",
    "SPECIES_MAGNEMITE", "SPECIES_GASTLY", "SPECIES_RHYHORN", "SPECIES_HORSEA",
    "SPECIES_PORYGON", "SPECIES_DRATINI", "SPECIES_CHIKORITA", "SPECIES_CYNDAQUIL",
    "SPECIES_TOTODILE", "SPECIES_PICHU", "SPECIES_CLEFFA", "SPECIES_IGGLYBUFF",
    "SPECIES_TOGEPI", "SPECIES_MAREEP", "SPECIES_HOPPIP", "SPECIES_TEDDIURSA",
    "SPECIES_SWINUB", "SPECIES_ELEKID", "SPECIES_MAGBY", "SPECIES_LARVITAR",
    "SPECIES_TREECKO", "SPECIES_TORCHIC", "SPECIES_MUDKIP", "SPECIES_ZIGZAGOON",
    "SPECIES_WURMPLE", "SPECIES_LOTAD", "SPECIES_SEEDOT", "SPECIES_RALTS",
    "SPECIES_SLAKOTH", "SPECIES_WHISMUR", "SPECIES_AZURILL", "SPECIES_ARON",
    "SPECIES_TRAPINCH", "SPECIES_DUSKULL", "SPECIES_SPHEAL", "SPECIES_BAGON",
    "SPECIES_BELDUM", "SPECIES_TURTWIG", "SPECIES_CHIMCHAR", "SPECIES_PIPLUP",
    "SPECIES_STARLY", "SPECIES_SHINX", "SPECIES_BUDEW", "SPECIES_MIME_JR",
    "SPECIES_HAPPINY", "SPECIES_GIBLE", "SPECIES_SNIVY", "SPECIES_TEPIG",
    "SPECIES_OSHAWOTT", "SPECIES_LILLIPUP", "SPECIES_PIDOVE", "SPECIES_ROGGENROLA",
    "SPECIES_TIMBURR", "SPECIES_TYMPOLE", "SPECIES_SEWADDLE", "SPECIES_VENIPEDE",
    "SPECIES_SANDILE", "SPECIES_GOTHITA", "SPECIES_SOLOSIS", "SPECIES_VANILLITE",
    "SPECIES_KLINK", "SPECIES_TYNAMO", "SPECIES_LITWICK", "SPECIES_AXEW",
    "SPECIES_PAWNIARD", "SPECIES_DEINO", "SPECIES_CHESPIN", "SPECIES_FENNEKIN",
    "SPECIES_FROAKIE", "SPECIES_FLETCHLING", "SPECIES_SCATTERBUG", "SPECIES_FLABEBE",
    "SPECIES_HONEDGE", "SPECIES_GOOMY", "SPECIES_ROWLET", "SPECIES_LITTEN",
    "SPECIES_POPPLIO", "SPECIES_PIKIPEK", "SPECIES_GRUBBIN", "SPECIES_BOUNSWEET",
    "SPECIES_JANGMO_O", "SPECIES_GROOKEY", "SPECIES_SCORBUNNY", "SPECIES_SOBBLE",
    "SPECIES_ROOKIDEE", "SPECIES_BLIPBUG", "SPECIES_ROLYCOLY", "SPECIES_APPLIN",
    "SPECIES_HATENNA", "SPECIES_IMPIDIMP", "SPECIES_DREEPY", "SPECIES_SPRIGATITO",
    "SPECIES_FUECOCO", "SPECIES_QUAXLY", "SPECIES_PAWMI", "SPECIES_SMOLIV",
    "SPECIES_NACLI", "SPECIES_TINKATINK", "SPECIES_FRIGIBAX",
]


def backup_originals():
    """Copia los archivos originales la primera vez y devuelve su texto."""
    texts = {}
    for rel in FILES:
        src = ROOT / rel
        dst = ORIG / rel
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  copia original guardada: {rel}")
        texts[rel] = dst.read_text(encoding="utf-8")
    return texts


def check_species(names):
    """Avisa si algún nombre no existe en include/constants/species.h."""
    header = (ROOT / "include/constants/species.h").read_text(encoding="utf-8")
    missing = [n for n in names if not re.search(r"\b" + n + r"\s*=", header)]
    if missing:
        sys.exit(f"ERROR: especies no encontradas en species.h: {missing}")


def pretty(species):
    return species.replace("SPECIES_", "").replace("_", " ").title()


def randomize_starters(text, rng):
    starters = rng.sample(STARTER_POOL, 3)
    slots = ["GRASS_STARTER", "FIRE_STARTER", "WATER_STARTER"]
    for slot, species in zip(slots, starters):
        pattern = re.compile(r"^#define " + slot + r"\b.*$", re.M)
        if not pattern.search(text):
            sys.exit(f"ERROR: no encuentro '#define {slot}' en starter_choose.c")
        text = pattern.sub(f"#define {slot} {species}", text, count=1)
    return text, starters


# --------------------------------------------------------------------------
# Datos de especies (tipos y evoluciones) leídos del propio proyecto
# --------------------------------------------------------------------------
SPECIES_INFO_DIR = "src/data/pokemon/species_info"


STAT_FIELDS = ["baseHP", "baseAttack", "baseDefense", "baseSpeed", "baseSpAttack", "baseSpDefense"]
FLAG_FIELDS = ["isRestrictedLegendary", "isSubLegendary", "isMythical", "isUltraBeast", "isParadox",
               "isAlolanForm", "isGalarianForm", "isHisuianForm", "isPaldeanForm",
               "isTotem", "isMegaEvolution", "isGigantamax", "isPrimalReversion", "isTeraForm"]


def _stat_value(raw, defines):
    raw = raw.strip()
    for _ in range(3):
        if raw in defines:
            raw = defines[raw]
    if "?" in raw:
        raw = raw.split("?", 1)[1]
    m = re.search(r"\d+", raw)
    return int(m.group()) if m else 0


def load_species_db(originals):
    """Devuelve {SPECIES_X: {"types", "evos", "bst", flags...}} leyendo los archivos originales."""
    db = {}
    for rel in sorted(k for k in originals if k.startswith(SPECIES_INFO_DIR)):
        text = originals[rel]
        defines = dict(re.findall(r"^\s*#define\s+(\w+)\s+(.+?)\s*$", text, re.M))
        starts = [(m.start(), m.group(1)) for m in re.finditer(r"^\s*\[(SPECIES_\w+)\]\s*=", text, re.M)]
        for i, (pos, name) in enumerate(starts):
            end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
            body = text[pos:end]
            t = re.search(r"\.types\s*=\s*MON_TYPES\(([^)]*)\)", body)
            types = [x.strip() for x in t.group(1).split(",")] if t else []
            evos = []
            e = re.search(r"\.evolutions\s*=\s*EVOLUTION\((.*?)\),\s*\n", body, re.S)
            if e:
                for m in re.finditer(r"\{(EVO_\w+),\s*([^,]+),\s*(SPECIES_\w+)", e.group(1)):
                    lvl = m.group(2).strip()
                    evos.append((m.group(1), int(lvl) if lvl.isdigit() else 0, m.group(3)))
            bst = 0
            for f in STAT_FIELDS:
                sm = re.search(r"\." + f + r"\s*=\s*([^,\n]+)", body)
                if sm:
                    bst += _stat_value(sm.group(1), defines)
            a = re.search(r"\.abilities\s*=\s*\{([^}]*)\}", body)
            abilities = [x.strip() for x in a.group(1).split(",")] if a else []
            info = {"types": types, "evos": evos, "bst": bst, "abilities": abilities}
            for f in FLAG_FIELDS:
                info[f] = bool(re.search(r"\." + f + r"\s*=\s*TRUE", body))
            if name not in db:
                db[name] = info
    return db


def load_aliases():
    """SPECIES_DEOXYS -> SPECIES_DEOXYS_NORMAL, etc."""
    header = (ROOT / "include/constants/species.h").read_text(encoding="utf-8")
    return dict(re.findall(r"\b(SPECIES_\w+)\s*=\s*(SPECIES_\w+)\s*,", header))


def resolve(name, aliases):
    for _ in range(5):
        if name in aliases:
            name = aliases[name]
    return name


def national_dex_species(aliases):
    """Las 1025 especies base (una por número de Pokédex), con su nombre de bloque de datos."""
    text = (ROOT / "include/constants/pokedex.h").read_text(encoding="utf-8")
    enum = text.split("NATIONAL_DEX_COUNT")[0]
    names = []
    for n in re.findall(r"^\s*NATIONAL_DEX_(\w+)\s*,", enum, re.M):
        if n != "NONE" and ("SPECIES_" + n) not in names:
            names.append("SPECIES_" + n)
    return [resolve(n, aliases) for n in names]


def is_legend(info):
    return any(info[f] for f in ["isRestrictedLegendary", "isSubLegendary", "isMythical", "isUltraBeast", "isParadox"])


# Tabla de tipos: TYPE_CHART[atacante][defensor] = multiplicador (solo lo que no es x1).
_T = "NORMAL FIRE WATER ELECTRIC GRASS ICE FIGHTING POISON GROUND FLYING PSYCHIC BUG ROCK GHOST DRAGON DARK STEEL FAIRY".split()
_SE = {  # supereficaz
    "FIRE": "GRASS ICE BUG STEEL", "WATER": "FIRE GROUND ROCK", "ELECTRIC": "WATER FLYING",
    "GRASS": "WATER GROUND ROCK", "ICE": "GRASS GROUND FLYING DRAGON",
    "FIGHTING": "NORMAL ICE ROCK DARK STEEL", "POISON": "GRASS FAIRY", "GROUND": "FIRE ELECTRIC POISON ROCK STEEL",
    "FLYING": "GRASS FIGHTING BUG", "PSYCHIC": "FIGHTING POISON", "BUG": "GRASS PSYCHIC DARK",
    "ROCK": "FIRE ICE FLYING BUG", "GHOST": "PSYCHIC GHOST", "DRAGON": "DRAGON", "DARK": "PSYCHIC GHOST",
    "STEEL": "ICE ROCK FAIRY", "FAIRY": "FIGHTING DRAGON DARK",
}
_NVE = {  # poco eficaz
    "NORMAL": "ROCK STEEL", "FIRE": "FIRE WATER ROCK DRAGON", "WATER": "WATER GRASS DRAGON",
    "ELECTRIC": "ELECTRIC GRASS DRAGON", "GRASS": "FIRE GRASS POISON FLYING BUG DRAGON STEEL",
    "ICE": "FIRE WATER ICE STEEL", "FIGHTING": "POISON FLYING PSYCHIC BUG FAIRY", "POISON": "POISON GROUND ROCK GHOST",
    "GROUND": "GRASS BUG", "FLYING": "ELECTRIC ROCK STEEL", "PSYCHIC": "PSYCHIC STEEL",
    "BUG": "FIRE FIGHTING POISON FLYING GHOST STEEL FAIRY", "ROCK": "FIGHTING GROUND STEEL", "GHOST": "DARK",
    "DRAGON": "STEEL", "DARK": "FIGHTING DARK FAIRY", "STEEL": "FIRE WATER ELECTRIC STEEL", "FAIRY": "FIRE POISON STEEL",
}
_IMM = {"NORMAL": "GHOST", "ELECTRIC": "GROUND", "FIGHTING": "GHOST", "POISON": "STEEL",
        "GROUND": "FLYING", "PSYCHIC": "DARK", "GHOST": "NORMAL", "DRAGON": "FAIRY"}


def type_mult(atk, defender_types):
    a = atk.replace("TYPE_", "")
    m = 1.0
    for d in defender_types:
        d = d.replace("TYPE_", "")
        if d in _SE.get(a, "").split():
            m *= 2
        elif d in _NVE.get(a, "").split():
            m *= 0.5
        elif d in _IMM.get(a, "").split():
            m *= 0
    return m


def best_hit(attacker_types, defender_types):
    return max((type_mult(t, defender_types) for t in attacker_types), default=1.0)


# --------------------------------------------------------------------------
# Líneas evolutivas
# --------------------------------------------------------------------------
def choose_line(db, base, rng):
    """Elige (de forma fija por semilla) una rama: lista de (especie, metodo, nivel) desde la base."""
    line = [(base, None, 0)]
    cur = base
    seen = {base}
    while db.get(cur, {}).get("evos"):
        evos = [e for e in db[cur]["evos"] if e[2] in db and e[2] not in seen]
        if not evos:
            break
        method, lvl, nxt = rng.choice(evos)
        line.append((nxt, method, lvl))
        seen.add(nxt)
        cur = nxt
    return line


def stage_for_level(line, level, min_stage):
    """Etapa que le toca a un Pokémon de rival con este nivel.
    Evoluciona por nivel si lo alcanza; si la evolución no es por nivel
    (piedra, amistad, intercambio...) evoluciona si el original ya estaba en esa etapa."""
    stage = 0
    for i in range(1, len(line)):
        _, method, lvl = line[i]
        if method == "EVO_LEVEL" and lvl > 0:
            ok = level >= lvl
        else:
            ok = min_stage >= i
        if not ok:
            break
        stage = i
    return line[stage][0]


# --------------------------------------------------------------------------
# Parte 2 · Rival (Bruno / Aura)
# --------------------------------------------------------------------------
# Sufijo del combate = inicial que eligió el JUGADOR (posición 0, 1, 2 de la mochila).
SUFFIX_SLOT = {"TREECKO": 0, "TORCHIC": 1, "MUDKIP": 2}
ORIGINAL_LINES = [
    ["Treecko", "Grovyle", "Sceptile"],
    ["Torchic", "Combusken", "Blaziken"],
    ["Mudkip", "Marshtomp", "Swampert"],
]
ORIGINAL_STAGE = {name.upper(): (slot, stage) for slot, l in enumerate(ORIGINAL_LINES) for stage, name in enumerate(l)}


def pick_rival_slots(db, lines, rng):
    """Para cada inicial del jugador, el rival lleva el de los otros dos que mejor le planta cara."""
    finals = [db[l[-1][0]]["types"] for l in lines]
    choice = {}
    for p in range(3):
        best, best_score = [], None
        for r in range(3):
            if r == p:
                continue
            score = best_hit(finals[r], finals[p]) - best_hit(finals[p], finals[r])
            if best_score is None or score > best_score:
                best, best_score = [r], score
            elif score == best_score:
                best.append(r)
        choice[p] = rng.choice(best)
    return choice


def randomize_rival(text, db, lines, rng):
    rival_slot = pick_rival_slots(db, lines, rng)
    blocks = re.split(r"(?m)^(?==== TRAINER_)", text)
    changed = 0
    for bi, block in enumerate(blocks):
        m = re.match(r"=== TRAINER_(MAY|BRENDAN)_\w+_(TREECKO|TORCHIC|MUDKIP) ===", block)
        if not m:
            continue
        line = lines[rival_slot[SUFFIX_SLOT[m.group(2)]]]
        mons = block.split("\n\n")
        for mi, mon in enumerate(mons):
            first, _, rest = mon.partition("\n")
            sm = re.match(r"^(\s*)([A-Za-z]+)\b(.*)$", first)
            if not sm or sm.group(2).upper() not in ORIGINAL_STAGE:
                continue
            _, orig_stage = ORIGINAL_STAGE[sm.group(2).upper()]
            lv = re.search(r"^Level:\s*(\d+)", rest, re.M)
            level = int(lv.group(1)) if lv else 5
            species = stage_for_level(line, level, orig_stage)
            mons[mi] = sm.group(1) + species + sm.group(3) + ("\n" + rest if rest else "")
            changed += 1
        blocks[bi] = "\n\n".join(mons)
    if changed == 0:
        sys.exit("ERROR: no he encontrado los combates del rival en trainers.party")
    return "".join(blocks), rival_slot, changed


# --------------------------------------------------------------------------
# Parte 3 · Rutas (Pokémon salvajes)
# --------------------------------------------------------------------------
ENCOUNTER_KINDS = ["land_mons", "water_mons", "rock_smash_mons", "fishing_mons"]
STORY_LEGENDS = {"SPECIES_GROUDON", "SPECIES_KYOGRE", "SPECIES_RAYQUAZA"}
LEGEND_MIN_LEVEL = 25        # a partir de aquí (mitad del juego) pueden salir legendarios
LEGEND_MAP_CHANCE = 0.25     # % de zonas de mitad de juego en adelante con un legendario en el hueco del 1%


def build_pools(db, aliases):
    dex = [s for s in national_dex_species(aliases) if s in db]
    special = ("isTotem", "isMegaEvolution", "isGigantamax", "isPrimalReversion", "isTeraForm")
    regional = [s for s, i in db.items()
                if (i["isAlolanForm"] or i["isGalarianForm"] or i["isHisuianForm"] or i["isPaldeanForm"])
                and not any(i[f] for f in special) and not s.endswith("_ZEN")]   # Zen = forma de combate
    everyone = list(dict.fromkeys(dex + regional))
    normal = [s for s in everyone if not is_legend(db[s]) and db[s]["bst"] > 0]
    # En estado salvaje: subleyendas, míticos, ultraentes y paradojas. Los legendarios
    # de caja (Mewtwo, Lugia, Zacian...) se reservan para los encuentros fijos.
    legends = [s for s in everyone if is_legend(db[s]) and not db[s]["isRestrictedLegendary"]
               and s not in STORY_LEGENDS and db[s]["bst"] > 0]
    return normal, legends


def compute_level_info(db):
    """Para cada especie: nivel mínimo razonable para verla y nivel al que evoluciona (si es por nivel)."""
    pre = {}
    for sp, info in db.items():
        for method, lvl, nxt in info["evos"]:
            pre.setdefault(nxt, (sp, method, lvl))
    min_lv, depth = {}, {}

    def calc(sp, seen=()):
        if sp in min_lv:
            return min_lv[sp], depth[sp]
        if sp not in pre or sp in seen:
            min_lv[sp], depth[sp] = 1, 0
            return 1, 0
        p, method, lvl = pre[sp]
        pl, pd = calc(p, seen + (sp,))
        d = pd + 1
        if method == "EVO_LEVEL" and lvl > 0:
            l = max(pl, lvl)
        else:                         # piedra, amistad, intercambio...
            l = max(pl, 18 if d == 1 else 32)
        min_lv[sp], depth[sp] = l, d
        return l, d

    evolves_at = {}
    for sp, info in db.items():
        calc(sp)
        lv = [lvl for method, lvl, _ in info["evos"] if method == "EVO_LEVEL" and lvl > 0]
        if lv:
            evolves_at[sp] = min(lv)
    return min_lv, evolves_at


def bst_cap(level):
    """Potencia máxima permitida según el nivel del hueco."""
    return 330 + 7 * level


def allowed_at(sp, level, db, min_lv, evolves_at):
    if min_lv.get(sp, 1) > level + 2:          # aún no le tocaría existir (Garchomp en la Ruta 101)
        return False
    if sp in evolves_at and evolves_at[sp] < level - 6:   # ya debería haber evolucionado (Caterpie a nivel 40)
        return False
    return db[sp]["bst"] <= bst_cap(level)


def pick_for_slot(level, pool, db, min_lv, evolves_at, usage, rng, exclude=()):
    """Cualquier especie que tenga sentido a ese nivel; entre ellas, la menos usada hasta ahora."""
    cands = [s for s in pool if s not in exclude and allowed_at(s, level, db, min_lv, evolves_at)]
    if not cands:
        cands = [s for s in pool if s not in exclude] or list(pool)
    low = min(usage.get(s, 0) for s in cands)
    best = [s for s in cands if usage.get(s, 0) == low]
    choice = rng.choice(best)
    usage[choice] = usage.get(choice, 0) + 1
    return choice


def map_level(entry):
    """Nivel típico de la zona: el de la hierba si la hay (surf y caña llegan más tarde)."""
    kinds = ["land_mons"] if "land_mons" in entry else ENCOUNTER_KINDS
    levels = [m["max_level"] for k in kinds if k in entry for m in entry[k]["mons"]]
    return sum(levels) / len(levels) if levels else 0


def randomize_routes(text, db, aliases, rng):
    data = json.loads(text)
    normal, legends = build_pools(db, aliases)
    usage, legend_usage = {}, {}
    min_lv, evolves_at = compute_level_info(db)
    report = []
    group = next(g for g in data["wild_encounter_groups"] if g["label"] == "gWildMonHeaders")
    for entry in group["encounters"]:
        # Hueco por hueco: cada hueco de la zona tiene una especie distinta
        # (12 en la hierba), elegida entre todas las que encajan con su nivel.
        zone = set()
        for kind in ENCOUNTER_KINDS:
            if kind not in entry:
                continue
            for mon in entry[kind]["mons"]:
                mon["species"] = pick_for_slot(mon["max_level"], normal, db, min_lv, evolves_at,
                                               usage, rng, exclude=zone)
                zone.add(mon["species"])
        legend = None
        lvl = map_level(entry)
        if "land_mons" in entry and lvl >= LEGEND_MIN_LEVEL and rng.random() < LEGEND_MAP_CHANCE:
            slot = entry["land_mons"]["mons"][-1]          # el hueco del 1 %
            low = min(legend_usage.get(s, 0) for s in legends)
            legend = rng.choice([s for s in legends if legend_usage.get(s, 0) == low])
            legend_usage[legend] = legend_usage.get(legend, 0) + 1
            slot["species"] = legend
        report.append({"map": entry["map"], "level": round(lvl),
                       "species": sorted(zone), "legend": legend})
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n", report


# --------------------------------------------------------------------------
# Parte 4 · Evoluciones por intercambio
# --------------------------------------------------------------------------
TRADE_LEVEL = 36
# Objetos que NO existen en el Esmeralda original: habrá que ponerlos a la venta o en el mapa.
NOT_IN_EMERALD = {"ITEM_UPGRADE", "ITEM_DUBIOUS_DISC", "ITEM_PROTECTOR", "ITEM_ELECTIRIZER",
                  "ITEM_MAGMARIZER", "ITEM_REAPER_CLOTH", "ITEM_PRISM_SCALE", "ITEM_SACHET",
                  "ITEM_WHIPPED_DREAM", "ITEM_LINKING_CORD"}

_TRADE_RE = re.compile(r"\{EVO_TRADE,\s*0,\s*(SPECIES_\w+)(?:,\s*CONDITIONS\(\{(IF_\w+),\s*(\w+)\}\))?\}")


def convert_trade_evolutions(texts):
    """Intercambio simple o con pareja -> nivel 36.  Intercambio con objeto -> usar el objeto como una piedra."""
    changes = []

    def repl(m):
        target, cond, arg = m.group(1), m.group(2), m.group(3)
        if cond == "IF_HOLD_ITEM":
            changes.append((target, arg))
            return "{EVO_ITEM, " + arg + ", " + target + "}"
        changes.append((target, f"nivel {TRADE_LEVEL}"))
        return "{EVO_LEVEL, " + str(TRADE_LEVEL) + ", " + target + "}"

    out = {}
    for rel, text in texts.items():
        out[rel] = _TRADE_RE.sub(repl, text)
    return out, changes


# --------------------------------------------------------------------------
# Parte 5 · Entrenadores, líderes, Alto Mando y rival (resto del equipo)
# --------------------------------------------------------------------------
LEVEL_MULT = 1.10            # +10 % de nivel a todos los entrenadores
LEADERS = {                  # en orden de medalla
    "ROXANNE": "TYPE_ROCK", "BRAWLY": "TYPE_FIGHTING", "WATTSON": "TYPE_ELECTRIC",
    "FLANNERY": "TYPE_FIRE", "NORMAN": "TYPE_NORMAL", "WINONA": "TYPE_FLYING",
    "TATE_AND_LIZA": "TYPE_PSYCHIC", "JUAN": "TYPE_WATER",
}
ELITE = {"SIDNEY": "TYPE_DARK", "PHOEBE": "TYPE_GHOST", "GLACIA": "TYPE_ICE",
         "DRAKE": "TYPE_DRAGON", "WALLACE": "TYPE_WATER"}
LEADER_TEAM_SIZE = [3, 3, 4, 4, 5, 5, 6, 6]   # el equipo crece con cada medalla
REMATCH_TEAM_SIZE = 6
ELITE_TEAM_SIZE = 6
IVS_REGULAR, IVS_BOSS, IVS_CHAMPION = 15, 25, 31
KEEP_FIELDS = ("Nature:", "Shiny:", "Ball:", "Happiness:", "EVs:")


def species_name_index(aliases):
    """'Mr. Mime' -> SPECIES_MR_MIME, etc. (para leer los nombres del archivo de entrenadores)."""
    header = (ROOT / "include/constants/species.h").read_text(encoding="utf-8")
    idx = {}
    for name in re.findall(r"\b(SPECIES_\w+)\s*=", header):
        key = re.sub(r"[^A-Z0-9]", "", name[len("SPECIES_"):])
        idx.setdefault(key, name)
    return idx


def name_to_species(raw, idx, aliases):
    raw = raw.strip()
    if raw.startswith("SPECIES_"):
        return resolve(raw, aliases)
    key = re.sub(r"[^A-Z0-9]", "", raw.upper().replace("♂", "M").replace("♀", "F"))
    sp = idx.get(key)
    return resolve(sp, aliases) if sp else None


class Lines:
    """Ayudas sobre líneas evolutivas: base, etapa y ramas."""

    def __init__(self, db):
        self.db = db
        self.pre = {}
        for sp, info in db.items():
            for _, _, nxt in info["evos"]:
                self.pre.setdefault(nxt, sp)

    def base(self, sp):
        seen = set()
        while sp in self.pre and sp not in seen:
            seen.add(sp)
            sp = self.pre[sp]
        return sp

    def stage(self, sp):
        d, seen = 0, set()
        while sp in self.pre and sp not in seen:
            seen.add(sp)
            sp = self.pre[sp]
            d += 1
        return d

    def is_final(self, sp):
        return not [e for e in self.db[sp]["evos"] if e[2] in self.db]

    def line_through(self, sp, rng):
        """Línea completa (base -> ... -> sp -> ...) con el formato de choose_line."""
        path = [sp]
        while path[0] in self.pre and self.pre[path[0]] not in path:
            path.insert(0, self.pre[path[0]])
        line = [(path[0], None, 0)]
        for a, b in zip(path, path[1:]):
            m = next(e for e in self.db[a]["evos"] if e[2] == b)
            line.append((b, m[0], m[1]))
        tail = choose_line(self.db, sp, rng)
        return line + tail[1:]


def parse_mon(text):
    lines = text.strip("\n").split("\n")
    first = lines[0]
    if first.startswith(("/*", "//", "*")) or not any(l.startswith("Level:") for l in lines):
        return None
    m = re.match(r"^(.*?)(?:\s*@\s*(.+))?$", first)
    name_part, item = m.group(1).strip(), m.group(2)
    nick = re.match(r"^.*\(([^()]+)\)\s*(?:\((?:M|F)\))?$", name_part)
    if nick and nick.group(1) not in ("M", "F"):
        species_raw = nick.group(1)
    else:
        species_raw = re.sub(r"\s*\((?:M|F)\)$", "", name_part)
    level = int(re.search(r"^Level:\s*(\d+)", text, re.M).group(1))
    keep = [l for l in lines[1:] if l.startswith(KEEP_FIELDS)]
    return {"species_raw": species_raw, "item": item, "level": level, "keep": keep}


def render_mon(species, item, level, ivs, keep, ability=None):
    out = [species + (f" @ {item}" if item else ""), f"Level: {level}",
           "IVs: " + " / ".join(f"{ivs} {s}" for s in ["HP", "Atk", "Def", "SpA", "SpD", "Spe"])]
    if ability:
        out.append(f"Ability: {ability}")
    return "\n".join(out + keep)


def ace_ability(db, species):
    """El as lleva su habilidad oculta (suele ser la más útil); si no tiene, la primera."""
    abil = [a for a in db[species].get("abilities", []) if a and a != "ABILITY_NONE"]
    if not abil:
        return None
    raw = db[species]["abilities"]
    hidden = raw[2] if len(raw) > 2 and raw[2] not in ("", "ABILITY_NONE") else None
    return hidden or abil[0]


class TrainerRandomizer:
    def __init__(self, db, aliases, normal, rng):
        self.db, self.rng = db, rng
        self.aliases = aliases
        self.idx = species_name_index(aliases)
        self.L = Lines(db)
        self.pool = normal
        self.min_lv, self.evolves_at = compute_level_info(db)
        self.usage = {}
        self.memory = {}          # (nombre del entrenador, base original) -> línea nueva
        self.ace = {}             # nombre del líder -> especie del as (igual en las revanchas)
        self.unknown = set()

    def candidates(self, level, type_=None, exclude=(), final_only=False):
        def ok(s, strict):
            if s in exclude:
                return False
            if type_ and type_ not in self.db[s]["types"]:
                return False
            if final_only and not self.L.is_final(s):
                return False
            if strict:
                return allowed_at(s, level, self.db, self.min_lv, self.evolves_at)
            return self.db[s]["bst"] <= bst_cap(level) + 60
        c = [s for s in self.pool if ok(s, True)]
        if not c:
            c = [s for s in self.pool if ok(s, False)]
        if not c:
            c = [s for s in self.pool if s not in exclude and (not type_ or type_ in self.db[s]["types"])]
        return c

    def pick(self, cands):
        low = min(self.usage.get(s, 0) for s in cands)
        choice = self.rng.choice([s for s in cands if self.usage.get(s, 0) == low])
        self.usage[choice] = self.usage.get(choice, 0) + 1
        return choice

    def species_for(self, who, orig, level, type_, team):
        """Especie nueva para un Pokémon de entrenador, coherente entre combates del mismo entrenador."""
        orig_stage = self.L.stage(orig) if orig in self.db else 0
        key = (who, self.L.base(orig) if orig in self.db else orig)
        if key in self.memory:
            sp = stage_for_level(self.memory[key], level, orig_stage)
            if sp not in team:
                return sp
        sp = self.pick(self.candidates(level, type_, exclude=team))
        self.memory[key] = self.L.line_through(sp, self.rng)
        return sp

    def ace_for(self, who, level, type_, team):
        if who in self.ace and self.ace[who] not in team:
            return self.ace[who]
        sp = self.pick(self.candidates(level, type_, exclude=team, final_only=True))
        self.ace[who] = sp
        return sp


def trainer_role(const):
    """('leader', NOMBRE, nº medalla, es_revancha) / ('elite', NOMBRE) / ('rival', ...) / ('regular', ...)."""
    base = re.sub(r"_\d+$", "", const)
    if base in LEADERS:
        return "leader", base, list(LEADERS).index(base), not const.endswith("_1")
    if const in ELITE:
        return "elite", const, None, False
    if re.match(r"(MAY|BRENDAN)_", const):
        return "rival", base, None, False
    return "regular", base, None, False


def randomize_trainers(text, db, aliases, normal, rng):
    tr = TrainerRandomizer(db, aliases, normal, rng)
    head, sep, body = text.partition("=== TRAINER_")
    blocks = re.split(r"(?m)^(?==== TRAINER_)", sep + body)
    leaders_report, ace_levels = {}, {}
    out = []
    for block in blocks:
        m = re.match(r"=== TRAINER_(\w+) ===", block)
        if not m:
            out.append(block)
            continue
        const = m.group(1)
        role, who, badge, rematch = trainer_role(const)
        name = re.search(r"^Name:\s*(.*)$", block, re.M)
        who_key = (name.group(1).strip() if name else who) + "|" + who.split("_")[0]
        parts = block.rstrip("\n").split("\n\n")
        header, mon_parts = parts[0], parts[1:]
        mons = [(p, parse_mon(p)) for p in mon_parts]
        real = [x for x in mons if x[1]]
        if not real:
            out.append(block)
            continue
        type_ = LEADERS.get(who) or ELITE.get(who)
        ivs = IVS_REGULAR
        if role in ("leader", "elite", "rival"):
            ivs = IVS_BOSS
        if who == "WALLACE":
            ivs = IVS_CHAMPION
        team, new_parts = [], []
        n_real = len(real)
        for i, (raw, mon) in enumerate(mons):
            if not mon:
                new_parts.append(raw)
                continue
            level = min(100, round(mon["level"] * LEVEL_MULT))
            orig = name_to_species(mon["species_raw"], tr.idx, aliases)
            if role == "rival" and mon["species_raw"].upper() in ORIGINAL_STAGE:
                sp = mon["species_raw"]                    # el inicial del rival lo pone la parte 2
            elif orig is None:
                tr.unknown.add(mon["species_raw"])
                sp = mon["species_raw"]
            elif type_ and real[-1][0] is raw:             # el último de un líder/Alto Mando: el as
                sp = tr.ace_for(who, level, type_, team)
            else:
                sp = tr.species_for(who_key, orig, level, type_, team)
            team.append(sp)
            is_ace = bool(type_) and real[-1][0] is raw and sp in db
            new_parts.append(render_mon(sp, mon["item"], level, ivs, mon["keep"],
                                        ace_ability(db, sp) if is_ace else None))
        # Equipos que crecen (líderes y Alto Mando): se añaden Pokémon antes del as
        if type_:
            if role == "leader":
                target = REMATCH_TEAM_SIZE if rematch else LEADER_TEAM_SIZE[badge]
            else:
                target = ELITE_TEAM_SIZE
            mon_idx = [i for i, (_, mon) in enumerate(mons) if mon]
            ace_pos = mon_idx[-1]
            fill_level = min(100, round(mons[mon_idx[-2]][1]["level"] * LEVEL_MULT)) if len(mon_idx) > 1 \
                else max(1, round(mons[ace_pos][1]["level"] * LEVEL_MULT) - 2)
            k = 0
            while len(team) < target:
                sp = tr.species_for(who_key, f"EXTRA_{k}", fill_level, type_, team)
                team.insert(-1, sp)
                new_parts.insert(ace_pos, render_mon(sp, None, fill_level, ivs, []))
                ace_pos += 1
                k += 1
            levels = [int(re.search(r"Level: (\d+)", p).group(1)) for p in new_parts if re.search(r"^Level:", p, re.M)]
            leaders_report[const] = [{"species": pretty(x), "level": l} for x, l in zip(team, levels)]
            if role == "leader" and not rematch:
                ace_levels[badge] = max(levels)
            if who == "WALLACE":
                ace_levels["champion"] = max(levels)
        out.append("\n\n".join([header] + new_parts) + "\n\n")
    if tr.unknown:
        print("  Aviso: nombres no reconocidos (se dejan igual):", ", ".join(sorted(tr.unknown)))
    return head + "".join(out).rstrip("\n") + "\n", leaders_report, ace_levels


def update_level_caps(text, ace_levels):
    """El límite de cada medalla = nivel del as del siguiente líder (ya con el +10 %)."""
    for badge in range(8):
        if badge in ace_levels:
            text = re.sub(r"(\{FLAG_BADGE0" + str(badge + 1) + r"_GET,\s*)\d+(\})",
                          lambda m: m.group(1) + str(ace_levels[badge]) + m.group(2), text)
    if "champion" in ace_levels:
        text = re.sub(r"(\{FLAG_IS_CHAMPION,\s*)\d+(\})",
                      lambda m: m.group(1) + str(ace_levels["champion"]) + m.group(2), text)
    return text


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else random.randrange(1, 10**6)
    rng = random.Random(seed)
    print(f"Semilla: {seed}")

    originals = backup_originals()
    check_species(STARTER_POOL)
    db = load_species_db(originals)
    aliases = load_aliases()

    result = {"seed": seed}

    text, starters = randomize_starters(originals["src/starter_choose.c"], rng)
    (ROOT / "src/starter_choose.c").write_text(text, encoding="utf-8")
    result["starters"] = starters
    print("Iniciales:", ", ".join(pretty(s) for s in starters))

    # Líneas evolutivas fijas de cada inicial (la rama se decide aquí, con la semilla)
    lines = [choose_line(db, s, rng) for s in starters]
    result["starter_lines"] = [[x[0] for x in l] for l in lines]

    normal_pool, _ = build_pools(db, aliases)
    trainers_text, leaders_report, ace_levels = randomize_trainers(
        originals["src/data/trainers.party"], db, aliases, normal_pool, rng)
    result["leaders"] = leaders_report
    caps = update_level_caps(originals["src/caps.c"], ace_levels)
    (ROOT / "src/caps.c").write_text(caps, encoding="utf-8")
    result["level_caps"] = {str(k): v for k, v in ace_levels.items()}
    print("Entrenadores: +10 % de nivel; líderes y Alto Mando por tipo con as final")
    print("  Límites de nivel:", ", ".join(str(ace_levels[b]) for b in range(8) if b in ace_levels),
          "· Campeón:", ace_levels.get("champion"))

    text, rival_slot, n = randomize_rival(trainers_text, db, lines, rng)
    (ROOT / "src/data/trainers.party").write_text(text, encoding="utf-8")
    result["rival"] = {pretty(starters[p]): pretty(starters[r]) for p, r in rival_slot.items()}
    print(f"Rival ({n} Pokémon cambiados):")
    for p, r in rival_slot.items():
        print(f"  si eliges {pretty(starters[p])} -> el rival lleva {pretty(starters[r])}")

    text, report = randomize_routes(originals["src/data/wild_encounters.json"], db, aliases, rng)
    (ROOT / "src/data/wild_encounters.json").write_text(text, encoding="utf-8")
    result["routes"] = report
    n_leg = sum(1 for r in report if r["legend"])
    print(f"Rutas: {len(report)} zonas randomizadas, {n_leg} con un legendario escondido (1 %)")

    species_files = {k: v for k, v in originals.items() if k.startswith(SPECIES_INFO_DIR)}
    new_files, changes = convert_trade_evolutions(species_files)
    for rel, text in new_files.items():
        (ROOT / rel).write_text(text, encoding="utf-8")
    result["trade_evolutions"] = [{"species": pretty(t), "how": h} for t, h in changes]
    needed = sorted({h for _, h in changes if h in NOT_IN_EMERALD})
    result["items_to_place"] = needed
    print(f"Evoluciones por intercambio: {len(changes)} cambiadas (nivel {TRADE_LEVEL} u objeto)")
    if needed:
        print("  Objetos que habrá que poner en el juego:", ", ".join(n.replace("ITEM_", "").title() for n in needed))

    OUT.mkdir(exist_ok=True)
    (OUT / "last_run.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("Resumen guardado en randomizer/output/last_run.json")
    print("Ahora compila: make -j$(nproc)")


if __name__ == "__main__":
    main()
