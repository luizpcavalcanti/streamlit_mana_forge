import random
import streamlit as st
import openai
import os
import shutil
import zipfile
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import requests

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
    return response["data"][0]["url"]
# Function to generate NPC (name, role, and backstory) using GPT-4
def generate_npc():
    prompt = "Create an NPC character for a D&D game. Provide the NPC's name, role (e.g., merchant, guard, wizard), and a short backstory that fits within a fantasy adventure setting."
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a creative storyteller crafting NPCs for a fantasy adventure."},
            {"role": "user", "content": prompt}
        ]
    )
    npc_info = response["choices"][0]["message"]["content"]
    # Split the NPC info based on new lines
    npc_lines = npc_info.split('\n')

    # Try extracting the NPC details based on the format
    try:
        npc_name = npc_lines[0].strip()  # First line should contain the NPC name
        npc_role = npc_lines[1].strip()  # Second line should contain the NPC role
        npc_backstory = npc_lines[2].strip()  # Third line should contain the NPC backstory
    except IndexError:
        npc_name = "Unknown NPC"
        npc_role = "Unknown Role"
        npc_backstory = "No backstory available."

    return {"name": npc_name, "role": npc_role, "backstory": npc_backstory}

# Function to generate a quest (title and description) using GPT-4
def generate_quest():
    prompt = "Create a quest for a D&D game. Provide a title for the quest and a detailed description of the quest's objective, challenges, and any important context or background."
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a creative storyteller crafting quests for a fantasy adventure."},
            {"role": "user", "content": prompt}
        ]
    )
    quest_info = response["choices"][0]["message"]["content"]
    # Extracting quest information
    quest_lines = quest_info.split('\n')
    quest_title = quest_lines[0].strip().split(':')[1].strip()
    quest_description = quest_lines[1].strip().split(':')[1].strip()
    return {"title": quest_title, "description": quest_description}

# Function to generate PDF
def create_pdf(character, npc, quest):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Character info
    c.drawString(100, 750, f"Character Name: {character['Name']}")
    c.drawString(100, 730, f"Gender: {character['Gender']}")
    c.drawString(100, 710, f"Race: {character['Race']}")
    c.drawString(100, 690, f"Class: {character['Class']}")
    c.drawString(100, 670, f"Background: {character['Background']}")
    c.drawString(100, 650, f"History: {character['History']}")
    
    # NPC info
    c.drawString(100, 620, f"NPC Name: {npc['name']}")
    c.drawString(100, 600, f"NPC Role: {npc['role']}")
    c.drawString(100, 580, f"NPC Backstory: {npc['backstory']}")
    
    # Quest info
    c.drawString(100, 550, f"Quest Title: {quest['title']}")
    c.drawString(100, 530, f"Quest Description: {quest['description']}")
    
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer

# Function to create a ZIP file with assets
def create_zip(character, image_url):
    # Create a temporary directory to store assets
    temp_dir = "/tmp/assets"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Save character data to a file
    with open(os.path.join(temp_dir, f"{character['Name']}_character.json"), "w") as f:
        json.dump(character, f)
    
    # Download character image
    img_response = requests.get(image_url)
    with open(os.path.join(temp_dir, f"{character['Name']}_portrait.png"), "wb") as f:
        f.write(img_response.content)

    # Create PDF and save it
    pdf = create_pdf(character, generate_npc(), generate_quest())
    with open(os.path.join(temp_dir, f"{character['Name']}_character.pdf"), "wb") as f:
        f.write(pdf.read())

    # Create ZIP file
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), temp_dir))

    zip_buffer.seek(0)
    
    # Clean up temporary directory
    shutil.rmtree(temp_dir)
    
    return zip_buffer

# Streamlit UI
st.title("Mana Forge Character Generator")

# Session state initialization for persistence
if "character" not in st.session_state:
    st.session_state.character = None

# Character selection dropdown
selected_race = st.selectbox("Select a race:", races)
selected_gender = st.selectbox("Select a gender:", genders)

# Text input for character name
name = st.text_input("Enter character name:", "")

# Generate character automatically on input completion
if name and st.button("Generate Character"):
    st.session_state.character = generate_character(name, selected_gender, selected_race)
    st.session_state.character["History"] = generate_character_history(st.session_state.character)
    st.session_state.character["Image"] = generate_character_image(st.session_state.character)
    
    # Show character info
    st.write(f"**Name:** {st.session_state.character['Name']}")
    st.write(f"**Gender:** {st.session_state.character['Gender']}")
    st.write(f"**Race:** {st.session_state.character['Race']}")
    st.write(f"**Class:** {st.session_state.character['Class']}")
    st.write(f"**Background:** {st.session_state.character['Background']}")
    
    st.write("### Character History:")
    st.write(st.session_state.character["History"])
    
    st.write("### Character Portrait:")
    st.image(st.session_state.character["Image"], caption="Generated Character Portrait")
    
    # Generate NPC and Quest
    npc = generate_npc()
    quest = generate_quest()
    
    # Show NPC and Quest Info
    st.write("### NPC:")
    st.write(f"**Name:** {npc['name']}")
    st.write(f"**Role:** {npc['role']}")
    st.write(f"**Backstory:** {npc['backstory']}")
    
    st.write("### Quest:")
    st.write(f"**Title:** {quest['title']}")
    st.write(f"**Description:** {quest['description']}")
    
    # Generate ZIP file automatically
    zip_buffer = create_zip(st.session_state.character, st.session_state.character["Image"])
    
    # Provide download link
    st.download_button(
        label="Download All Assets as ZIP",
        data=zip_buffer,
        file_name=f"{st.session_state.character['Name']}_assets.zip",
        mime="application/zip"
    )
