# Mana Forge — Character Generator & World Toolkit (2025 Rewritten, Immersive Infinite Story)
# Streamlit app with local JSON persistence (save/load anywhere), reactive story, world time, background events
# Author: (you)

import os
import json
import time
import random
from io import BytesIO
from typing import Dict, List, Any, Optional

import streamlit as st
import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth

# --------------------------------
# OpenAI (modern SDK)
# --------------------------------
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

# --------------------------------
# Constants & Config
# --------------------------------
APP_TITLE = "🎭 Mana Forge — Character Generator & Toolkit"
DATA_DIR = "data"
TEXT_MODEL = st.secrets.get("OPENAI_TEXT_MODEL", "gpt-4o-mini")
IMAGE_MODEL = st.secrets.get("OPENAI_IMAGE_MODEL", "gpt-image-1")
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")

os.makedirs(DATA_DIR, exist_ok=True)

# --------------------------------
# Helpers — Persistence (disk)
# --------------------------------
def _save_json(path: str, obj: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def _load_json(path: str, default: Any):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

STATE_FILES = {
    "characters": os.path.join(DATA_DIR, "characters.json"),
    "parties": os.path.join(DATA_DIR, "parties.json"),
    "stories": os.path.join(DATA_DIR, "stories.json"),
    "worlds": os.path.join(DATA_DIR, "worlds.json"),
    "journals": os.path.join(DATA_DIR, "journals.json"),
    "infinite_story": os.path.join(DATA_DIR, "infinite_story.json"),   # padrão local, mas você pode salvar em qualquer lugar
}

# --------------------------------
# Session State init/load
# --------------------------------
for key in ["characters", "parties", "stories", "worlds", "journals", "infinite_story"]:
    if key not in st.session_state:
        default = [] if key != "worlds" else []
        st.session_state[key] = _load_json(STATE_FILES[key], default)

# extra state para o modo imersivo
st.session_state.setdefault("world_time", 0)              # dias
st.session_state.setdefault("event_log", [])              # lista de eventos (dict)
st.session_state.setdefault("pending_choices", None)      # dict com {prompt, options:[...], context}
st.session_state.setdefault("story_mood", "Neutral")      # humor global simples
st.session_state.setdefault("active_world_name", None)    # vincular história a um "world"

# --------------------------------
# Static tables
# --------------------------------
RACES = [
    "Human", "Elf", "Dwarf", "Halfling", "Gnome", "Half-Orc", "Tiefling",
    "Dragonborn", "Kobold", "Lizardfolk", "Minotaur", "Troll", "Vampire",
    "Satyr", "Undead", "Lich", "Werewolf"
]

CLASSES = [
    "Fighter", "Wizard", "Rogue", "Cleric", "Barbarian", "Sorcerer", "Bard",
    "Monk", "Druid", "Ranger", "Paladin", "Warlock", "Artificer", "Blood Hunter",
    "Mystic", "Warden", "Berserker", "Necromancer", "Trickster", "Beast Master",
    "Alchemist", "Pyromancer", "Dark Knight"
]

BACKGROUNDS = [
    "Acolyte", "Folk Hero", "Sage", "Criminal", "Noble", "Hermit", "Outlander",
    "Entertainer", "Artisan", "Sailor", "Soldier", "Charlatan", "Knight", "Pirate",
    "Spy", "Archaeologist", "Gladiator", "Inheritor", "Haunted One", "Bounty Hunter",
    "Explorer", "Watcher", "Traveler", "Phantom", "Vigilante"
]

GENDERS = ["Male", "Female", "Non-binary"]
IMAGE_STYLES = ["Standard", "8bit Style", "Anime Style"]

# --------------------------------
# OpenAI client + robust calls
# --------------------------------
@st.cache_resource(show_spinner=False)
def get_openai_client():
    if OpenAI is None:
        st.error("OpenAI SDK não instalado. Adicione 'openai' >= 1.0 ao requirements.")
        return None
    if not OPENAI_API_KEY:
        st.error("Falta OPENAI_API_KEY em st.secrets")
        return None
    try:
        return OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        st.error(f"Falha ao iniciar OpenAI: {e}")
        return None

def call_chat(messages: List[Dict[str, str]], model: str = TEXT_MODEL, **kwargs) -> str:
    client = get_openai_client()
    if client is None:
        return ""
    for attempt in range(4):
        try:
            resp = client.chat.completions.create(model=model, messages=messages, **kwargs)
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            if attempt == 3:
                st.error(f"OpenAI chat error: {e}")
                return ""
            time.sleep(0.75 * (attempt + 1))
    return ""

def call_image(prompt: str, model: str = IMAGE_MODEL, size: str = "1024x1024") -> Dict[str, Any]:
    client = get_openai_client()
    if client is None:
        return {}
    for attempt in range(3):
        try:
            resp = client.images.generate(model=model, prompt=prompt, size=size)
            data = resp.data[0]
            if hasattr(data, "url") and data.url:
                return {"url": data.url}
            if hasattr(data, "b64_json") and data.b64_json:
                return {"b64": data.b64_json}
            break
        except Exception as e:
            if attempt == 2:
                st.error(f"OpenAI image error: {e}")
                return {}
            time.sleep(0.75 * (attempt + 1))
    return {}

# --------------------------------
# Generators (character/npc/quest/image)
# --------------------------------
def generate_character(name: str, gender: str, race: str, character_class: str, background: str) -> Dict[str, Any]:
    return {"Name": name, "Gender": gender, "Race": race, "Class": character_class, "Background": background}

def generate_character_history(character: Dict[str, Any], generate_history: bool = True) -> str:
    if not generate_history:
        return ""
    prompt = (
        f"Create a short backstory for a {character['Race']} {character['Class']} named {character['Name']}. "
        f"They come from a {character['Background']} background. Include motivations and key events and locations. "
        f"No real-world names."
    )
    system = {"role": "system", "content": "You are a grounded fantasy storyteller. Keep tight, concrete details."}
    user = {"role": "user", "content": prompt}
    return call_chat([system, user])

def generate_npc_names(count: int = 10) -> List[Dict[str, str]]:
    prompt = (
        f"Generate {count} unique fantasy NPC names with their roles and a brief background for each. "
        f"Output as a bullet list: Name — Role — Background."
    )
    txt = call_chat([{"role": "user", "content": prompt}])
    npcs = []
    for line in txt.splitlines():
        line = line.strip("-• ").strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("—")]
        if len(parts) >= 3:
            npcs.append({"name": parts[0], "role": parts[1], "backstory": "—".join(parts[2:])})
    return npcs

