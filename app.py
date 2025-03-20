import random
import streamlit as st
import json
import openai
import zipfile
import os
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
    prompt = f"Create a short backstory for a {character['Gender']} {character['Race']} {character['Class']} named {character['Name']}. They come from a {character['Background']} background. The story should include their motivations, key life events, and an intriguing mystery."
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[ 
            {"role": "system", "content": "You are a creative storyteller crafting fantasy character backstories."},
            {"role": "user", "content": prompt}
        ]
    )
    return response["choices"][0]["message"]["content"]

# Function to generate an image using OpenAI's DALL·E 3
def generate_character_image(character):
    prompt = f"A detailed fantasy portrait of a {character['Gender']} {character['Race']} {character['Class']} wearing attire fitting their {character['Background']} background."
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

        # Generate additional art assets
        if st.button("Generate 3D Art Assets"):
            # Generate 2 turn-around pictures (for 3D modeling or 360 preview)
            st.write("Generating 2 turn-around images for 3D modeling...")
            # Note: Here, you can add specific logic for generating turn-around images using DALL·E, for example.
            # Currently, it's placeholder logic.
            st.image(character["Image"], caption="Turnaround View 1")
            st.image(character["Image"], caption="Turnaround View 2")

        # Generate a ZIP file with all generated assets
        if st.button("Download ZIP"):
            # Prepare content
            output_dir = f"/tmp/{character['Name']}_assets"
            os.makedirs(output_dir, exist_ok=True)

            # Save character data in a PDF
            pdf_path = os.path.join(output_dir, f"{character['Name']}_character.pdf")
            c = canvas.Canvas(pdf_path, pagesize=letter)
            c.drawString(100, 750, f"Character: {character['Name']}")
            c.drawString(100, 730, f"Gender: {character['Gender']}")
            c.drawString(100, 710, f"Race: {character['Race']}")
            c.drawString(100, 690, f"Class: {character['Class']}")
            c.drawString(100, 670, f"Background: {character['Background']}")
            c.drawString(100, 650, f"History: {character['History']}")
            c.drawImage(character["Image"], 100, 500, width=200, height=200)
            c.save()

            # Add the character images and data to the ZIP file
            zip_file_path = f"/tmp/{character['Name']}_assets.zip"
            with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                zipf.write(pdf_path, os.path.basename(pdf_path))  # Add PDF to ZIP
                # Optionally add the character images (both portrait and 3D art assets)
                zipf.write(character["Image"], f"{character['Name']}_portrait.png")  # Add portrait image

            # Provide a download link for the ZIP file
            with open(zip_file_path, "rb") as f:
                st.download_button(
                    label="Download All Character Assets",
                    data=f,
                    file_name=f"{character['Name']}_assets.zip",
                    mime="application/zip"
                )
