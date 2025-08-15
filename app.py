import random
import streamlit as st
import json
import openai
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import requests

# Load OpenAI key securely
openai.api_key = st.secrets["OPENAI_API_KEY"]

# -------------------- Session State --------------------
for key in ["characters", "parties", "stories", "worlds"]:
    if key not in st.session_state:
        st.session_state[key] = []

# -------------------- Character Data --------------------
races = ["Human", "Elf", "Dwarf", "Halfling", "Gnome", "Half-Orc", "Tiefling", "Dragonborn", "Kobold", "Lizardfolk", "Minotaur", "Troll", "Vampire", "Satyr", "Undead", "Lich", "Werewolf"]
classes = ["Fighter", "Wizard", "Rogue", "Cleric", "Barbarian", "Sorcerer", "Bard", "Monk", "Druid", "Ranger", "Paladin", "Warlock", "Artificer", "Blood Hunter", "Mystic", "Warden", "Berserker", "Necromancer", "Trickster", "Beast Master", "Alchemist", "Pyromancer", "Dark Knight"]
backgrounds = ["Acolyte", "Folk Hero", "Sage", "Criminal", "Noble", "Hermit", "Outlander", "Entertainer", "Artisan", "Sailor", "Soldier", "Charlatan", "Knight", "Pirate", "Spy", "Archaeologist", "Gladiator", "Inheritor", "Haunted One", "Bounty Hunter", "Explorer", "Watcher", "Traveler", "Phantom", "Vigilante"]
genders = ["Male", "Female", "Non-binary"]
image_styles = ["Standard", "8bit Style", "Anime Style"]

# -------------------- Utility Functions --------------------
def generate_character(name, gender, race, character_class, background):
    return {"Name": name, "Gender": gender, "Race": race, "Class": character_class, "Background": background}