def generate_location_names(count: int = 10) -> List[Dict[str, str]]:
    prompt = (
        f"Generate {count} unique fantasy location names with a short description for each. "
        f"Output as a bullet list: Name — Description. Include towns, ruins, forests, mountains, etc."
    )
    txt = call_chat([{"role": "user", "content": prompt}])
    locs = []
    for line in txt.splitlines():
        line = line.strip("-• ").strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("—")]
        if len(parts) >= 2:
            locs.append({"name": parts[0], "description": "—".join(parts[1:])})
    return locs

def generate_npc(generate_npc_text: bool = True) -> Dict[str, str]:
    if not generate_npc_text:
        return {"name": "Unknown", "role": "Unknown", "backstory": "No backstory provided."}
    txt = call_chat([{"role": "user", "content": "Generate a unique fantasy NPC: 'Name, Role' only."}])
    if "," in txt:
        name, role = (txt.split(",", 1) + [""])[:2]
    else:
        name, role = txt, random.choice(["merchant", "guard", "wizard", "priest"])
    backstory = f"{name.strip()} is a {role.strip()} with a complicated past."
    return {"name": name.strip(), "role": role.strip(), "backstory": backstory}

def generate_quest(generate_quest_text: bool = True) -> Dict[str, str]:
    if not generate_quest_text:
        return {"title": "Untitled Quest", "description": "No description provided."}
    txt = call_chat([{"role": "user", "content": "Create a fantasy quest with a Title on the first line and a one-paragraph Description on the second."}])
    parts = [p for p in (txt or "").splitlines() if p.strip()]
    title = parts[0].strip() if parts else "Untitled Quest"
    description = "\n".join(parts[1:]).strip() if len(parts) > 1 else "A mysterious quest awaits."
    return {"title": title, "description": description}

def generate_character_image(character: Dict[str, Any], style: str = "Standard") -> Dict[str, Any]:
    base_prompt = (
        f"A full-body portrait of a {character['Gender']} {character['Race']} {character['Class']} with {character['Background']} vibes, "
        f"heroic pose, detailed fantasy outfit."
    )
    if style == "8bit Style":
        base_prompt += " Pixelated sprite art, 8-bit game style."
    elif style == "Anime Style":
        base_prompt += " Anime style, cel-shaded."
    return call_image(base_prompt)

# --------------------------------
# PDF helpers
# --------------------------------
def draw_wrapped_text(c, text: str, x: int, y: int, max_width: int, line_height: int):
    for raw_line in (text or "").splitlines():
        words = raw_line.split()
        line = ""
        for w in words:
            test = f"{line} {w}".strip()
            if stringWidth(test, "Helvetica", 8) > max_width:
                c.drawString(x, y, line)
                y -= line_height
                line = w
            else:
                line = test
        if line:
            c.drawString(x, y, line)
            y -= line_height
    return y

