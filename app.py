# Mana Forge — Character Generator & World Toolkit (Rewritten 2025)
# Streamlit app with modern OpenAI SDK, batch lore generation, caching, and persistence
# Author: (you)

import os
import json
import time
import random
from io import BytesIO
from typing import Dict, List, Any

import streamlit as st
import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth

# ---------------------------
# OpenAI (modern SDK)
# ---------------------------
try:
    from openai import OpenAI
except Exception as e:
    OpenAI = None  # Will be checked later

# ---------------------------
# Constants & Config
# ---------------------------
APP_TITLE = "🎭 Mana Forge — Character Generator & Toolkit"
DATA_DIR = "data"
TEXT_MODEL = st.secrets.get("OPENAI_TEXT_MODEL", "gpt-4o-mini")
IMAGE_MODEL = st.secrets.get("OPENAI_IMAGE_MODEL", "gpt-image-1")

# Legacy compat for users who kept OPENAI_API_KEY only
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")

# Create data dir
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------
# Helpers — Persistence
# ---------------------------

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
}


# ---------------------------
# Session State init/load
# ---------------------------
for key in ["characters", "parties", "stories", "worlds", "journals"]:
    if key not in st.session_state:
        st.session_state[key] = _load_json(STATE_FILES[key], [])


# ---------------------------
# Static tables
# ---------------------------
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


# ---------------------------
# OpenAI client + robust calls
# ---------------------------
@st.cache_resource(show_spinner=False)
def get_openai_client():
    if OpenAI is None:
        st.error("OpenAI SDK not installed. Add 'openai' >= 1.0 to your requirements.")
        return None
    if not OPENAI_API_KEY:
        st.error("Missing OPENAI_API_KEY in st.secrets")
        return None
    try:
        return OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        st.error(f"Failed to init OpenAI: {e}")
        return None


def call_chat(messages: List[Dict[str, str]], model: str = TEXT_MODEL, **kwargs) -> str:
    client = get_openai_client()
    if client is None:
        return ""
    # Simple backoff
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
    """Returns dict with either {'url': ...} or {'b64': ...}."""
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


# ---------------------------
# Generators
# ---------------------------

def generate_character(name: str, gender: str, race: str, character_class: str, background: str) -> Dict[str, Any]:
    return {"Name": name, "Gender": gender, "Race": race, "Class": character_class, "Background": background}


def generate_character_history(character: Dict[str, Any], generate_history: bool = True) -> str:
    if not generate_history:
        return ""
    prompt = (
        f"Create a short backstory for a {character['Race']} {character['Class']} named {character['Name']}. "
        f"They come from a {character['Background']} background. Include motivations and key events and locations, "
        f"don't use existing names from reality."
    )
    system = {
        "role": "system",
        "content": "You are a creative storyteller, in a grounded epic-fantasy voice (no real-world names).",
    }
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
        line = line.strip("-• ")
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
        line = line.strip("-• ")
        if not line:
            continue
        parts = [p.strip() for p in line.split("—")]
        if len(parts) >= 2:
            locs.append({"name": parts[0], "description": "—".join(parts[1:])})
    return locs


def generate_npc(generate_npc_text: bool = True) -> Dict[str, str]:
    if not generate_npc_text:
        return {"name": "Unknown", "role": "Unknown", "backstory": "No backstory provided."}
    txt = call_chat([
        {"role": "user", "content": "Generate a unique fantasy NPC: 'Name, Role' only."}
    ])
    name, role = (txt.split(",", 1) + [""])[:2] if "," in txt else (txt, random.choice(["merchant", "guard", "wizard", "priest"]))
    backstory = f"{name.strip()} is a {role.strip()} with a mysterious past."
    return {"name": name.strip(), "role": role.strip(), "backstory": backstory}


def generate_quest(generate_quest_text: bool = True) -> Dict[str, str]:
    if not generate_quest_text:
        return {"title": "Untitled Quest", "description": "No description provided."}
    txt = call_chat([
        {"role": "user", "content": "Create a fantasy quest with a Title on the first line and a one-paragraph Description on the second."}
    ])
    parts = txt.splitlines()
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
        base_prompt += " Anime style, cel-shaded, vivid background."
    return call_image(base_prompt)


# ---------------------------
# PDF helpers
# ---------------------------

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
            data = base64.b64decode(payload["b64"])  # bytes
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


# ---------------------------
# World init & batch lore
# ---------------------------

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
                # caching
                "lore": "",
                "_sig": "",  # signature of inputs used to generate lore
            }
    st.session_state.worlds.append(world)
    _save_json(STATE_FILES["worlds"], st.session_state.worlds)
    return world


def _region_signature(region: Dict[str, Any]) -> str:
    """Simple signature of region inputs that affect lore."""
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
    """Generate lore only for regions whose signature changed; batch in one prompt and parse JSON."""
    targets = []
    for key, region in world["regions"].items():
        sig = _region_signature(region)
        if sig != region.get("_sig") and (region["characters"] or region["quests"] or region["npcs"]):
            targets.append((key, region, sig))

    if not targets:
        return  # nothing to do

    # Build request
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
            "You are a fantasy world-building assistant. Return ONLY JSON list where each item is {key, lore}. "
            "Each 'lore' should be a rich paragraph (120-200 words) folding in characters, NPCs, quests, capital status, and traits."
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
        # Fallback: naive split by sections if JSON failed
        chunks = [p.strip() for p in raw.split("\n\n") if p.strip()]
        for idx, (key, region, sig) in enumerate(targets):
            region["lore"] = chunks[idx] if idx < len(chunks) else region.get("lore", "")
            region["_sig"] = sig


# ---------------------------
# Journal helpers
# ---------------------------

