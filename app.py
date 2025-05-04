import random
import streamlit as st
import json
import openai
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit, ImageReader
import base64
import requests

# Load OpenAI key securely
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Initialize session state
if "characters" not in st.session_state:
    st.session_state.characters = []
if "parties" not in st.session_state:
    st.session_state.parties = []
if "npc_chains" not in st.session_state:
    st.session_state.npc_chains = []

# Character traits
races = ["Human", "Elf", "Dwarf", "Halfling", "Gnome", "Half-Orc", "Tiefling", "Dragonborn", "Kobold", "Lizardfolk", "Minotaur", "Troll", "Vampire", "Satyr", "Undead", "Lich", "Werewolf"]
classes = ["Fighter", "Wizard", "Rogue", "Cleric", "Barbarian", "Sorcerer", "Bard", "Monk", "Druid", "Ranger", "Paladin", "Warlock", "Artificer", "Blood Hunter", "Mystic", "Warden", "Berserker", "Necromancer", "Trickster", "Beast Master", "Alchemist", "Pyromancer", "Dark Knight"]
backgrounds = ["Acolyte", "Folk Hero", "Sage", "Criminal", "Noble", "Hermit", "Outlander", "Entertainer", "Artisan", "Sailor", "Soldier", "Charlatan", "Knight", "Pirate", "Spy", "Archaeologist", "Gladiator", "Inheritor", "Haunted One", "Bounty Hunter", "Explorer", "Watcher", "Traveler", "Phantom", "Vigilante"]
genders = ["Male", "Female", "Non-binary"]
image_styles = ["Standard", "8bit Style", "Anime Style"]

# Generation functions (unchanged)
def generate_character(name, gender, race, character_class, background):
    return {"Name": name, "Gender": gender, "Race": race, "Class": character_class, "Background": background}

def generate_character_history(character, generate_history=True):
    if generate_history:
        prompt = f"Create a short backstory for a {character['Race']} {character['Class']} named {character['Name']}. They come from a {character['Background']} background. Include motivations, key events, and a mystery."
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are a creative storyteller."}, {"role": "user", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"]
    return ""

def generate_character_image(character, style="Standard"):
    base_prompt = f"A full-body portrait of a {character['Gender']} {character['Race']} {character['Class']} with {character['Background']} vibes, heroic pose, detailed fantasy outfit."
    if style == "8bit Style": base_prompt += " pixelated sprite art, 8-bit game style"
    if style == "Anime Style": base_prompt += " anime art style, cel-shaded, colorful background"
    response = openai.Image.create(model="dall-e-3", prompt=base_prompt, size="1024x1024")
    return response["data"][0]["url"]

def generate_npc(generate_npc_text=True):
    if generate_npc_text:
        prompt = "Generate a unique fantasy NPC name and their profession."
        response = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        parts = response["choices"][0]["message"]["content"].strip().split(", ")
        name = parts[0]
        role = parts[1] if len(parts) == 2 else random.choice(["merchant", "guard", "wizard", "priest"])
        backstory = f"{name} is a {role} with a mysterious past."
    else:
        name, role, backstory = "Unknown", "Unknown", "No backstory provided."
    return {"name": name, "role": role, "backstory": backstory}

def generate_quest(generate_quest_text=True):
    if generate_quest_text:
        prompt = "Create a fantasy quest with a title and short description."
        response = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        parts = response["choices"][0]["message"]["content"].strip().split("\n", 1)
        title = parts[0]
        description = parts[1] if len(parts) > 1 else "A mysterious quest awaits."
    else:
        title, description = "Untitled Quest", "No description provided."
    return {"title": title, "description": description}

def download_image(image_url):
    try:
        response = requests.get(image_url)
        return ImageReader(BytesIO(response.content))
    except:
        return None

def draw_wrapped_text(canvas, text, x, y, max_width, line_height):
    from reportlab.pdfbase.pdfmetrics import stringWidth
    words = text.split()
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        if stringWidth(test_line, "Helvetica", 7) > max_width:
            canvas.drawString(x, y, line)
            y -= line_height
            line = word
        else:
            line = test_line
    if line:
        canvas.drawString(x, y, line)
        y -= line_height
    return y

def create_pdf(character, npc, quest, images):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    x, y = 50, 750
    line_height = 12; max_width = 500
    def section(title, content):
        nonlocal y
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, title)
        y -= line_height
        c.setFont("Helvetica", 8)
        y = draw_wrapped_text(c, content, x, y, max_width, line_height)
        y -= line_height
    # sections
    section("Character Info", f"{character['Name']} ({character['Gender']}, {character['Race']}, {character['Class']})")
    section("Background", character['Background'])
    section("History", character.get('History', ''))
    section("NPC", f"{npc['name']} - {npc['role']}")
    section("NPC Backstory", npc['backstory'])
    section("Quest", quest['title'])
    section("Quest Description", quest['description'])
    # images
    for url in images:
        img = download_image(url)
        if img:
            if y - 270 < 0: c.showPage(); y = 750
            c.drawImage(img, x, y - 400, width=400, height=400, preserveAspectRatio=True)
            y -= 420
    c.showPage(); c.save(); buffer.seek(0)
    return buffer

