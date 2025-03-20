import random
import streamlit as st
import json
import openai
import torch
from diffusers import DiffusionPipeline

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

# Load the image generation model
pipe = DiffusionPipeline.from_pretrained("black-forest-labs/FLUX.1-schnell").to("cpu")

def generate_character(name, gender, race):
    return {
        "Name": name,
        "Gender": gender,
        "Race": race,
        "Class": random.choice(classes),
        "Background": random.choice(backgrounds)
    }

def generate_character_history(character):
    prompt = f"Create a short backstory for a {character['Race']} {character['Class']} named {character['Name']}. " \
             f"They come from a {character['Background']} background. The story should include their motivations, key life events, and an intriguing mystery."
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a creative storyteller crafting fantasy character backstories."},
            {"role": "user", "content": prompt}
        ]
    )
    return response["choices"][0]["message"]["content"]

def generate_quest(character):
    prompt = f"Create a quest for a {character['Race']} {character['Class']} with a {character['Background']} background. The quest should be personalized, based on their background, and should lead to an intriguing plot."
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a creative quest designer crafting personalized quests."},
            {"role": "user", "content": prompt}
        ]
    )
    return response["choices"][0]["message"]["content"]

def generate_npc(character):
    prompt = f"Create an NPC related to a {character['Race']} {character['Class']} with a {character['Background']} background. The NPC should have a significant role in the character's story."
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a creative storyteller crafting NPCs related to a character's background."},
            {"role": "user", "content": prompt}
        ]
    )
    return response["choices"][0]["message"]["content"]

def generate_character_image(character):
    prompt = f"A detailed fantasy portrait of a {character['Race']} {character['Class']} with a {character['Background']} background, high quality, 8K, realistic lighting."
    image = pipe(prompt).images[0]
    return image

# Streamlit UI
st.title("Mana Forge Character Generator")

selected_race = st.selectbox("Select a race:", races)
selected_gender = st.selectbox("Select a gender:", genders)
name = st.text_input("Enter character name:", "")

if st.button("Generate Character"):
    if not name.strip():
        st.warning("Please enter a character name before generating.")
    else:
        character = generate_character(name, selected_gender, selected_race)
        character["History"] = generate_character_history(character)
        character["Quest"] = generate_quest(character)
        character["NPC"] = generate_npc(character)
        
        st.success("Character Created Successfully!")
        st.write(f"**Name:** {character['Name']}")
        st.write(f"**Gender:** {character['Gender']}")
        st.write(f"**Race:** {character['Race']}")
        st.write(f"**Class:** {character['Class']}")
        st.write(f"**Background:** {character['Background']}")
        st.write("### Character History:")
        st.write(character["History"])
        st.write("### Character Quest:")
        st.write(character["Quest"])
        st.write("### Related NPC:")
        st.write(character["NPC"])
        
        st.write("### Character Image:")
        character_image = generate_character_image(character)
        st.image(character_image, caption=f"{character['Name']} - {character['Race']} {character['Class']}", use_column_width=True)