def _image_reader_from_payload(payload: Dict[str, Any]):
    if not payload:
        return None
    try:
        if payload.get("url"):
            r = requests.get(payload["url"], timeout=15)
            r.raise_for_status()
            return ImageReader(BytesIO(r.content))
        if payload.get("b64"):
            import base64
            data = base64.b64decode(payload["b64"])
            return ImageReader(BytesIO(data))
    except Exception:
        return None
    return None

def create_pdf(character: Dict[str, Any], npc: Dict[str, str], quest: Dict[str, str], images: List[Dict[str, Any]]):
    buf = BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=letter)
    x, y = 50, 750
    lh, mw = 12, 500

    def section(title: str, content: str):
        nonlocal y
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, title)
        y -= lh
        c.setFont("Helvetica", 8)
        y = draw_wrapped_text(c, content or "", x, y, mw, lh)
        y -= lh

    section("Character Info", f"{character['Name']} ({character['Gender']}, {character['Race']}, {character['Class']})")
    section("Background", character.get("Background", ""))
    section("History", character.get("History", ""))
    section("NPC", f"{npc.get('name','')} - {npc.get('role','')}")
    section("NPC Backstory", npc.get("backstory", ""))
    section("Quest", quest.get("title", ""))
    section("Quest Description", quest.get("description", ""))

    for img_payload in images:
        reader = _image_reader_from_payload(img_payload)
        if reader:
            if y - 420 < 0:
                c.showPage(); y = 750
            c.drawImage(reader, x, y - 400, width=400, height=400, preserveAspectRatio=True)
            y -= 420
    c.showPage(); c.save(); buf.seek(0)
    return buf

# --------------------------------
# World grid + batched lore cache (mantido)
# --------------------------------
def initialize_world(world_name: str) -> Dict[str, Any]:
    world = {"name": world_name, "regions": {}}
    for i in range(5):
        for j in range(5):
            key = f"{i+1}-{j+1}"
            world["regions"][key] = {
                "name": f"Location {i+1}-{j+1}",
                "characters": [],
                "npcs": [],
                "quests": [],
                "capital": False,
                "special_traits": [],
                "lore": "",
                "_sig": "",
            }
    st.session_state.worlds.append(world)
    _save_json(STATE_FILES["worlds"], st.session_state.worlds)
    return world

def _region_signature(region: Dict[str, Any]) -> str:
    payload = {
        "name": region.get("name"),
        "capital": region.get("capital"),
        "special_traits": region.get("special_traits", []),
        "characters": [(c.get("Name"), c.get("Race"), c.get("Class")) for c in region.get("characters", [])],
        "npcs": [(n.get("name"), n.get("role")) for n in region.get("npcs", [])],
        "quests": [(q.get("title")) for q in region.get("quests", [])],
    }
    return json.dumps(payload, sort_keys=True)

def batch_generate_lore(world: Dict[str, Any]):
    targets = []
    for key, region in world["regions"].items():
        sig = _region_signature(region)
        if sig != region.get("_sig") and (region["characters"] or region["quests"] or region["npcs"]):
            targets.append((key, region, sig))
    if not targets:
        return
    items = []
    for key, region, sig in targets:
        items.append({
            "key": key,
            "name": region["name"],
            "capital": region["capital"],
            "traits": region.get("special_traits", []),
            "characters": [f"{c['Name']} ({c['Race']} {c['Class']})" for c in region.get("characters", [])],
            "npcs": [f"{n['name']} ({n['role']})" for n in region.get("npcs", [])],
            "quests": [f"{q['title']}: {q.get('description','')}" for q in region.get("quests", [])],
        })
    system = {
        "role": "system",
        "content": (
            "Return ONLY JSON list where each item is {key, lore}. "
            "Each 'lore' is a 120-200 word paragraph folding in characters/NPCs/quests/capital/traits. Grounded tone."
        ),
    }
    user = {"role": "user", "content": json.dumps(items)}
    raw = call_chat([system, user], temperature=0.8)
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            mapped = {entry.get("key"): entry.get("lore", "") for entry in parsed}
            for key, region, sig in targets:
                region["lore"] = mapped.get(key, region.get("lore", ""))
                region["_sig"] = sig
    except Exception:
        chunks = [p.strip() for p in (raw or "").split("\n\n") if p.strip()]
        for idx, (key, region, sig) in enumerate(targets):
            region["lore"] = chunks[idx] if idx < len(chunks) else region.get("lore", "")
            region["_sig"] = sig

# --------------------------------
# Journal helpers (mantido)
# --------------------------------
def save_journal(world_name: str, text: str):
    fn = os.path.join(DATA_DIR, f"journal_{world_name}.txt")
    with open(fn, "w", encoding="utf-8") as f:
        f.write(text)
    found = False
    for j in st.session_state.journals:
        if j.get("world") == world_name:
            j["text"] = text
            found = True
            break
    if not found:
        st.session_state.journals.append({"world": world_name, "text": text})
    _save_json(STATE_FILES["journals"], st.session_state.journals)

