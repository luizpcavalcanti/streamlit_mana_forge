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
def generate_character(name, gender, race):
    return {
        "Name": name,
        "Gender": gender,
        "Race": race,
        "Class": random.choice(classes),
        "Background": random.choice(backgrounds)
    }

# GPT-based history (optional)
def generate_character_history(character, prompt=None):
    if not prompt:
        return ""
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a creative storyteller."},
            {"role": "user", "content": prompt}
        ]
    )
    return response["choices"][0]["message"]["content"]

# DALL·E 3 character image (optional)
def generate_character_image(prompt):
    response = openai.Image.create(model="dall-e-3", prompt=prompt, size="1024x1024")
    return response["data"][0]["url"]

# NPC generation (optional)
def generate_npc(prompt):
    if not prompt:
        return {}
    response = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
    return {"text": response["choices"][0]["message"]["content"].strip()}

# Quest generation (optional)
def generate_quest(prompt):
    if not prompt:
        return {}
    response = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
    return {"text": response["choices"][0]["message"]["content"].strip()}

# Music generation using Audiocraft/MusicGen (optional)
def generate_theme_song(prompt_text, save_path="theme_song.wav"):
    try:
        from audiocraft.models import MusicGen
        from audiocraft.data.audio import audio_write

        model = MusicGen.get_pretrained('melody')
        model.set_generation_params(duration=10)
        wav = model.generate([prompt_text])
        audio_write(save_path.replace(".wav", ""), wav[0].cpu(), model.sample_rate, strategy="loudness", format="wav")
        return save_path
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
    if "History" in character and character["History"]:
        write_line(f"History: {character['History'][:200]}...")
    if npc:
        write_line(f"NPC: {npc.get('text', '')[:100]}...")
    if quest:
        write_line(f"Quest: {quest.get('text', '')[:150]}...")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# Streamlit UI
st.title("🎭 Mana Forge Character Generator")

name = st.text_input("Enter character name:")
selected_race = st.selectbox("Select race:", races)
selected_gender = st.selectbox("Select gender:", genders)

# Optional toggles
generate_history = st.checkbox("🧠 Generate Character Backstory")
history_prompt = st.text_area("Backstory Prompt", "", disabled=not generate_history)

generate_image = st.checkbox("🖼️ Generate Character Image")
image_prompt = st.text_area("Image Prompt", "", disabled=not generate_image)

generate_npc_toggle = st.checkbox("🧑‍🤝‍🧑 Generate NPC")
npc_prompt = st.text_area("NPC Prompt", "", disabled=not generate_npc_toggle)

generate_quest_toggle = st.checkbox("📜 Generate Quest")
quest_prompt = st.text_area("Quest Prompt", "", disabled=not generate_quest_toggle)

generate_music = st.checkbox("🎼 Generate Theme Song")
music_prompt = st.text_input("Theme Song Prompt", value="", disabled=not generate_music)

if st.button("Generate Character"):
    if not name.strip():
        st.warning("Please enter a name.")
    else:
        st.session_state.character = generate_character(name, selected_gender, selected_race)
        
        if generate_history:
            st.session_state.character["History"] = generate_character_history(st.session_state.character, history_prompt)

        if generate_image and image_prompt:
            st.session_state.character["Image"] = generate_character_image(image_prompt)

        if generate_npc_toggle and npc_prompt:
            st.session_state.npc = generate_npc(npc_prompt)
        else:
            st.session_state.npc = {}

        if generate_quest_toggle and quest_prompt:
            st.session_state.quest = generate_quest(quest_prompt)
        else:
            st.session_state.quest = {}

        st.success("Character Created!")
        char = st.session_state.character

        if "Image" in char:
            st.image(char["Image"], caption="Character Portrait")

        st.markdown(f"**Name:** {char['Name']}  ")
        st.markdown(f"**Race:** {char['Race']}  ")
        st.markdown(f"**Class:** {char['Class']}  ")
        st.markdown(f"**Background:** {char['Background']}  ")

        if "History" in char:
            st.markdown("**History:**")
            st.write(char["History"])

        if st.session_state.npc:
            st.markdown("### 🧑‍🤝‍🧑 NPC")
            st.write(st.session_state.npc["text"])

        if st.session_state.quest:
            st.markdown("### 📜 Quest")
            st.write(st.session_state.quest["text"])

        if generate_music and music_prompt.strip():
            song_path = generate_theme_song(music_prompt)
            if song_path and os.path.exists(song_path):
                with open(song_path, "rb") as audio_file:
                    st.audio(audio_file.read(), format="audio/wav")
                st.success("Theme song generated.")
            else:
                st.warning("Failed to generate theme song. Check Audiocraft installation.")

        if st.button("📄 Download PDF"):
            pdf = create_pdf(st.session_state.character, st.session_state.npc, st.session_state.quest)
            st.download_button("Download PDF", pdf, file_name=f"{char['Name']}_profile.pdf", mime="application/pdf")