def generate_character_history(character, generate_history=True):
    if generate_history:
        prompt = f"Create a short backstory for a {character['Race']} {character['Class']} named {character['Name']}. They come from a {character['Background']} background. Include motivations and key events and locations, don't use existing names from reality."
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are a creative storyteller in the style of George RR Martin."},
                      {"role": "user", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"]
    return ""

def generate_npc(generate_npc_text=True):
    if generate_npc_text:
        prompt = "Generate a unique fantasy NPC name and their profession."
        response = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        content = response["choices"][0]["message"]["content"].strip()
        if ", " in content:
            name, role = content.split(", ", 1)
        else:
            name, role = content, random.choice(["merchant", "guard", "wizard", "priest"])
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

def generate_character_image(character, style="Standard"):
    base_prompt = f"A full-body portrait of a {character['Gender']} {character['Race']} {character['Class']} with {character['Background']} vibes, heroic pose, detailed fantasy outfit."
    if style == "8bit Style": base_prompt += " pixelated sprite art, 8-bit game style"
    if style == "Anime Style": base_prompt += " anime art style, cel-shaded, colorful background"
    response = openai.Image.create(model="dall-e-3", prompt=base_prompt, size="1024x1024")
    return response["data"][0]["url"]

def generate_story(character, npc, quest):
    prompt = (
        f"Write a short D&D style story paragraph involving the following quest, party, and NPC:\n"
        f"Character: {character['Name']} ({character['Race']} {character['Class']}, {character['Background']})\n"
        f"NPC: {npc['name']} - {npc['role']}, {npc['backstory']}\n"
        f"Make it immersive and written like George RR Martin recounting an adventure."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a fantasy storyteller."}, {"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

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

# -------------------- World Builder --------------------
def initialize_world(world_name):
    world = {"name": world_name, "regions": {}}
    for i in range(5):
        for j in range(5):
            world["regions"][f"{i+1}-{j+1}"] = {
                "name": f"Location {i+1}-{j+1}",
                "characters": [],
                "npcs": [],
                "quests": [],
                "capital": False,
                "special_traits": [],
                "lore": ""
            }
    st.session_state.worlds.append(world)
    return world

def generate_world_journal(world):
    journal_entries = []
    for key, region in world["regions"].items():
        entry = f"**{region['name']}**\n"
        if region["capital"]: entry += "Capital Region\n"
        if region["special_traits"]:
            entry += "Special Traits:\n" + "\n".join([f"- {t}" for t in region["special_traits"]]) + "\n"
        if region["characters"]:
            entry += "Characters:\n" + "\n".join([f"- {c['Name']} ({c['Race']} {c['Class']})" for c in region["characters"]]) + "\n"
        if region["npcs"]:
            entry += "NPCs:\n" + "\n".join([f"- {n['name']} ({n['role']})" for n in region["npcs"]]) + "\n"
        if region["quests"]:
            entry += "Quests:\n" + "\n".join([f"- {q['title']}" for q in region["quests"]]) + "\n"

        # Append cached lore
        if region["lore"]:
            entry += f"Lore:\n{region['lore']}\n"
        journal_entries.append(entry)
    return "\n\n".join(journal_entries)

# -------------------- Streamlit UI --------------------
st.title("🎭 Mana Forge Character & World Generator")

mode = st.sidebar.radio("Select Mode:", ["Character", "Party", "Story Mode", "World Builder"])

# -------------------- CHARACTER TAB --------------------
if mode == "Character":
    st.header("🧙 Character Generator")
    name = st.text_input("Enter character name:")
    race = st.selectbox("Select race:", races)
    gender = st.selectbox("Select gender:", genders)
    auto_generate = st.checkbox("Auto-generate class & background?", value=True)
    style = st.selectbox("Select Art Style:", image_styles)
    generate_history_chk = st.checkbox("Generate Character History", value=True)

    if not auto_generate:
        char_class = st.selectbox("Select class:", classes)
        background = st.selectbox("Select background:", backgrounds)

    if st.button("Generate Character"):
        if not name.strip():
            st.warning("Enter a name")
        else:
            if auto_generate:
                char_class = random.choice(classes)
                background = random.choice(backgrounds)
            char = generate_character(name, gender, race, char_class, background)
            char["History"] = generate_character_history(char, generate_history_chk)
            npc = generate_npc()
            quest = generate_quest()
            st.session_state.characters.append({"character": char, "npc": npc, "quest": quest})
            st.success(f"Character '{name}' created!")

    if st.session_state.characters:
        for idx, data in enumerate(st.session_state.characters):
            exp = st.expander(f"{data['character']['Name']} ({data['character']['Class']})")
            with exp:
                st.json(data)

# -------------------- PARTY TAB --------------------
elif mode == "Party":
    st.header("🧑‍🤝‍🧑 Party Builder")
    if len(st.session_state.characters) < 2:
        st.warning("Create at least 2 characters first.")
    else:
        options = [f"{i+1}. {d['character']['Name']}" for i, d in enumerate(st.session_state.characters)]
        selected = st.multiselect("Select party members:", options)
        if st.button("Form Party") and selected:
            idxs = [options.index(s) for s in selected]
            members = [st.session_state.characters[i] for i in idxs]
            st.session_state.parties.append({"members": members, "story": ""})
            st.success("Party formed!")

# -------------------- STORY MODE TAB --------------------
elif mode == "Story Mode":
    st.header("📜 Quest & Adventure Generator")
    use_party = st.checkbox("Generate story for a Party instead of a single character?")

    if use_party and st.session_state.parties:
        options = [f"Party {i+1}: {', '.join([m['character']['Name'] for m in p['members']])}" for i, p in enumerate(st.session_state.parties)]
        idx = st.selectbox("Select Party:", range(len(options)), format_func=lambda i: options[i])
        selected_party = st.session_state.parties[idx]
    elif not use_party and st.session_state.characters:
        options = [c['character']['Name'] for c in st.session_state.characters]
        idx = st.selectbox("Select Character:", range(len(options)), format_func=lambda i: options[i])
        selected_character_data = st.session_state.characters[idx]
        selected_character = selected_character_data['character']
        selected_npc = selected_character_data['npc']
        selected_quest = selected_character_data['quest']
    else:
        st.warning("No characters or parties available.")
        st.stop()

    if st.button("Generate Story"):
        if use_party:
            names = ", ".join([m['character']['Name'] for m in selected_party['members']])
            prompt = f"Write an immersive D&D style story involving party members: {names}.\n\n{selected_party.get('story','')}"
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "You are a fantasy storyteller."},
                          {"role": "user", "content": prompt}]
            )
            new_story = response['choices'][0]['message']['content']
            selected_party['story'] += "\n" + new_story
            st.text_area("Infinite Story", selected_party['story'], height=300)
        else:
            story = generate_story(selected_character, selected_npc, selected_quest)
            st.text_area("Story", story, height=300)

# -------------------- WORLD BUILDER TAB --------------------
elif mode == "World Builder":
    st.header("🏞️ World Builder & Lore Generator")
    world_name = st.text_input("Enter new world name:")
    if st.button("Create World") and world_name.strip():
        w = initialize_world(world_name)
        st.success(f"World '{world_name}' created with {len(w['regions'])} regions!")

    if st.session_state.worlds:
        world_options = [w['name'] for w in st.session_state.worlds]
        idx = st.selectbox("Select World:", range(len(world_options)), format_func=lambda i: world_options[i])
        selected_world = st.session_state.worlds[idx]

        if st.button("Generate World Journal"):
            journal = generate_world_journal(selected_world)
            st.text_area(f"World Journal: {selected_world['name']}", journal, height=400)

        if st.button("Cache Lore for all Regions"):
            for key, region in selected_world["regions"].items():
                if not region["lore"]:
                    prompt = f"Generate lore for a fantasy region called {region['name']}."
                    response = openai.ChatCompletion.create(model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}])
                    region["lore"] = response['choices'][0]['message']['content']
            st.success("Lore cached for all regions!")