def save_to_json(character, npc, quest, file_name="character_data.json"):
    with open(file_name, 'w') as f:
        json.dump({"character": character, "npc": npc, "quest": quest}, f, indent=4)

# --- Streamlit UI ---
st.title("🎭 Mana Forge Character Generator & Toolkit")
mode = st.sidebar.radio("Select Mode:", ["Character", "Party", "NPC Chains"])

# Character mode
if mode == "Character":
    # Original UI inputs
    name = st.text_input("Enter character name:")
    selected_race = st.selectbox("Select race:", races)
    selected_gender = st.selectbox("Select gender:", genders)
    auto_generate = st.checkbox("Auto-generate class & background?", value=True)
    if auto_generate:
        character_class = random.choice(classes)
        background = random.choice(backgrounds)
        st.write(f"Class: {character_class} | Background: {background}")
    else:
        character_class = st.selectbox("Select class:", classes)
        background = st.selectbox("Select background:", backgrounds)
    selected_style = st.selectbox("Select Art Style:", image_styles)
    generate_music = st.checkbox("Generate Theme Song (Audiocraft)")
    generate_turnaround = st.checkbox("Generate 360° Turnaround")
    generate_location = st.checkbox("Generate Place of Origin")
    generate_extra = st.checkbox("Generate Extra Images")
    generate_history = st.checkbox("Generate Character History")
    generate_npc_text = st.checkbox("Generate NPC Text")
    generate_quest_text = st.checkbox("Generate Quest Text")
    if st.button("Generate Character"):
        if not name.strip(): st.warning("Please enter a name.")
        else:
            # generate
            char = generate_character(name, selected_gender, selected_race, character_class, background)
            char["History"] = generate_character_history(char, generate_history)
            # images
            image_urls = [generate_character_image(char, selected_style)]
            if generate_turnaround: image_urls.append(generate_character_image(char, selected_style))
            if generate_location: image_urls.append(generate_character_image(char, selected_style))
            if generate_extra:
                image_urls.append(generate_character_image(char, selected_style))
                image_urls.append(generate_character_image(char, selected_style))
            npc = generate_npc(generate_npc_text)
            quest = generate_quest(generate_quest_text)
            st.session_state.characters.append({"character": char, "npc": npc, "quest": quest, "images": image_urls})
            st.success("Character Created!")
    # display
    for i, data in enumerate(st.session_state.characters):
        ch, npc, quest, imgs = data['character'], data['npc'], data['quest'], data['images']
        tabs = st.tabs(["Info", "History", "NPC", "Quests", "Images", "Export"])
        with tabs[0]:
            st.write(f"**{ch['Name']}** — {ch['Gender']}, {ch['Race']} {ch['Class']} ({ch['Background']})")
        with tabs[1]:
            st.write(ch.get('History', 'No history generated'))
        with tabs[2]:
            st.write(f"**{npc['name']}** ({npc['role']})")
            st.write(npc['backstory'])
        with tabs[3]:
            st.write(f"**{quest['title']}**")
            st.write(quest['description'])
        with tabs[4]:
            for url in imgs: st.image(url, use_container_width=True)
        with tabs[5]:
            st.download_button("Download JSON", data=json.dumps({"character": ch, "npc": npc, "quest": quest}), file_name=f"{ch['Name']}.json")
            pdf_buf = create_pdf(ch, npc, quest, imgs)
            st.download_button("Download PDF", data=pdf_buf, file_name=f"{ch['Name']}.pdf", mime="application/pdf")

# Party mode
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
            response = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role": "user", "content": f"Write a group story for party members: {names}."}])
            story = response['choices'][0]['message']['content']
            st.session_state.parties.append({"members": members, "story": story})
            st.success("Party Created!")
        for idx, party in enumerate(st.session_state.parties):
            exp = st.expander(f"Party {idx+1}: {', '.join([m['character']['Name'] for m in party['members']])}")
            with exp:
                subtabs = st.tabs(["Overview", "Story", "Export"])
                with subtabs[0]:
                    for m in party['members']: st.write(m['character']['Name'])
                with subtabs[1]: st.write(party['story'])
                with subtabs[2]:
                    st.download_button("Download Party JSON", data=json.dumps(party), file_name=f"party_{idx+1}.json")
                    buf = BytesIO(); c = canvas.Canvas(buf, pagesize=letter)
                    c.drawString(50, 750, f"Party: {names}"); c.drawString(50, 730, party['story']); c.showPage(); c.save(); buf.seek(0)
                    st.download_button("Download Party PDF", data=buf, file_name=f"party_{idx+1}.pdf", mime="application/pdf")

# NPC Chains mode
else:
    st.header("🔗 NPC Chains")
    if st.button("Generate NPC Chain for All Characters"):
        chain = {d['character']['Name']: {"NPC": d['npc'], "Quest": d['quest']} for d in st.session_state.characters}
        st.session_state.npc_chains.append(chain)
        st.success("NPC Chain Generated!")
    for idx, chain in enumerate(st.session_state.npc_chains):
        exp = st.expander(f"NPC Chain {idx+1}")
        with exp:
            st.json(chain)