def load_journal(world_name: str) -> str:
    for j in st.session_state.journals:
        if j.get("world") == world_name:
            return j.get("text", "")
    fn = os.path.join(DATA_DIR, f"journal_{world_name}.txt")
    if os.path.exists(fn):
        with open(fn, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def generate_world_journal(world: Dict[str, Any]) -> str:
    batch_generate_lore(world)
    entries = []
    for key, region in world["regions"].items():
        entry = [f"**{region['name']}**"]
        if region.get("capital"):
            entry.append("Capital Region")
        if region.get("special_traits"):
            entry.append("Special Traits:\n" + "\n".join([f"- {t}" for t in region["special_traits"]]))
        if region.get("characters"):
            chars = "\n".join([f"- {c['Name']} ({c['Race']} {c['Class']})" for c in region["characters"]])
            entry.append("Characters:\n" + chars)
        if region.get("npcs"):
            npcs = "\n".join([f"- {n['name']} ({n['role']})" for n in region["npcs"]])
            entry.append("NPCs:\n" + npcs)
        if region.get("quests"):
            qs = "\n".join([f"- {q['title']}" for q in region["quests"]])
            entry.append("Quests:\n" + qs)
        if region.get("lore"):
            entry.append("Lore/Story:\n" + region["lore"])
        entries.append("\n".join(entry))
    return "\n\n".join(entries)

# --------------------------------
# Immersive Infinite Story — Core
# --------------------------------
def _append_story_chunk(text: str, tags: Optional[List[str]] = None):
    st.session_state["infinite_story"].append({
        "timestamp": time.time(),
        "day": st.session_state["world_time"],
        "text": text,
        "tags": tags or []
    })
    # salva cópia no diretório padrão para quem não usa caminho custom
    _save_json(STATE_FILES["infinite_story"], st.session_state["infinite_story"])

def _story_text_full() -> str:
    return "\n\n".join([f"[Day {e.get('day',0)}] {e['text']}" for e in st.session_state["infinite_story"]])

def save_story_to_path(path: str):
    _save_json(path, st.session_state["infinite_story"])

def load_story_from_upload(file):
    try:
        data = json.load(file)
        if isinstance(data, list):
            st.session_state["infinite_story"] = data
            st.success("Story carregada do arquivo.")
        else:
            st.error("JSON inválido (esperado: lista).")
    except Exception as e:
        st.error(f"Falha ao carregar JSON: {e}")

def last_events(n: int = 5) -> List[Dict[str, Any]]:
    return st.session_state["event_log"][-n:]

def _append_event(kind: str, payload: Dict[str, Any]):
    event = {
        "timestamp": time.time(),
        "day": st.session_state["world_time"],
        "kind": kind,
        "payload": payload
    }
    st.session_state["event_log"].append(event)

def _pick_world_and_region() -> Optional[Dict[str, Any]]:
    if not st.session_state.worlds:
        return None
    # escolhe mundo ativo se houver
    world = None
    if st.session_state["active_world_name"]:
        for w in st.session_state.worlds:
            if w["name"] == st.session_state["active_world_name"]:
                world = w
                break
    if not world:
        world = random.choice(st.session_state.worlds)
    # escolhe região
    if not world["regions"]:
        return {"world": world, "key": None, "region": None}
    key = random.choice(list(world["regions"].keys()))
    return {"world": world, "key": key, "region": world["regions"][key]}

def _background_event_tick():
    """Gera 0-2 eventos simples e concretos, usando NPCs/quests/traits se houver."""
    slot = _pick_world_and_region()
    if not slot:
        return []
    region = slot["region"]
    world = slot["world"]
    events = []
    roll = random.random()
    if roll < 0.35 and region:
        # NPC movement or rumor
        npc_name = None
        if region["npcs"]:
            npc_name = random.choice(region["npcs"])["name"]
        text = f"No {region['name']}, rumores de caravanas atrasadas e trilhas apagadas perto do vale."
        if npc_name:
            text = f"{npc_name} foi visto deixando {region['name']} ao amanhecer. Moradores falam de trilhas apagadas no vale."
        _append_event("rumor", {"region": region["name"], "npc": npc_name})
        events.append(text)
    if 0.35 <= roll < 0.7 and region:
        # quest progress
        if region["quests"]:
            q = random.choice(region["quests"])
            text = f"Progresso em '{q['title']}': uma pista concreta surgiu perto de {region['name']}."
            _append_event("quest_progress", {"region": region["name"], "quest": q["title"]})
            events.append(text)
    if roll >= 0.7:
        # minor disaster / opportunity
        choice = random.choice(["tempestade curta", "feira improvisada", "incêndio contido", "tensão na guarda"])
        text = f"Em {region['name']}, houve {choice}. Poucos feridos, mas a rotina mudou."
        _append_event("world_shift", {"region": region["name"], "note": choice})
        events.append(text)
    # anexa eventos ao texto da história com uma tag
    for t in events:
        _append_story_chunk(t, tags=["background"])
    # mexe no humor simples
    if events:
        if "incêndio" in events[-1] or "tensão" in events[-1] or "atrasadas" in events[-1]:
            st.session_state["story_mood"] = "Tense"
        elif "feira" in events[-1]:
            st.session_state["story_mood"] = "Hopeful"
    return events

def _build_reactive_prompt() -> str:
    # coleta contexto mínimo e concreto
    recent = last_events(3)
    recent_txt = "\n".join([f"- {e['kind']} @ Day {e['day']}: {e['payload']}" for e in recent]) or "- none"
    party_names = ", ".join([c["character"]["Name"] for c in st.session_state.get("characters", [])[:3]]) or "no party"
    mood = st.session_state["story_mood"]
    world_name = st.session_state["active_world_name"] or "Unbound World"
    base = (
        f"World: {world_name}\n"
        f"Day: {st.session_state['world_time']}\n"
        f"Mood: {mood}\n"
        f"Recent events:\n{recent_txt}\n\n"
        f"Party (sample): {party_names}\n\n"
        f"Continue the story in 6-10 sentences. Keep it grounded and concrete. Avoid new proper nouns unless necessary."
    )
    return base

def generate_choices(context_text: str) -> Dict[str, Any]:
    """Pede 3 escolhas sucintas em JSON seguro."""
    sys = {"role": "system", "content": "Return ONLY compact JSON: {prompt: str, options: [str, str, str]}."}
    usr = {"role": "user", "content": f"Given this story context:\n\n{context_text}\n\nPropose 3 player choices that are actionable and concrete."}
    raw = call_chat([sys, usr], temperature=0.6)
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "options" in data:
            return data
    except Exception:
        pass
    # fallback simples
    return {"prompt": "What do you do next?", "options": ["Investigar a pista", "Ajudar moradores", "Seguir viagem"]}

def apply_choice(choice_text: str, context_text: str) -> str:
    """Gera consequência curta e concreta baseada na escolha."""
    sys = {"role": "system", "content": "You write concise, grounded consequences. 5-8 sentences. No flourish."}
    usr = {"role": "user", "content": f"Context:\n{context_text}\n\nPlayer choice: {choice_text}\n\nWrite the immediate consequence, grounded, concrete."}
    return call_chat([sys, usr], temperature=0.7)

# --------------------------------
# UI
# --------------------------------
st.title(APP_TITLE, anchor="title")

mode = st.sidebar.radio("Select Mode:", [
    "Character", "Party", "Story Mode", "World Builder", "Infinite Story"  # novo modo
])

# --------------------------------
# CHARACTER MODE
# --------------------------------
if mode == "Character":
    name = st.text_input("Enter character name:")
    selected_race = st.selectbox("Select race:", RACES)
    selected_gender = st.selectbox("Select gender:", GENDERS)
    auto_generate = st.checkbox("Auto-generate class & background?", value=True)

    selected_style = st.selectbox("Select Art Style:", IMAGE_STYLES)
    generate_music = st.checkbox("Generate Theme Song (placeholder)")
    generate_turnaround = st.checkbox("Generate 360° Turnaround")
    generate_location = st.checkbox("Generate Place of Origin")
    generate_extra = st.checkbox("Generate Extra Images")
    generate_history = st.checkbox("Generate Character History", value=True)
    generate_npc_text = st.checkbox("Generate NPC Text", value=True)
    generate_quest_text = st.checkbox("Generate Quest Text", value=True)

    if not auto_generate:
        character_class = st.selectbox("Select class:", CLASSES)
        background = st.selectbox("Select background:", BACKGROUNDS)

    if st.button("Generate Character"):
        if not name.strip():
            st.warning("Enter a name.")
        else:
            if auto_generate:
                character_class = random.choice(CLASSES)
                background = random.choice(BACKGROUNDS)

            ch = generate_character(name, selected_gender, selected_race, character_class, background)
            ch["History"] = generate_character_history(ch, generate_history)

            image_payloads = []
            base = generate_character_image(ch, selected_style)
            if base:
                image_payloads.append(base)
            if generate_turnaround:
                image_payloads.append(generate_character_image(ch, selected_style))
            if generate_location:
                image_payloads.append(generate_character_image(ch, selected_style))
            if generate_extra:
                image_payloads.append(generate_character_image(ch, selected_style))
                image_payloads.append(generate_character_image(ch, selected_style))

            npc = generate_npc(generate_npc_text)
            quest = generate_quest(generate_quest_text)

            st.session_state.characters.append({
                "character": ch,
                "npc": npc,
                "quest": quest,
                "images": image_payloads,
            })
            _save_json(STATE_FILES["characters"], st.session_state.characters)
            st.success(f"Character '{ch['Name']}' created.")

    for i, data in enumerate(st.session_state.characters):
        ch, npc, quest, imgs = data['character'], data['npc'], data['quest'], data['images']
        tabs = st.tabs(["Info", "History", "NPC", "Quests", "Images", "Export"])
        with tabs[0]:
            st.write(f"**{ch['Name']}** — {ch['Gender']}, {ch['Race']} {ch['Class']} ({ch['Background']})")
        with tabs[1]:
            st.write(ch.get('History', 'No history generated'))
        with tabs[2]:
            st.write(f"**{npc.get('name','')}** ({npc.get('role','')})")
            st.write(npc.get('backstory',''))
        with tabs[3]:
            st.write(f"**{quest.get('title','')}**")
            st.write(quest.get('description',''))
        with tabs[4]:
            for payload in imgs:
                if payload.get("url"):
                    st.image(payload["url"], use_container_width=True)
                elif payload.get("b64"):
                    import base64
                    st.image(base64.b64decode(payload["b64"]))
        with tabs[5]:
            st.download_button(
                "Download JSON",
                data=json.dumps({"character": ch, "npc": npc, "quest": quest}, indent=2, ensure_ascii=False),
                file_name=f"{ch['Name']}.json",
            )
            pdf_buf = create_pdf(ch, npc, quest, imgs)
            st.download_button(
                "Download PDF",
                data=pdf_buf,
                file_name=f"{ch['Name']}.pdf",
                mime="application/pdf",
            )

# --------------------------------
# PARTY MODE
# --------------------------------
elif mode == "Party":
    st.header("🧑‍🤝‍🧑 Party Builder")
    if len(st.session_state.characters) < 2:
        st.warning("Create at least 2 characters to form a party.")
    else:
        options = [f"{i+1}. {d['character']['Name']}" for i, d in enumerate(st.session_state.characters)]
        selected = st.multiselect("Select party members:", options)

        if st.button("Form Party") and selected:
            idxs = [options.index(s) for s in selected]
            members = [st.session_state.characters[i] for i in idxs]
            names = ", ".join([m['character']['Name'] for m in members])
            story = call_chat([{"role": "user", "content": f"Write a group story for party members: {names}."}])
            st.session_state.parties.append({"members": members, "story": story})
            _save_json(STATE_FILES["parties"], st.session_state.parties)
            st.success("Party created.")

        for idx, party in enumerate(st.session_state.parties):
            exp = st.expander(f"Party {idx+1}: {', '.join([m['character']['Name'] for m in party['members']])}")
            with exp:
                subtabs = st.tabs(["Overview", "Story", "Export"])
                with subtabs[0]:
                    for m in party['members']:
                        st.write(m['character']['Name'])
                with subtabs[1]:
                    st.write(party['story'])
                    with st.form(f"story_form_{idx}"):
                        if st.form_submit_button("Generate New Story"):
                            names = ", ".join([m['character']['Name'] for m in party['members']])
                            existing = party['story']
                            continuation = call_chat([
                                {"role": "user", "content": f"Continue the following story for the party members {names}:\n\n{existing}"}
                            ])
                            party['story'] += "\n\n" + continuation
                            st.session_state.parties[idx] = party
                            _save_json(STATE_FILES["parties"], st.session_state.parties)
                            st.success("Appended.")
                with subtabs[2]:
                    st.download_button(
                        "Download Party JSON",
                        data=json.dumps(party, indent=2, ensure_ascii=False),
                        file_name=f"party_{idx+1}.json",
                    )
                    buf = BytesIO()
                    c = pdf_canvas.Canvas(buf, pagesize=letter)
                    c.setFont("Helvetica", 8)
                    c.drawString(50, 750, f"Party: {', '.join([m['character']['Name'] for m in party['members']])}")
                    y = draw_wrapped_text(c, party['story'], 50, 730, max_width=500, line_height=12)
                    c.showPage(); c.save(); buf.seek(0)
                    st.download_button("Download Party PDF", data=buf, file_name=f"party_{idx+1}.pdf", mime="application/pdf")

# --------------------------------
# STORY MODE (clássico)
# --------------------------------
elif mode == "Story Mode":
    st.header("📜 Quest Creator")
    if not st.session_state.characters:
        st.warning("Generate characters first in the Character tab.")
    else:
        character_names = [c['character']['Name'] for c in st.session_state.characters]
        selected_char_index = st.selectbox("Select Character:", range(len(character_names)), format_func=lambda i: character_names[i])
        selected_character_data = st.session_state.characters[selected_char_index]
        selected_character = selected_character_data['character']
        selected_npc = selected_character_data['npc']
        selected_quest = selected_character_data['quest']

        if st.button("Generate"):
            prompt = (
                f"Write a short grounded fantasy paragraph involving:\n"
                f"Character: {selected_character['Name']} ({selected_character['Race']} {selected_character['Class']}, {selected_character['Background']})\n"
                f"NPC: {selected_npc['name']} - {selected_npc['role']}\n"
                f"Quest: {selected_quest['title']}\n"
            )
            story_text = call_chat([
                {"role": "system", "content": "You are a fantasy storyteller."},
                {"role": "user", "content": prompt},
            ])
            st.session_state.stories.append({
                "character": selected_character,
                "npc": selected_npc,
                "quest": selected_quest,
                "story": story_text,
            })
            _save_json(STATE_FILES["stories"], st.session_state.stories)
            st.success("Quest generated.")

    if st.session_state.stories:
        st.subheader("Quests")
        for idx, entry in enumerate(st.session_state.stories):
            with st.expander(f"Story {idx+1}: {entry['character']['Name']} - {entry['quest']['title']}"):
                st.markdown(f"**Character**: {entry['character']['Name']} ({entry['character']['Class']})")
                st.markdown(f"**NPC**: {entry['npc']['name']} - {entry['npc']['role']}")
                st.markdown(f"**Quest**: {entry['quest']['title']}")
                st.text_area("Story Text", value=entry['story'], height=200, key=f"story_text_{idx}")

                story_json = json.dumps(entry, indent=2, ensure_ascii=False)
                st.download_button("Download JSON", story_json, file_name=f"story_{idx+1}.json")

                pdf_buf = BytesIO()
                c = pdf_canvas.Canvas(pdf_buf, pagesize=letter)
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, 750, f"Story {idx+1}: {entry['character']['Name']} - {entry['quest']['title']}")
                c.setFont("Helvetica", 10)
                y = draw_wrapped_text(c, entry['story'], 50, 730, 500, 14)
                c.save(); pdf_buf.seek(0)
                st.download_button("Download PDF", data=pdf_buf, file_name=f"story_{idx+1}.pdf", mime="application/pdf")

