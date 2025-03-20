
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
    return response["data"][0]["url"]

# Function to generate NPC
def generate_npc():
    npc_name = random.choice(["Aelric", "Talia", "Morthos", "Kaelen", "Elyssa", "Varian", "Lilith"])
    npc_role = random.choice(["merchant", "guard", "wizard", "priest", "knight", "bard", "rogue", "hunter"])
    npc_backstory = f"{npc_name} is a {npc_role} with a mysterious past, often seen in the tavern sharing tales of great adventures and hidden treasures."
    return {"name": npc_name, "role": npc_role, "backstory": npc_backstory}

# Function to generate quest
def generate_quest():
    quest_title = random.choice(["Rescue the Princess", "Retrieve the Lost Artifact", "Defeat the Dark Sorcerer", "Find the Hidden Treasure"])
    quest_description = f"Your task is to embark on an epic adventure to {quest_title}. Along the way, you'll face challenges, make allies, and confront enemies."
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

# Streamlit UI
st.title("Mana Forge Character Generator")

# Session state initialization for persistence
if "character" not in st.session_state:
    st.session_state.character = None
if "npc" not in st.session_state:
    st.session_state.npc = None
if "quest" not in st.session_state:
    st.session_state.quest = None

# Character selection dropdown
selected_race = st.selectbox("Select a race:", races)
selected_gender = st.selectbox("Select a gender:", genders)

# Text input for character name
name = st.text_input("Enter character name:", "")

# Generate character button
if st.button("Generate Character"):
    if not name.strip():  # Ensure a name is provided
        st.warning("Please enter a character name before generating.")
    else:
        st.session_state.character = generate_character(name, selected_gender, selected_race)
        st.session_state.character["History"] = generate_character_history(st.session_state.character)  # Generate character backstory
        st.session_state.character["Image"] = generate_character_image(st.session_state.character)  # Generate character image
        
        st.session_state.npc = generate_npc()  # Generate NPC
        st.session_state.quest = generate_quest()  # Generate quest

        st.success("Character Created Successfully!")
        st.write(f"**Name:** {st.session_state.character['Name']}")
        st.write(f"**Gender:** {st.session_state.character['Gender']}")
        st.write(f"**Race:** {st.session_state.character['Race']}")
        st.write(f"**Class:** {st.session_state.character['Class']}")
        st.write(f"**Background:** {st.session_state.character['Background']}")
        
        st.write("### Character History:")
        st.write(st.session_state.character["History"])
        
        st.write("### Character Portrait:")
        st.image(st.session_state.character["Image"], caption="Generated Character Portrait")

        # NPC and Quest Display
        st.write("### NPC:")
        st.write(f"**Name:** {st.session_state.npc['name']}")
        st.write(f"**Role:** {st.session_state.npc['role']}")
        st.write(f"**Backstory:** {st.session_state.npc['backstory']}")

        st.write("### Quest:")
        st.write(f"**Title:** {st.session_state.quest['title']}")
        st.write(f"**Description:** {st.session_state.quest['description']}")

        # Optional buttons for generating more images and creating PDFs
        if st.button("Generate 3D Art Assets (Turnarounds)"):
            st.write("Generating 3D turnarounds...")
            # Add logic for 3D turnarounds (this is a placeholder for now)
        
        if st.button("Download All Assets as PDF and ZIP"):
            st.write("Generating PDF and ZIP...")
            # Generate PDF
            pdf = create_pdf(st.session_state.character, st.session_state.npc, st.session_state.quest)
            
            # Save PDF to disk or stream it as download
            st.download_button(
                label="Download PDF",
                data=pdf,
                file_name=f"{st.session_state.character['Name']}_character.pdf",
                mime="application/pdf"
            )
