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
def generate_character(name, gender, race, auto_generate_class_and_background):
    character_class = random.choice(classes) if auto_generate_class_and_background else st.selectbox("Select class:", classes)
    background = random.choice(backgrounds) if auto_generate_class_and_background else st.selectbox("Select background:", backgrounds)
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
            messages=[
                {"role": "system", "content": "You are a creative storyteller."},
                {"role": "user", "content": prompt}
            ]
        )
        return response["choices"][0]["message"]["content"]
    return ""

# DALL·E 3 character image
def generate_character_image(character):
    prompt = f"A full-body portrait of a {character['Gender']} {character['Race']} {character['Class']} with {character['Background']} vibes, heroic pose, detailed fantasy outfit."
    response = openai.Image.create(model="dall-e-3", prompt=prompt, size="1024x1024")
    return response["data"][0]["url"]

# NPC generation (optional)
def generate_npc(generate_npc_text=True):
    if generate_npc_text:
        prompt = "Generate a unique fantasy NPC name and their profession."
        response = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        npc_text = response["choices"][0]["message"]["content"].strip().split(", ")
        name = npc_text[0]
        role = npc_text[1] if len(npc_text) == 2 else random.choice(["merchant", "guard", "wizard", "priest"])
        backstory = f"{name} is a {role} with a mysterious past."
    else:
        name = "Unknown"
        role = "Unknown"
        backstory = "No backstory provided."
    
    return {"name": name, "role": role, "backstory": backstory}

# Quest generation (optional)
def generate_quest(generate_quest_text=True):
    if generate_quest_text:
        prompt = "Create a fantasy quest with a title and short description."
        response = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        parts = response["choices"][0]["message"]["content"].strip().split("\n", 1)
        title = parts[0]
        description = parts[1] if len(parts) > 1 else "A mysterious quest awaits."
    else:
        title = "Untitled Quest"
        description = "No description provided."
    
    return {"title": title, "description": description}

# Music generation using Audiocraft/MusicGen
def generate_theme_song(prompt_text, save_path="theme_song.wav"):
    try:
        from audiocraft.models import MusicGen
        from audiocraft.data.audio import audio_write

        model = MusicGen.get_pretrained('melody')
        model.set_generation_params(duration=10)
        wav = model.generate([prompt_text])
        audio_write("output/theme_song", wav[0].cpu(), model.sample_rate, strategy="loudness", format="wav")
        return "output/theme_song.wav"
    except Exception as e:
        return None

# PDF export
def create_pdf(character, npc, quest):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    def write_line(text): nonlocal y; c.drawString(100, y, text); y -= 20

    write_line(f"Character: {character['Name']} ({character['Gender']}, {character['Race']}, {character['Class']})")
    write_line(f"Background: {character['Background']}")
    write_line(f"History: {character['History'][:200]}...")
    write_line(f"NPC: {npc['name']} - {npc['role']}")
    write_line(f"NPC Backstory: {npc['backstory'][:100]}...")
    write_line(f"Quest: {quest['title']}")
    write_line(f"Quest Desc: {quest['description'][:150]}...")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# Save data to JSON
def save_to_json(character, npc, quest, file_name="character_data.json"):
    data = {
        "character": character,
        "npc": npc,
        "quest": quest
    }
    with open(file_name, 'w') as f:
        json.dump(data, f, indent=4)

# Streamlit UI
st.title("🎭 Mana Forge Character Generator")

name = st.text_input("Enter character name:")
selected_race = st.selectbox("Select race:", races)
selected_gender = st.selectbox("Select gender:", genders)

# Checkbox options
auto_generate_class_and_background = st.checkbox("Automatically generate class and background (or select manually)?", value=True)
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
        st.session_state.character = generate_character(name, selected_gender, selected_race, auto_generate_class_and_background)
        st.session_state.character["History"] = generate_character_history(st.session_state.character, generate_history)
        st.session_state.character["Image"] = generate_character_image(st.session_state.character)
        st.session_state.npc = generate_npc(generate_npc_text)
        st.session_state.quest = generate_quest(generate_quest_text)

        st.success("Character Created!")
        char = st.session_state.character
        st.image(char["Image"], caption="Character Portrait")
        st.markdown(f"**Name:** {char['Name']}\n\n**Race:** {char['Race']}  \n**Class:** {char['Class']}  \n**Background:** {char['Background']}")
        st.markdown("**History:**")
        st.write(char["History"])

        if generate_turnaround:
            st.image(generate_character_image(char), caption="Turnaround Image")
        if generate_location:
            st.image(generate_character_image(char), caption="Place of Origin")
        if generate_extra:
            st.image(generate_character_image(char), caption="Extra Image 1")
            st.image(generate_character_image(char), caption="Extra Image 2")

        st.markdown("### 🧑‍🤝‍🧑 NPC")
        st.write(st.session_state.npc)

        st.markdown("### 📜 Quest")
        st.write(st.session_state.quest)

        if generate_music:
            prompt = f"Fantasy orchestral theme for a {char['Race']} {char['Class']} named {char['Name']} from a {char['Background']} background."
            song_path = generate_theme_song(prompt)
            if song_path and os.path.exists(song_path):
                with open(song_path, "rb") as audio_file:
                    st.audio(audio_file.read(), format="audio/wav")
            else:
                st.warning("Failed to generate theme song. Check Audiocraft installation.")

        if st.button("📄 Download PDF"):
            pdf = create_pdf(st.session_state.character, st.session_state.npc, st.session_state.quest)
            st.download_button("Download PDF", pdf, file_name=f"{char['Name']}_profile.pdf", mime="application/pdf")

        if st.button("💾 Save Data as JSON"):
            save_to_json(st.session_state.character, st.session_state.npc, st.session_state.quest)
            st.success("Data saved to JSON.")