# --------------------------------
# WORLD BUILDER (mantido + gerar NPC/Loc)
# --------------------------------
elif mode == "World Builder":
    tab1, tab2 = st.tabs(["Regions", "Journal"])
    with tab1:
        world_name = st.text_input("Enter Region Name:")
        if st.button("Create Region") and world_name.strip():
            world = initialize_world(world_name)
            st.session_state["active_world_name"] = world_name
            st.success(f"Region '{world_name}' created.")

        if st.session_state.worlds:
            for world in st.session_state.worlds:
                st.subheader(f"🌍 {world['name']}")
                cols_title = st.columns(5)
                for i in range(5):
                    cols = st.columns(5)
                    for j in range(5):
                        loc_key = f"{i+1}-{j+1}"
                        region = world["regions"][loc_key]
                        cols[j].write(f"**{region['name']}**")
                        if region["characters"] or region["npcs"] or region["quests"]:
                            cols[j].write(f"{len(region['characters'])} Chars, {len(region['npcs'])} NPCs, {len(region['quests'])} Quests")
                        if region["capital"]:
                            cols[j].write("🏰 Capital")
                        if region["special_traits"]:
                            cols[j].write("🌟 Traits:")
                            for trait in region["special_traits"]:
                                cols[j].write(f"- {trait}")

        npc_count = st.slider("Number of NPCs to generate:", 1, 20, 10)
        loc_count = st.slider("Number of Locations to generate:", 1, 20, 10)
        if st.button("Generate NPCs and Locations"):
            npcs = generate_npc_names(npc_count)
            locations = generate_location_names(loc_count)
            st.session_state.npcs = npcs
            st.session_state.locations = locations
            st.success(f"Generated {npc_count} NPCs and {loc_count} locations!")
        if "npcs" in st.session_state and "locations" in st.session_state:
            st.subheader("Generated NPCs")
            for npc in st.session_state.npcs:
                st.write(f"**{npc['name']}** ({npc['role']}) - {npc['backstory']}")
            st.subheader("Generated Locations")
            for loc in st.session_state.locations:
                st.write(f"**{loc['name']}** - {loc['description']}")

    with tab2:
        subtab1, subtab2, subtab3, subtab4, subtab5, subtab6 = st.tabs(["Journals", "Stories", "Characters", "NPCs", "Quests", "Parties"])
        with subtab1:
            st.header("📓 Journals")
            if not st.session_state.worlds:
                st.info("No worlds created yet.")
            else:
                for idx, world in enumerate(st.session_state.worlds):
                    st.subheader(f"📜 Journals for {world['name']}")
                    previous = load_journal(world['name'])
                    batch_generate_lore(world)
                    current = generate_world_journal(world)
                    full = f"{previous}\n\n{current}".strip()
                    st.text_area(f"Journal Text - {world['name']}", value=full, height=300, key=f"journal_text_{idx}")
                    if st.button(f"Save Journal for {world['name']}", key=f"save_journal_{idx}"):
                        save_journal(world['name'], full)
                        _save_json(STATE_FILES["worlds"], st.session_state.worlds)
                        st.success(f"Journal saved for {world['name']}.")

        with subtab2:
            st.header("📝 World Stories")
            if not st.session_state.stories:
                st.info("No stories created yet.")
            else:
                for idx, story in enumerate(st.session_state.stories):
                    with st.expander(f"Story {idx+1}: {story['character']['Name']} - {story['quest']['title']}"):
                        st.markdown(f"**Character**: {story['character']['Name']} ({story['character']['Class']})")
                        st.markdown(f"**NPC**: {story['npc']['name']} - {story['npc']['role']}")
                        st.markdown(f"**Quest**: {story['quest']['title']}")
                        st.text_area(f"Story Text - {idx+1}", value=story['story'], height=200, key=f"story_text_{idx}")

        with subtab3:
            st.header("🦸 Characters")
            if st.session_state.characters:
                for character in st.session_state.characters:
                    st.write(character)
            else:
                st.info("No characters created yet.")

        with subtab4:
            st.header("🗣️ NPCs")
            st.info("NPC management coming soon...")

        with subtab5:
            st.header("🪐 Quests")
            st.info("Quests management coming soon...")

        with subtab6:
            st.header("🪐 Parties")
            st.info("Parties management coming soon...")