def save_journal(world_name: str, text: str):
    # persist to disk and session
    # also keep a rolling file per world
    fn = os.path.join(DATA_DIR, f"journal_{world_name}.txt")
    with open(fn, "w", encoding="utf-8") as f:
        f.write(text)
    # index in session
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
    # Ensure lore cache is updated
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


# ---------------------------
# UI
# ---------------------------

st.title(APP_TITLE, anchor="title")

mode = st.sidebar.radio("Select Mode:", ["Character", "Party", "Story Mode", "World Builder"]) 

# ---------------------------
# CHARACTER MODE
# ---------------------------
if mode == "Character":
    name = st.text_input("Enter character name:")
    selected_race = st.selectbox("Select race:", RACES)
    selected_gender = st.selectbox("Select gender:", GENDERS)
    auto_generate = st.checkbox("Auto-generate class & background?", value=True)

    selected_style = st.selectbox("Select Art Style:", IMAGE_STYLES)
    generate_music = st.checkbox("Generate Theme Song (Audiocraft)")  # placeholder
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
            st.warning("Please enter a name.")
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
            st.success(f"Character '{ch['Name']}' Created!")

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

# ---------------------------
# PARTY MODE
# ---------------------------
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
            story = call_chat([
                {"role": "user", "content": f"Write a group story for party members: {names}."}
            ])
            st.session_state.parties.append({"members": members, "story": story})
            _save_json(STATE_FILES["parties"], st.session_state.parties)
            st.success("Party Created!")

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
                            st.success("New story generated and appended!")
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

# ---------------------------
# STORY MODE
# ---------------------------
elif mode == "Story Mode":
    st.header("📜 Quest Creator")

    if not st.session_state.characters:
        st.warning("Please generate characters first in the Character tab.")
    else:
        character_names = [c['character']['Name'] for c in st.session_state.characters]
        selected_char_index = st.selectbox("Select Character:", range(len(character_names)), format_func=lambda i: character_names[i])
        selected_character_data = st.session_state.characters[selected_char_index]

        selected_character = selected_character_data['character']
        selected_npc = selected_character_data['npc']
        selected_quest = selected_character_data['quest']

        if st.button("Generate"):
            prompt = (
                f"Write a short D&D style story paragraph involving the following quest, party, and NPC:\n"
                f"Character: {selected_character['Name']} ({selected_character['Race']} {selected_character['Class']}, {selected_character['Background']})\n"
                f"NPC: {selected_npc['name']} - {selected_npc['role']}, {selected_npc['backstory']}\n"
                f"Make it immersive and grounded."
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
            st.success("Quest generated!")

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

                # PDF export for story
                pdf_buf = BytesIO()
                c = pdf_canvas.Canvas(pdf_buf, pagesize=letter)
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, 750, f"Story {idx+1}: {entry['character']['Name']} - {entry['quest']['title']}")
                c.setFont("Helvetica", 10)
                # Reuse draw_wrapped_text signature used elsewhere
                def _wrap(ca, text, x, y, w, lh):
                    return draw_wrapped_text(ca, text, x, y, w, lh)
                y = _wrap(c, entry['story'], 50, 730, 500, 14)
                c.save(); pdf_buf.seek(0)
                st.download_button("Download PDF", data=pdf_buf, file_name=f"story_{idx+1}.pdf", mime="application/pdf")

# ---------------------------
# WORLD BUILDER
# ---------------------------
if mode == "World Builder":
    tab1, tab2 = st.tabs(["Regions", "Journal"])

    with tab1:
        world_name = st.text_input("Enter Region Name:")
        if st.button("Create Region") and world_name.strip():
            world = initialize_world(world_name)
            st.success(f"Region '{world_name}' Created!")

        if st.session_state.worlds:
            for world in st.session_state.worlds:
                st.subheader(f"🌍 {world['name']}")
                for i in range(5):
                    cols = st.columns(5)
                    for j in range(5):
                        loc_key = f"{i+1}-{j+1}"
                        region = world["regions"][loc_key]
                        cols[j].write(f"**{region['name']}**")
                        if region["characters"] or region["npcs"] or region["quests"]:
                            cols[j].write(f"{len(region['characters'])} Characters, {len(region['npcs'])} NPCs, {len(region['quests'])} Quests")
                        if region["capital"]:
                            cols[j].write("🏰 Capital Region")
                        if region["special_traits"]:
                            cols[j].write("🌟 Special Traits:")
                            for trait in region["special_traits"]:
                                cols[j].write(f"- {trait}")
        # NPC & Location generation
        npc_count = st.slider("Number of NPCs to generate:", min_value=1, max_value=20, value=10)
        loc_count = st.slider("Number of Locations to generate:", min_value=1, max_value=20, value=10)
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
                st.info("No worlds created yet. Create a region to start generating journals.")
            else:
                for idx, world in enumerate(st.session_state.worlds):
                    st.subheader(f"📜 Journals for {world['name']}")
                    previous = load_journal(world['name'])
                    # Update lore cache before journal assembly
                    batch_generate_lore(world)
                    current = generate_world_journal(world)
                    full = f"{previous}\n\n{current}".strip()
                    st.text_area(f"Journal Text - {world['name']}", value=full, height=300, key=f"journal_text_{idx}")
                    if st.button(f"Save Journal for {world['name']}", key=f"save_journal_{idx}"):
                        save_journal(world['name'], full)
                        _save_json(STATE_FILES["worlds"], st.session_state.worlds)
                        st.success(f"Journal saved for {world['name']}!")

        with subtab2:
            st.header("📝 World Stories")
            if not st.session_state.stories:
                st.info("No stories created yet. Use the **Story Mode** to generate and save some epic tales!")
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
