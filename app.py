import random
import streamlit as st
import json
import openai
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
import base64

# Load OpenAI key securely
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Initialize session state
if "characters" not in st.session_state:
    st.session_state.characters = []

# Character traits
races = ["Human", "Elf", "Dwarf", "Halfling", "Gnome", "Half-Orc", "Tiefling", "Dragonborn", "Kobold", "Lizardfolk", "Minotaur", "Troll", "Vampire", "Satyr", "Undead", "Lich", "Werewolf"]
classes = ["Fighter", "Wizard", "Rogue", "Cleric", "Barbarian", "Sorcerer", "Bard", "Monk", "Druid", "Ranger", "Paladin", "Warlock", "Artificer", "Blood Hunter", "Mystic", "Warden", "Berserker", "Necromancer", "Trickster", "Beast Master", "Alchemist", "Pyromancer", "Dark Knight"]
backgrounds = ["Acolyte", "Folk Hero", "Sage", "Criminal", "Noble", "Hermit", "Outlander", "Entertainer", "Artisan", "Sailor", "Soldier", "Charlatan", "Knight", "Pirate", "Spy", "Archaeologist", "Gladiator", "Inheritor", "Haunted One", "Bounty Hunter", "Explorer", "Watcher", "Traveler", "Phantom", "Vigilante"]
genders = ["Male", "Female", "Non-binary"]
image_styles = ["Standard", "8bit Style", "Anime Style"]

# Character generation
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

def generate_character_image(character, style="Standard"):
    base_prompt = f"A full-body portrait of a {character['Gender']} {character['Race']} {character['Class']} with {character['Background']} vibes, heroic pose, detailed fantasy outfit."

    if style == "8bit Style":
        base_prompt += " pixelated sprite art, 8-bit game style"
    elif style == "Anime Style":
        base_prompt += " anime art style, cel-shaded, colorful background"

    response = openai.Image.create(model="dall-e-3", prompt=base_prompt, size="1024x1024")
    return response["data"][0]["url"]

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
    width, height = letter
    margin = 50
    y = height - margin
    max_width = width - 2 * margin

    def write_paragraph(text, line_height=14):
        nonlocal y
        wrapped = simpleSplit(text, 'Helvetica', 12, max_width)
        for line in wrapped:
            if y < margin:
                c.showPage()
                y = height - margin
            c.drawString(margin, y, line)
            y -= line_height
        y -= line_height // 2

    c.setFont("Helvetica", 12)
    write_paragraph(f"Character: {character['Name']} ({character['Gender']}, {character['Race']}, {character['Class']})")
    write_paragraph(f"Background: {character['Background']}")
    write_paragraph("History:")
    write_paragraph(character['History'])

    write_paragraph(f"NPC: {npc['name']} - {npc['role']}")
    write_paragraph("NPC Backstory:")
    write_paragraph(npc['backstory'])

    write_paragraph(f"Quest: {quest['title']}")
    write_paragraph("Quest Description:")
    write_paragraph(quest['description'])

    c.save()
    buffer.seek(0)
    return buffer

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

auto_generate_class_and_background = st.checkbox("Automatically generate class and background?", value=True)
if auto_generate_class_and_background:
    character_class = random.choice(classes)
    background = random.choice(backgrounds)
    st.write(f"Class: {character_class} | Background: {background}")
else:
    character_class = st.selectbox("Select class:", classes)
    background = st.selectbox("Select background:", backgrounds)

selected_style = st.selectbox("Select Art Style for Image:", image_styles)

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
        char = generate_character(name, selected_gender, selected_race, character_class, background)
        char["History"] = generate_character_history(char, generate_history)
        char["Image"] = generate_character_image(char, selected_style)
        npc = generate_npc(generate_npc_text)
        quest = generate_quest(generate_quest_text)

        st.session_state.characters.append({"character": char, "npc": npc, "quest": quest})
        st.success("Character Created!")

# Tabs for output
if st.session_state.characters:
    for i, data in enumerate(st.session_state.characters):
        char = data["character"]
        npc = data["npc"]
        quest = data["quest"]

        with st.expander(f"Character #{i+1}: {char['Name']}"):
            tabs = st.tabs(["Character", "NPC", "Quest", "Music"])

            with tabs[0]:
                st.image(char["Image"], caption="Character Portrait")
                st.markdown(f"**{char['Name']}** | {char['Race']} {char['Class']} | Background: {char['Background']}")
                edited_history = st.text_area("Edit History", char["History"], key=f"history_{i}")
                char["History"] = edited_history

                if generate_turnaround:
                    st.image(generate_character_image(char, selected_style), caption="Turnaround Image")
                if generate_location:
                    st.image(generate_character_image(char, selected_style), caption="Place of Origin")
                if generate_extra:
                    st.image(generate_character_image(char, selected_style), caption="Extra Image 1")
                    st.image(generate_character_image(char, selected_style), caption="Extra Image 2")

            with tabs[1]:
                st.write(npc)

            with tabs[2]:
                edited_quest = st.text_area("Edit Quest Description", quest["description"], key=f"quest_{i}")
                quest["description"] = edited_quest
                st.markdown(f"### {quest['title']}")
                st.write(edited_quest)

            with tabs[3]:
                if generate_music:
                    prompt = f"Fantasy orchestral theme for a {char['Race']} {char['Class']} named {char['Name']} from a {char['Background']} background."
                    song_path = generate_theme_song(prompt)
                    if song_path and os.path.exists(song_path):
                        with open(song_path, "rb") as audio_file:
                            st.audio(audio_file.read(), format="audio/wav")
                    else:
                        st.warning("Failed to generate theme song. Check Audiocraft installation.")

            if st.button(f"📄 Download PDF #{i+1}"):
                pdf = create_pdf(char, npc, quest)
                st.download_button("Download PDF", pdf, file_name=f"{char['Name']}_profile.pdf", mime="application/pdf")

            if st.button(f"💾 Save Data as JSON #{i+1}"):
                save_to_json(char, npc, quest, file_name=f"{char['Name']}_data.json")
                st.success("Data saved to JSON.")
