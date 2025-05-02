import random
import streamlit as st
import json
import openai
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import base64

# Load OpenAI key securely
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Character traits
races = ["Human", "Elf", "Dwarf", "Halfling", "Gnome", "Half-Orc", "Tiefling", "Dragonborn", "Kobold", "Lizardfolk", "Minotaur", "Troll", "Vampire", "Satyr", "Undead", "Lich", "Werewolf"]
classes = ["Fighter", "Wizard", "Rogue", "Cleric", "Barbarian", "Sorcerer", "Bard", "Monk", "Druid", "Ranger", "Paladin", "Warlock", "Artificer", "Blood Hunter", "Mystic", "Warden", "Berserker", "Necromancer", "Trickster", "Beast Master", "Alchemist", "Pyromancer", "Dark Knight"]
backgrounds = ["Acolyte", "Folk Hero", "Sage", "Criminal", "Noble", "Hermit", "Outlander", "Entertainer", "Artisan", "Sailor", "Soldier", "Charlatan", "Knight", "Pirate", "Spy", "Archaeologist", "Gladiator", "Inheritor", "Haunted One", "Bounty Hunter", "Explorer", "Watcher", "Traveler", "Phantom", "Vigilante"]
genders = ["Male", "Female", "Non-binary"]

# Character generation
def generate_character(name, gender, race, character_class, background):
    return {
        "Name": name,
        "Gender": gender,
        "Race": race,
        "Class": character_class,
        "Background": background
    }

# GPT-based history (optional)
def generate_character_history(character, generate_history=True):
    if generate_history:
        prompt = f"Create a short backstory for a {character['Race']} {character['Class']} named {character['Name']}. They come from a {character['Background']} background. Include motivations, key events, and a mystery."
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are a creative storyteller."},
                      {"role": "user", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"]
    return ""

# DALL·E 3 character image
def generate_character_image(character):
    prompt = f"A full-body portrait of a {character['Gender']} {character['Race']} {character['Class']} with {character['Background']} vibes, heroic pose, detailed fantasy outfit."
    response = openai.Image.create(model="dall-e-3", prompt=prompt, size="1024x1024")
    return response["data"][0]["url"]

# Streamlit UI
st.title("🎭 Mana Forge Character Generator")

name = st.text_input("Enter character name:")
selected_race = st.selectbox("Select race:", races)
selected_gender = st.selectbox("Select gender:", genders)

# Checkbox options
auto_generate_class_and_background = st.checkbox("Automatically generate class and background (or select manually)?", value=True)

# Initialize session state variables for class and background to prevent auto-generation on non-related checkbox actions
if 'character_class' not in st.session_state:
    st.session_state.character_class = random.choice(classes)
if 'background' not in st.session_state:
    st.session_state.background = random.choice(backgrounds)

# Show class and background selection based on checkbox
if auto_generate_class_and_background:
    # Only update class and background if checkbox is checked
    character_class = random.choice(classes)
    background = random.choice(backgrounds)
    st.session_state.character_class = character_class
    st.session_state.background = background
    st.write(f"Class: {character_class} | Background: {background}")
else:
    character_class = st.selectbox("Select class:", classes, index=classes.index(st.session_state.character_class))
    background = st.selectbox("Select background:", backgrounds, index=backgrounds.index(st.session_state.background))

# Other checkboxes that should not affect the auto-generated class/background
generate_music = st.checkbox("Generate Theme Song (Audiocraft)")
generate_turnaround = st.checkbox("Generate 360° Turnaround")
generate_location = st.checkbox("Generate Place of Origin")
generate_extra = st.checkbox("Generate Extra Images")
generate_history = st.checkbox("Generate Character History")
generate_npc_text = st.checkbox("Generate NPC Text")
generate_quest_text = st.checkbox("Generate Quest Text")

if st.button("Generate Character"):
    if not name.strip():
        st.warning("Please enter a name.")
    else:
        # Generate the character
        st.session_state.character = generate_character(name, selected_gender, selected_race, st.session_state.character_class, st.session_state.background)
        st.session_state.character["History"] = generate_character_history(st.session_state.character, generate_history)
        st.session_state.character["Image"] = generate_character_image(st.session_state.character)

        st.success("Character Created!")
        char = st.session_state.character
        st.image(char["Image"], caption="Character Portrait")
        st.markdown(f"**Name:** {char['Name']}\n\n**Race:** {char['Race']}  \n**Class:** {char['Class']}  \n**Background:** {char['Background']}")
        st.markdown("**History:**")
        st.write(char["History"])

        # Additional content generation based on checkboxes
        if generate_turnaround:
            st.image(generate_character_image(char), caption="Turnaround Image")
        if generate_location:
            st.image(generate_character_image(char), caption="Place of Origin")
        if generate_extra:
            st.image(generate_character_image(char), caption="Extra Image 1")
            st.image(generate_character_image(char), caption="Extra Image 2")

        # NPC and quest generation
        st.markdown("### 🧑‍🤝‍🧑 NPC")
        st.session_state.npc = generate_npc(generate_npc_text)
        st.write(st.session_state.npc)

        st.markdown("### 📜 Quest")
        st.session_state.quest = generate_quest(generate_quest_text)
        st.write(st.session_state.quest)

        # Music generation
        if generate_music:
            prompt = f"Fantasy orchestral theme for a {char['Race']} {char['Class']} named {char['Name']} from a {char['Background']} background."
            song_path = generate_theme_song(prompt)
            if song_path and os.path.exists(song_path):
                with open(song_path, "rb") as audio_file:
                    st.audio(audio_file.read(), format="audio/wav")
            else:
                st.warning("Failed to generate theme song. Check Audiocraft installation.")

        # PDF and JSON download options
        if st.button("📄 Download PDF"):
            pdf = create_pdf(st.session_state.character, st.session_state.npc, st.session_state.quest)
            st.download_button("Download PDF", pdf, file_name=f"{char['Name']}_profile.pdf", mime="application/pdf")

        if st.button("💾 Save Data as JSON"):
            save_to_json(st.session_state.character, st.session_state.npc, st.session_state.quest)
            st.success("Data saved to JSON.")
