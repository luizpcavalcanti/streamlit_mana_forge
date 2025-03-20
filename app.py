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
    character = {
        "Name": name,
        "Gender": gender,
        "Race": race,
        "Class": random.choice(classes),
        "Background": random.choice(backgrounds),
    }
    return character

# Function to generate a character history using GPT-4
def generate_character_history(character):
    prompt = f"Create a short backstory for a {character['Race']} {character['Class']} named {character['Name']}. They come from a {character['Background']}
