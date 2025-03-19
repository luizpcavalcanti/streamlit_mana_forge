import random
import streamlit as st
import json
import openai

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

# Function to generate a character description
def generate_description(character):
    return f"{character['Name']} is a {character['Gender'].lower()} {character['Race'].lower()} {character['Class'].lower()} with a background as a {character['Background'].lower()}."

# Function to generate an image using OpenAI
def generate_character_image(description):
    response = openai.images.generate(
        model="dall-e-2",
        prompt=description,
        n=1,
        size="512x512"
    )
    return response.data[0].url

# Function to load characters from a file
def load_characters():
    try:
        with open("characters.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# Function to save characters to a file
def save_characters(characters):
    with open("characters.json", "w") as file:
        json.dump(characters, file, indent=4)

# Streamlit UI
st.title("D&D Character Generator")

# Character selection dropdown
selected_race = st.selectbox("Select a race:", races)
selected_gender = st.selectbox("Select a gender:", genders)

# Text input for character name
name = st.text_input("Enter character name:", "")

# Load characters
characters = load_characters()

# Generate character button
if st.button("Generate Character"):
    if not name.strip():  # Ensure a name is provided
        st.warning("Please enter a character name before generating.")
    else:
        character = generate_character(name, selected_gender, selected_race)
        description = generate_description(character)
        image_url = generate_character_image(description)
        character["Image"] = image_url
        characters.append(character)
        save_characters(characters)
        
        st.success("Character Created Successfully!")
        st.write(f"**Name:** {character['Name']}")
        st.write(f"**Gender:** {character['Gender']}")
        st.write(f"**Race:** {character['Race']}")
        st.write(f"**Class:** {character['Class']}")
        st.write(f"**Background:** {character['Background']}")
        st.image(image_url, caption=character['Name'])

# Display all characters as a list with expandable details
st.write("### Saved Characters:")
if characters:
    selected_character = st.selectbox("Select a character to view details:", [c["Name"] for c in characters])
    
    for character in characters:
        if character["Name"] == selected_character:
            with st.expander(f"{character['Name']} - Click to view details"):
                st.write(f"- **Gender:** {character['Gender']}")
                st.write(f"- **Race:** {character['Race']}")
                st.write(f"- **Class:** {character['Class']}")
                st.write(f"- **Background:** {character['Background']}")
                if "Image" in character:
                    st.image(character["Image"], caption=character["Name"])
else:
    st.write("No characters available.")
