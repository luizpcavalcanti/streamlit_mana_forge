import random
import streamlit as st
import json
import openai
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit, ImageReader
import base64
import requests

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
            messages=[{"role": "system", "content": "You are a creative storyteller."}, {"role": "user", "content": prompt}]
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

def download_image(image_url):
    try:
        response = requests.get(image_url)
        return ImageReader(BytesIO(response.content))
    except:
        return None

def draw_wrapped_text(canvas, text, x, y, max_width, line_height):
    from reportlab.pdfbase.pdfmetrics import stringWidth
    words = text.split()
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        if stringWidth(test_line, "Helvetica", 10) > max_width:
            canvas.drawString(x, y, line)
            y -= line_height
            line = word
        else:
            line = test_line
    if line:
        canvas.drawString(x, y, line)
        y -= line_height
    return y

def create_pdf(character, npc, quest, images):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    x, y = 50, 750  # Starting position for text
    line_height = 14
    max_width = 500
    page_height = letter[1]

    def section(title, content):
        nonlocal y
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y, title)
        y -= line_height
        c.setFont("Helvetica", 10)
        # Draw text, wrapping it to the specified width
        y = draw_wrapped_text(c, content, x, y, max_width, line_height)
        y -= line_height  # Extra spacing after each section

    def check_page_space(required_space):
        # Check if there's enough space for the content
        if y - required_space < 0:
            c.showPage()  # Start a new page
            return 750  # Reset y for a new page
        return y

    # Add sections
    section("Character Info", f"{character['Name']} ({character['Gender']}, {character['Race']}, {character['Class']})")
    section("Background", character['Background'])
    section("History", character.get("History", ""))
    section("NPC", f"{npc['name']} - {npc['role']}")
    section("NPC Backstory", npc['backstory'])
    section("Quest", f"{quest['title']}")
    section("Quest Description", quest['description'])

    # Add images, checking for space before placing each
    for idx, url in enumerate(images):
        img = download_image(url)
        if img:
            required_space = 270  # Space needed for image placement
            y = check_page_space(required_space)

            # Draw image with the larger size
            c.drawImage(img, x, y - 250, width=400, height=400, preserveAspectRatio=True)
            y -= 420  # Adjust the y position after the image

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

    section("Character Info", f"{character['Name']} ({character['Gender']}, {character['Race']}, {character['Class']})")
    section("Background", character['Background'])
    section("History", character.get("History", ""))
    section("NPC", f"{npc['name']} - {npc['role']}")
    section("NPC Backstory", npc['backstory'])
    section("Quest", f"{quest['title']}")
    section("Quest Description", quest['description'])

    for idx, url in enumerate(images):
        img = download_image(url)
        if img:
            if y < 300:
                c.showPage()
                y = 750
            c.drawImage(img, x, y - 250, width=200, height=200, preserveAspectRatio=True)
            y -= 270

    c.showPage()
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

# --- Streamlit UI ---
st.title("🎭 Mana Forge Character Generator")

name = st.text_input("Enter character name:")
selected_race = st.selectbox("Select race:", races)
selected_gender = st.selectbox("Select gender:", genders)

auto_generate_class_and_background = st.checkbox("Auto-generate class & background?", value=True)
if auto_generate_class_and_background:
    character_class = random.choice(classes)
    background = random.choice(backgrounds)
    st.write(f"Class: {character_class} | Background: {background}")
else:
    character_class = st.selectbox("Select class:", classes)
    background = st.selectbox("Select background:", backgrounds)

selected_style = st.selectbox("Select Art Style:", image_styles)

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
        image_urls = [generate_character_image(char, selected_style)]
        if generate_turnaround:
            image_urls.append(generate_character_image(char, selected_style))
        if generate_location:
            image_urls.append(generate_character_image(char, selected_style))
        if generate_extra:
            image_urls.append(generate_character_image(char, selected_style))
            image_urls.append(generate_character_image(char, selected_style))
        char["Image"] = image_urls[0]  # For main display
        npc = generate_npc(generate_npc_text)
        quest = generate_quest(generate_quest_text)

        st.session_state.characters.append({
            "character": char,
            "npc": npc,
            "quest": quest,
            "images": image_urls
        })
        st.success("Character Created!")

# --- Display Tabs ---
for i, data in enumerate(st.session_state.characters):
    char = data["character"]
    npc = data["npc"]
    quest = data["quest"]
    images = data["images"]

    st.subheader(f"Character {i+1} - {char['Name']}")
    st.write(f"**Race**: {char['Race']} | **Class**: {char['Class']} | **Gender**: {char['Gender']} | **Background**: {char['Background']}")
    st.write(f"**History**: {char.get('History', 'No history generated')}")
    st.write(f"**NPC**: {npc['name']} - {npc['role']}")
    st.write(f"**NPC Backstory**: {npc['backstory']}")
    st.write(f"**Quest**: {quest['title']}")
    st.write(f"**Quest Description**: {quest['description']}")

    # Show Image
    for img_url in images:
        st.image(img_url, use_container_width=True)

    # Export Options
    with open(f"{char['Name']}_character_data.json", "w") as f:
        json.dump({"character": char, "npc": npc, "quest": quest}, f, indent=4)

    pdf_buffer = create_pdf(char, npc, quest, images)
    st.download_button(
        label="Download Character PDF",
        data=pdf_buffer,
        file_name=f"{char['Name']}_Character.pdf",
        mime="application/pdf"
    )
