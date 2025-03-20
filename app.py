import random
import streamlit as st
import json
import openai
import os
import shutil
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Securely load the OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Define character races, classes, backgrounds, and genders
races = [
    "Human", "Elf", "Dwarf", "Halfling", "Gnome", "Half-Orc", "Tiefling", "Dragonborn", "Kobold", "Lizardfolk", "Minotaur",
    "Troll", "Vampire", "Satyr", "Undead", "Lich", "Werewolf"
]

classes = [
    "Fighter", "Wizard", "Rogue", "Cleric", "Barbarian", "Sorcerer", "Bard", "Monk",
    "Druid", "Ranger", "Paladin", "Warlock", "Artificer", "Blood Hunter", "Mystic",
    "Warden", "Berserker", "Necromancer", "Trickster", "Beast Master", "Alchemist", "Pyromancer", "Dark Knight"
]

backgrounds = [
    "Acolyte", "Folk Hero", "Sage", "Criminal", "Noble", "Hermit", "Outlander", "Entertainer",
    "Artisan", "Sailor", "Soldier", "Charlatan", "Knight", "Pirate", "Spy", "Archaeologist", "Gladiator",
    "Inheritor", "Haunted One", "Bounty Hunter", "Explorer", "Watcher", "Traveler", "Phantom", "Vigilante"
]

genders = ["Male", "Female", "Non-binary"]

# Function to generate a random character
def generate_character(name, gender, race):
    return {
        "Name": name,
        "Gender": gender,
        "Race": race,
        "Class": random.choice(classes),
        "Background": random.choice(backgrounds)
    }

# Function to generate a character history using GPT-4
def generate_character_history(character):
    prompt = f"Create a short backstory for a {character['Race']} {character['Class']} named {character['Name']}. They come from a {character['Background']} background. The story should include their motivations, key life events, and an intriguing mystery."
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[ 
            {"role": "system", "content": "You are a creative storyteller crafting fantasy character backstories."},
            {"role": "user", "content": prompt}
        ]
    )
    return response["choices"][0]["message"]["content"]
# Function to generate a full-body character image using OpenAI's DALL·E 3
def generate_character_image(character):
    prompt = f"A full-body portrait of a {character['Gender']} {character['Race']} {character['Class']} wearing attire fitting their {character['Background']} background. The character should be standing, in a heroic pose, with detailed armor/clothing and weapons appropriate for their class."
    
    response = openai.Image.create(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024"
    )
    
    # Ensure the response contains the expected structure
    try:
        return response["data"][0]["url"]
    except (KeyError, IndexError):
        st.error("Error: Failed to generate character image. Try again.")
        return None

# Function to generate NPC using AI

def generate_npc():
    prompt = (
        "Generate a fantasy NPC with a name, role, and an interesting backstory. "
        "Respond in JSON format with the following keys: "
        '{"name": "NPC name", "role": "NPC role", "backstory": "NPC backstory"}'
    )

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a creative storyteller generating fantasy NPCs. Output must be valid JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format="json"
    )

    npc_data = response["choices"][0]["message"]["content"]

    try:
        return json.loads(npc_data)
    except json.JSONDecodeError:
        st.error("Error: OpenAI response is not valid JSON. Try again.")
        return None

# Function to generate quest using AI
def generate_quest():
    prompt = (
        "Generate a fantasy quest with a title and an engaging description. "
        "Respond in JSON format with the following keys: "
        '{"title": "Quest title", "description": "Quest description"}'
    )

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a creative storyteller generating fantasy quests. Output must be valid JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format="json"
    )

    quest_data = response["choices"][0]["message"]["content"]

    try:
        return json.loads(quest_data)
    except json.JSONDecodeError:
        st.error("Error: OpenAI response is not valid JSON. Try again.")
        return None

# Initialize session state
if "character" not in st.session_state:
    st.session_state.character = None
if "npc" not in st.session_state:
    st.session_state.npc = None
if "quest" not in st.session_state:
    st.session_state.quest = None

st.title("Mana Forge Character Generator")

# Character selection dropdown
selected_race = st.selectbox("Select a race:", races)
selected_gender = st.selectbox("Select a gender:", genders)
name = st.text_input("Enter character name:", "")

if st.button("Generate Character"):
    if not name.strip():
        st.warning("Please enter a character name before generating.")
    else:
        st.session_state.character = generate_character(name, selected_gender, selected_race)
        st.session_state.character["History"] = generate_character_history(st.session_state.character)
        st.session_state.character["Image"] = generate_character_image(st.session_state.character)
        st.session_state.npc = generate_npc()
        st.session_state.quest = generate_quest()
        st.success("Character Created Successfully!")

if st.session_state.character:
    st.write(f"**Name:** {st.session_state.character['Name']}")
    st.write(f"**Gender:** {st.session_state.character['Gender']}")
    st.write(f"**Race:** {st.session_state.character['Race']}")
    st.write(f"**Class:** {st.session_state.character['Class']}")
    st.write(f"**Background:** {st.session_state.character['Background']}")
    st.write("### Character History:")
    st.write(st.session_state.character["History"])
    st.write("### Character Portrait:")
    st.image(st.session_state.character["Image"], caption="Generated Character Portrait")

if st.session_state.npc:
    st.write("### NPC:")
    st.write(f"**Name:** {st.session_state.npc['name']}")
    st.write(f"**Role:** {st.session_state.npc['role']}")
    st.write(f"**Backstory:** {st.session_state.npc['backstory']}")

if st.session_state.quest:
    st.write("### Quest:")
    st.write(f"**Title:** {st.session_state.quest['title']}")
    st.write(f"**Description:** {st.session_state.quest['description']}")
