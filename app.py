import random
import streamlit as st
import json
import openai
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import base64

openai.api_key = st.secrets["OPENAI_API_KEY"]

# Options
races = ["Human", "Elf", "Dwarf", "Halfling", "Gnome", "Half-Orc", "Tiefling", "Dragonborn", "Kobold", "Lizardfolk", "Minotaur", "Troll", "Vampire", "Satyr", "Undead", "Lich", "Werewolf"]
classes = ["Fighter", "Wizard", "Rogue", "Cleric", "Barbarian", "Sorcerer", "Bard", "Monk", "Druid", "Ranger", "Paladin", "Warlock", "Artificer", "Blood Hunter", "Mystic", "Warden", "Berserker", "Necromancer", "Trickster", "Beast Master", "Alchemist", "Pyromancer", "Dark Knight"]
backgrounds = ["Acolyte", "Folk Hero", "Sage", "Criminal", "Noble", "Hermit", "Outlander", "Entertainer", "Artisan", "Sailor", "Soldier", "Charlatan", "Knight", "Pirate", "Spy", "Archaeologist", "Gladiator", "Inheritor", "Haunted One", "Bounty Hunter", "Explorer", "Watcher", "Traveler", "Phantom", "Vigilante"]
genders = ["Male", "Female", "Non-binary"]
image_styles = ["Standard", "8bit Style", "Anime Style", "Oil Painting", "Cyberpunk", "Watercolor"]

def generate_character(name, gender, race, character_class, background):
    return {
        "Name": name,
        "Gender": gender,
        "Race": race,
        "Class": character_class,
        "Background": background
    }

def generate_character_history(character, generate_history=True):
    if generate_history:
        prompt = f"Create a short backstory for a {character['Race']} {character['Class']} named {character['Name']} who has a {character['Background']} background."
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a creative storyteller."},
                {"role": "user", "content": prompt}
            ]
        )
        return response["choices"][0]["message"]["content"]
    return ""

def generate_character_image(character, style="Standard", custom_prompt=""):
    prompt = f"A full-body portrait of a {character['Gender']} {character['Race']} {character['Class']} with a {character['Background']} vibe."

    style_prompts = {
        "8bit Style": " pixelated 8-bit sprite, retro video game look",
        "Anime Style": " anime art style, colorful, cel-shaded",
        "Oil Painting": " in the style of a renaissance oil painting, dramatic lighting",
        "Cyberpunk": " futuristic cyberpunk theme, neon lights, urban background",
        "Watercolor": " soft watercolor painting style, artistic brushstrokes"
    }

    if style in style_prompts:
        prompt += style_prompts[style]
    
    if custom_prompt:
        prompt += f" {custom_prompt.strip()}"

    response = openai.Image.create(model="dall-e-3", prompt=prompt, size="1024x1024")
    return response["data"][0]["url"]

def generate_npc(generate_npc_text=True):
    if generate_npc_text:
        prompt = "Generate a fantasy NPC name and their profession."
        response = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        text = response["choices"][0]["message"]["content"].strip()
        parts = text.split(", ")
        return {"name": parts[0], "role": parts[1] if len(parts) > 1 else "mysterious traveler", "backstory": f"{parts[0]} is a {parts[1] if len(parts) > 1 else 'mysterious traveler'} with a secret past."}
    return {"name": "Unknown", "role": "Unknown", "backstory": "No backstory provided."}

def generate_quest(generate_quest_text=True):
    if generate_quest_text:
        prompt = "Create a fantasy quest with a title and short description."
        response = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        lines = response["choices"][0]["message"]["content"].split("\n", 1)
        return {"title": lines[0], "description": lines[1] if len(lines) > 1 else "An unknown adventure awaits."}
    return {"title": "Untitled Quest", "description": "No description provided."}

def generate_theme_song(prompt_text, save_path="theme_song.wav"):
    try:
        from audiocraft.models import MusicGen
        from audiocraft.data.audio import audio_write
        model = MusicGen.get_pretrained('melody')
        model.set_generation_params(duration=10)
        wav = model.generate([prompt_text])
        audio_write("output/theme_song", wav[0].cpu(), model.sample_rate, strategy="loudness", format="wav")
        return "output/theme_song.wav"
    except Exception:
        return None

def create_pdf(character, npc, quest):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    def write_line(text): nonlocal y; c.drawString(100, y, text); y -= 20

    write_line(f"{character['Name']} ({character['Gender']}, {character['Race']}, {character['Class']})")
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

def save_to_json(character, npc, quest, file_name="character_data.json"):
    with open(file_name, 'w') as f:
        json.dump({"character": character, "npc": npc, "quest": quest}, f, indent=4)

# Streamlit Interface
st.title("🎭 Mana Forge Character Generator")

name = st.text_input("Enter character name:")
selected_race = st.selectbox("Select race:", races)
selected_gender = st.selectbox("Select gender:", genders)

auto_generate_class = st.checkbox("Auto generate class and background?", value=True)
if auto_generate_class:
    selected_class = random.choice(classes)
    selected_background = random.choice(backgrounds)
    st.write(f"Generated Class: {selected_class} | Background: {selected_background}")
else:
    selected_class = st.selectbox("Select class:", classes)
    selected_background = st.selectbox("Select background:", backgrounds)

selected_style = st.selectbox("Select Art Style:", image_styles)
custom_prompt = st.text_input("Optional: Add custom style prompt (e.g., 'foggy background, warm colors')")

# Toggles
generate_history = st.checkbox("Generate character history", value=True)
generate_music = st.checkbox("Generate Theme Song")
generate_npc_text = st.checkbox("Generate NPC Text")
generate_quest_text = st.checkbox("Generate Quest Text")

if st.button("Generate Character"):
    if not name.strip():
        st.warning("Please enter a character name.")
    else:
        char = generate_character(name, selected_gender, selected_race, selected_class, selected_background)
        char["History"] = generate_character_history(char, generate_history)
        char["Image"] = generate_character_image(char, selected_style, custom_prompt)
        npc = generate_npc(generate_npc_text)
        quest = generate_quest(generate_quest_text)

        st.session_state.character = char
        st.session_state.npc = npc
        st.session_state.quest = quest

        st.markdown("### 🧙 Character Overview")
        st.markdown(f"{char['Name']} {char['Race']} {char['Gender']} {char['Class']} {char['Background']}")
        st.image(char["Image"], caption="Character Portrait")
        st.markdown("**Backstory:**")
        st.write(char["History"])

        st.markdown("### 🧑‍🤝‍🧑 NPC")
        st.write(npc)

        st.markdown("### 📜 Quest")
        st.write(quest)

        if generate_music:
            music_prompt = f"Fantasy orchestral theme for a {char['Race']} {char['Class']} named {char['Name']} from a {char['Background']} background."
            path = generate_theme_song(music_prompt)
            if path and os.path.exists(path):
                with open(path, "rb") as f:
                    st.audio(f.read(), format="audio/wav")
            else:
                st.error("Theme song generation failed or Audiocraft is not set up.")

        if st.button("📄 Download Character PDF"):
            pdf = create_pdf(char, npc, quest)
            st.download_button("Download PDF", pdf, file_name=f"{char['Name']}_character.pdf", mime="application/pdf")

        if st.button("💾 Save JSON"):
            save_to_json(char, npc, quest)
            st.success("Character data saved.")
