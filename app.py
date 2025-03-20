import random
import streamlit as st
import json
import openai

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

# Streamlit UI
st.title("Mana Forge Character Generator")

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
        character = generate_character(name, selected_gender, selected_race)
        character["History"] = generate_character_history(character)  # Generate character backstory
        character["Image"] = generate_character_image(character)  # Generate character image

        st.success("Character Created Successfully!")
        st.write(f"**Name:** {character['Name']}")
        st.write(f"**Gender:** {character['Gender']}")
        st.write(f"**Race:** {character['Race']}")
        st.write(f"**Class:** {character['Class']}")
        st.write(f"**Background:** {character['Background']}")

        st.write("### Character History:")
        st.write(character["History"])

        st.write("### Character Portrait:")
        st.image(character["Image"], caption="Generated Character Portrait")

        # Optional buttons for generating more images and creating PDFs
        if st.button("Generate 3D Art Assets (Turnarounds)"):
            st.write("Generating 3D turnarounds...")
            # Add logic for 3D turnarounds (this is a placeholder for now)
        
        if st.button("Download All Assets as PDF and ZIP"):
            st.write("Generating PDF and ZIP...")
            # Add logic to generate and download assets in PDF and ZIP formats (this is a placeholder for now)
