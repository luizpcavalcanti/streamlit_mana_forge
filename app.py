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
if "stories" not in st.session_state:
    st.session_state.stories = []
if "journals" not in st.session_state:
    st.session_state.journals = []

# --- Character Traits ---
races = ["Human", "Elf", "Dwarf", "Halfling", "Gnome", "Half-Orc", "Tiefling", "Dragonborn"]
classes = ["Fighter", "Wizard", "Rogue", "Cleric", "Barbarian", "Sorcerer", "Bard"]
backgrounds = ["Acolyte", "Folk Hero", "Sage", "Criminal", "Noble", "Hermit", "Outlander"]
genders = ["Male", "Female", "Non-binary"]
image_styles = ["Standard", "8bit Style", "Anime Style"]

# --- Generation Functions ---
def generate_character(name, gender, race, character_class, background):
    return {"Name": name, "Gender": gender, "Race": race, "Class": character_class, "Background": background}

def generate_character_history(character, generate_history=True):
    if generate_history:
        prompt = f"Create a short backstory for a {character['Race']} {character['Class']} named {character['Name']}..."
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are a fantasy storyteller."},
                      {"role": "user", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"]
    return ""

def generate_character_image(character, style="Standard"):
    base_prompt = f"A full-body portrait of a {character['Gender']} {character['Race']} {character['Class']}."
    if style == "8bit Style":
        base_prompt += " pixelated sprite art, 8-bit game style"
    if style == "Anime Style":
        base_prompt += " anime art style, cel-shaded"
    response = openai.Image.create(model="dall-e-3", prompt=base_prompt, size="1024x1024")
    return response["data"][0]["url"]

def generate_npc():
    prompt = "Generate a unique fantasy NPC name and their profession."
    response = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
    content = response["choices"][0]["message"]["content"].strip()
    if ", " in content:
        name, role = content.split(", ", 1)
    else:
        name, role = content, "mysterious wanderer"
    return {"name": name, "role": role, "backstory": f"{name} is a {role} with a secret past."}

def generate_quest():
    prompt = "Create a fantasy quest with a title and short description."
    response = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
    parts = response["choices"][0]["message"]["content"].strip().split("\n", 1)
    return {"title": parts[0], "description": parts[1] if len(parts) > 1 else "A mysterious quest awaits."}

# --- UI ---
st.title("🎭 Mana Forge Character Generator & Toolkit")

mode = st.sidebar.radio("Select Mode:", ["Character", "Party", "Journal"])

# --- Character Tab ---
if mode == "Character":
    name = st.text_input("Enter character name:")
    selected_race = st.selectbox("Select race:", races)
    selected_gender = st.selectbox("Select gender:", genders)
    auto_generate = st.checkbox("Auto-generate class & background?", value=True)
    selected_style = st.selectbox("Select Art Style:", image_styles)
    generate_history = st.checkbox("Generate Character History")

    if not auto_generate:
        character_class = st.selectbox("Select class:", classes)
        background = st.selectbox("Select background:", backgrounds)

    if st.button("Generate Character"):
        if not name.strip():
            st.warning("Please enter a name.")
        else:
            if auto_generate:
                character_class = random.choice(classes)
                background = random.choice(backgrounds)

            char = generate_character(name, selected_gender, selected_race, character_class, background)
            char["History"] = generate_character_history(char, generate_history)
            image_urls = [generate_character_image(char, selected_style)]
            npc = generate_npc()
            quest = generate_quest()

            st.session_state.characters.append({"character": char, "npc": npc, "quest": quest, "images": image_urls})
            st.success(f"Character '{char['Name']}' Created!")

    for data in st.session_state.characters:
        ch, npc, quest, imgs = data['character'], data['npc'], data['quest'], data['images']
        st.subheader(ch['Name'])
        st.write(f"**{ch['Race']} {ch['Class']}** ({ch['Background']})")
        st.write(ch.get('History', 'No history generated'))
        st.image(imgs, use_container_width=True)
        st.write(f"**NPC:** {npc['name']} ({npc['role']}) - {npc['backstory']}")
        st.write(f"**Quest:** {quest['title']} — {quest['description']}")

# --- Party Tab (Infinite Story Mode) ---
elif mode == "Party":
    st.header("🧑‍🤝‍🧑 Party Builder (Infinite Story Mode)")
    if len(st.session_state.characters) < 2:
        st.warning("Create at least 2 characters first.")
    else:
        options = [c['character']['Name'] for c in st.session_state.characters]
        selected = st.multiselect("Select party members:", options)

        if st.button("Form Party") and selected:
            members = [c for c in st.session_state.characters if c['character']['Name'] in selected]
            names = ", ".join([m['character']['Name'] for m in members])
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Write an epic party story for: {names}"}]
            )
            story = response['choices'][0]['message']['content']
            st.session_state.parties.append({"members": members, "story": story})
            st.success("Party Created!")

    for idx, party in enumerate(st.session_state.parties):
        with st.expander(f"Party {idx+1}: {', '.join([m['character']['Name'] for m in party['members']])}"):
            st.write(party['story'])
            if st.button(f"Continue Story {idx+1}"):
                names = ", ".join([m['character']['Name'] for m in party['members']])
                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": f"Continue the story for {names}:\n\n{party['story']}"}]
                )
                continuation = response['choices'][0]['message']['content']
                party['story'] += "\n\n" + continuation

# --- Journal Tab (Global Log) ---
elif mode == "Journal":
    st.header("📓 World Journal (Everything So Far)")
    st.subheader("Characters")
    for char in st.session_state.characters:
        st.write(char['character'])

    st.subheader("Parties & Stories")
    for idx, party in enumerate(st.session_state.parties):
        st.markdown(f"**Party {idx+1}:** {', '.join([m['character']['Name'] for m in party['members']])}")
        st.text_area(f"Story {idx+1}", value=party['story'], height=150)