# --------------------------------
# INFINITE STORY (imersivo, com salvar/carregar)
# --------------------------------
elif mode == "Infinite Story":
    st.header("♾️ Infinite Story (Reactive)")

    # Seleção de mundo ativo (opcional, melhora contexto)
    world_names = ["(none)"] + [w["name"] for w in st.session_state.worlds]
    sel = st.selectbox("Active World (optional):", world_names, index=0)
    st.session_state["active_world_name"] = None if sel == "(none)" else sel

    # Linha do tempo e humor
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("World Day", st.session_state["world_time"])
    with col2:
        st.metric("Events Logged", len(st.session_state["event_log"]))
    with col3:
        st.metric("Mood", st.session_state["story_mood"])

    # Carregar de arquivo
    with st.expander("Load / Save"):
        up = st.file_uploader("Load story file (JSON)", type=["json"])
        if up is not None:
            load_story_from_upload(up)

        save_path = st.text_input("Save file path", os.path.join(DATA_DIR, "infinite_story.json"))
        save_cols = st.columns(2)
        with save_cols[0]:
            if st.button("Save to Path"):
                try:
                    save_story_to_path(save_path)
                    st.success(f"Saved to: {save_path}")
                except Exception as e:
                    st.error(f"Save failed: {e}")
        with save_cols[1]:
            st.download_button(
                "Download Current Story (JSON)",
                data=json.dumps(st.session_state["infinite_story"], indent=2, ensure_ascii=False),
                file_name="infinite_story.json",
            )

    st.subheader("Story so far")
    st.text_area("",
        value=_story_text_full(),
        height=300
    )

    # Avançar tempo + eventos de fundo
    with st.form("advance_time_form"):
        days = st.number_input("Advance days", min_value=1, max_value=30, value=1, step=1)
        submit_time = st.form_submit_button("Advance World Time")
        if submit_time:
            for _ in range(days):
                st.session_state["world_time"] += 1
                _background_event_tick()
            st.success(f"Advanced {days} day(s).")

    st.divider()

    # Continuar história reativa
    if st.button("Continue Story (Reactive)"):
        ctx = _build_reactive_prompt()
        text = call_chat(
            [{"role": "system", "content": "Grounded, concrete fantasy narration. 6-10 sentences. No purple prose."},
             {"role": "user", "content": ctx}],
            temperature=0.8
        )
        if text:
            _append_story_chunk(text, tags=["continue"])
            # gerar escolhas
            ch = generate_choices(text)
            st.session_state["pending_choices"] = {"prompt": ch.get("prompt", "Choose."), "options": ch.get("options", []), "context": text}
            st.success("Story continued.")

    # Exibir e resolver escolhas
    if st.session_state["pending_choices"]:
        st.subheader("Your Choice")
        pc = st.session_state["pending_choices"]
        st.write(pc["prompt"])
        choice = st.radio("Options:", pc["options"], index=0)
        if st.button("Apply Choice"):
            consequence = apply_choice(choice, pc["context"])
            if consequence:
                _append_story_chunk(f"[Choice] {choice}\n{consequence}", tags=["choice"])
                # evento de consequência simples
                _append_event("choice", {"choice": choice})
                st.session_state["pending_choices"] = None
                st.success("Choice applied.")

    st.divider()

    # Anotação manual
    st.subheader("Manual Note")
    note = st.text_input("Append a manual note:")
    if st.button("Add Note"):
        if note.strip():
            _append_story_chunk(note.strip(), tags=["note"])
            st.success("Note added.")

