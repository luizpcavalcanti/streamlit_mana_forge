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
if "parties" not in st.session_state:
    st.session_state.parties = []
if "stories" not in st.session_state:
    st.session_state.stories = []
if "worlds" not in st.session_state:
    st.session_state.worlds = []
if "journals" not in st.session_state:
    st.session_state.journals = []
    
# Character traits
races = ["Human", "Elf", "Dwarf", "Halfling", "Gnome", "Half-Orc", "Tiefling", "Dragonborn", "Kobold", "Lizardfolk", "Minotaur", "Troll", "Vampire", "Satyr", "Undead", "Lich", "Werewolf"]
classes = ["Fighter", "Wizard", "Rogue", "Cleric", "Barbarian", "Sorcerer", "Bard", "Monk", "Druid", "Ranger", "Paladin", "Warlock", "Artificer", "Blood Hunter", "Mystic", "Warden", "Berserker", "Necromancer", "Trickster", "Beast Master", "Alchemist", "Pyromancer", "Dark Knight"]
backgrounds = ["Acolyte", "Folk Hero", "Sage", "Criminal", "Noble", "Hermit", "Outlander", "Entertainer", "Artisan", "Sailor", "Soldier", "Charlatan", "Knight", "Pirate", "Spy", "Archaeologist", "Gladiator", "Inheritor", "Haunted One", "Bounty Hunter", "Explorer", "Watcher", "Traveler", "Phantom", "Vigilante"]
genders = ["Male", "Female", "Non-binary"]
image_styles = ["Standard", "8bit Style", "Anime Style"]

# Generation functions
def generate_character(name, gender, race, character_class, background):
    return {"Name": name, "Gender": gender, "Race": race, "Class": character_class, "Background": background}

def generate_character_history(character, generate_history=True):
    if generate_history:
        prompt = f"Create a short backstory for a {character['Race']} {character['Class']} named {character['Name']}. They come from a {character['Background']} background. Include motivations and key events and locations, don't use existing names from reality"
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are a creative storyteller, written in the style of George RR Martin, but not named as his characters."}, {"role": "user", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"]
    return ""

# World Builder Functions

def generate_npc_names(count=10):
    prompt = f"Generate {count} unique fantasy NPC names along with their roles and a brief background for each. Include some variety, like merchants, warriors, scholars, and mystics."
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    lines = response["choices"][0]["message"]["content"].strip().split("\n")
    npcs = []
    for line in lines:
        if ": " in line:
            name, details = line.split(": ", 1)
            role, background = details.split(". ", 1)
            npcs.append({"name": name.strip(), "role": role.strip(), "backstory": background.strip()})
    return npcs

def generate_location_names(count=10):
    prompt = f"Generate {count} unique fantasy location names with a short description for each. Include different types of places like towns, ancient ruins, mystical forests, and mountain strongholds."
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    lines = response["choices"][0]["message"]["content"].strip().split("\n")
    locations = []
    for line in lines:
        if ": " in line:
            name, description = line.split(": ", 1)
            locations.append({"name": name.strip(), "description": description.strip()})
    return locations


def initialize_world(world_name):
    world = {"name": world_name, "regions": {}}
    for i in range(5):
        for j in range(5):
            world["regions"][f"{i+1}-{j+1}"] = {"name": f"Location {i+1}-{j+1}", "characters": [], "npcs": [], "quests": [], "capital": False, "special_traits": []}
    st.session_state.worlds.append(world)
    return world

def add_to_region(world_name, region_key, entry_type, entry):
    for world in st.session_state.worlds:
        if world["name"] == world_name:
            world["regions"][region_key][entry_type].append(entry)


def save_journal(world_name, journal_text):
    filename = f"journal_{world_name}.txt"
    with open(filename, "w", encoding="utf-8") as file:
        file.write(journal_text)

def load_journal(world_name):
    filename = f"journal_{world_name}.txt"
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            return file.read()
    return ""

def generate_world_journal(world):
    journal_entries = []
    for region_key, region in world["regions"].items():
        entry = f"**{region['name']}**\n"
        
        # Include capital city info
        if region["capital"]:
            entry += "Capital Region\n"
        
        # Add special traits or lore to the region
        if region["special_traits"]:
            entry += "Special Traits:\n" + "\n".join([f"- {trait}" for trait in region["special_traits"]]) + "\n"
        
        # Add characters info
        if region["characters"]:
            entry += "Characters:\n" + "\n".join([f"- {c['Name']} ({c['Race']} {c['Class']}) - Last Seen: {c.get('last_action', 'Unknown')}" for c in region["characters"]]) + "\n"
        
        # Add NPC info
        if region["npcs"]:
            entry += "NPCs:\n" + "\n".join([f"- {npc['name']} ({npc['role']}) - Last Seen: {npc.get('last_action', 'Unknown')}" for npc in region["npcs"]]) + "\n"
        
        # Add quests info
        if region["quests"]:
            entry += "Quests:\n" + "\n".join([f"- {quest['title']} - Last Update: {quest.get('last_action', 'Unknown')}" for quest in region["quests"]]) + "\n"
        
        # Use AI to generate regional content based on stories, characters, and quests
        if region["characters"] or region["quests"]:
            prompt = f"Generate a fantasy description of the region '{region['name']}' using the following elements:\n"
            prompt += "Characters:\n" + "\n".join([f"- {c['Name']} ({c['Race']} {c['Class']})" for c in region["characters"]]) + "\n" if region["characters"] else ""
            prompt += "NPCs:\n" + "\n".join([f"- {npc['name']} ({npc['role']})" for npc in region["npcs"]]) + "\n" if region["npcs"] else ""
            prompt += "Quests:\n" + "\n".join([f"- {quest['title']}: {quest['description']}" for quest in region["quests"]]) + "\n" if region["quests"] else ""
            prompt += f"Generate a rich, detailed story or lore for this region based on these elements, adding mystery, drama, or historical context.\n"
            
            # Get a response from the AI to enrich the region with lore and details
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "You are a fantasy world-building assistant."},
                          {"role": "user", "content": prompt}]
            )
            entry += f"Lore/Story:\n{response['choices'][0]['message']['content']}\n"
        
        journal_entries.append(entry)
    
    return "\n\n".join(journal_entries)


def generate_story(character, npc, quest):
    prompt = (
        f"Write a short D&D style story paragraph involving the following quest, party, and NPC:\n"
        f"Character: {character['Name']} ({character['Race']} {character['Class']}, {character['Background']})\n"
        f"NPC: {npc['name']} - {npc['role']}, {npc['backstory']}\n"
        f"Make it immersive and written like George RR Martin recounting an adventure."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a fantasy storyteller."}, {"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

def generate_character_image(character, style="Standard"):
    base_prompt = f"A full-body portrait of a {character['Gender']} {character['Race']} {character['Class']} with {character['Background']} vibes, heroic pose, detailed fantasy outfit."
    if style == "8bit Style": base_prompt += " pixelated sprite art, 8-bit game style"
    if style == "Anime Style": base_prompt += " anime art style, cel-shaded, colorful background"
    response = openai.Image.create(model="dall-e-3", prompt=base_prompt, size="1024x1024")
    return response["data"][0]["url"]

def generate_npc(generate_npc_text=True):
    if generate_npc_text:
        prompt = "Generate a unique fantasy NPC name and their profession."
        response = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        content = response["choices"][0]["message"]["content"].strip()
        if ", " in content:
            name, role = content.split(", ", 1)
        else:
            name, role = content, random.choice(["merchant", "guard", "wizard", "priest"])
        backstory = f"{name} is a {role} with a mysterious past."
    else:
        name, role, backstory = "Unknown", "Unknown", "No backstory provided."
    return {"name": name, "role": role, "backstory": backstory}


def generate_quest(generate_quest_text=True):
    if generate_quest_text:
        prompt = "Create a fantasy quest with a title and short description."
        response = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        parts = response["choices"][0]["message"]["content"].strip().split("\n", 1)
        title = parts[0]
        description = parts[1] if len(parts) > 1 else "A mysterious quest awaits."
    else:
        title, description = "Untitled Quest", "No description provided."
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
        if stringWidth(test_line, "Helvetica", 7) > max_width:
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
    x, y = 50, 750
    line_height = 12; max_width = 500
    def section(title, content):
        nonlocal y
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, title)
        y -= line_height
        c.setFont("Helvetica", 8)
        y = draw_wrapped_text(c, content, x, y, max_width, line_height)
        y -= line_height
    section("Character Info", f"{character['Name']} ({character['Gender']}, {character['Race']}, {character['Class']})")
    section("Background", character['Background'])
    section("History", character.get('History', ''))
    section("NPC", f"{npc['name']} - {npc['role']}")
    section("NPC Backstory", npc['backstory'])
    section("Quest", quest['title'])
    section("Quest Description", quest['description'])
    for url in images:
        img = download_image(url)
        if img:
            if y - 270 < 0: c.showPage(); y = 750
            c.drawImage(img, x, y - 400, width=400, height=400, preserveAspectRatio=True)
            y -= 420
    c.showPage(); c.save(); buffer.seek(0)
    return buffer

def save_to_json(character, npc, quest, file_name="character_data.json"):
    with open(file_name, 'w') as f:
        json.dump({"character": character, "npc": npc, "quest": quest}, f, indent=4)
        
# --- MAIN UI ---
st.title("🎭 Mana Forge Character Generator & Toolkit", anchor="title")
mode = st.sidebar.radio("Select Mode:", ["Character", "World Builder"])


# Character mode
if mode == "Character":
    name = st.text_input("Enter character name:")
    selected_race = st.selectbox("Select race:", races)
    selected_gender = st.selectbox("Select gender:", genders)
    auto_generate = st.checkbox("Auto-generate class & background?", value=True)

    selected_style = st.selectbox("Select Art Style:", image_styles)
    generate_music = st.checkbox("Generate Theme Song (Audiocraft)")
    generate_turnaround = st.checkbox("Generate 360° Turnaround")
    generate_location = st.checkbox("Generate Place of Origin")
    generate_extra = st.checkbox("Generate Extra Images")
    generate_history = st.checkbox("Generate Character History")
    generate_npc_text = st.checkbox("Generate NPC Text")
    generate_quest_text = st.checkbox("Generate Quest Text")

    if not auto_generate:
        character_class = st.selectbox("Select class:", classes)
        background = st.selectbox("Select background:", backgrounds)

    if st.button("Generate Character"):
        if not name.strip():
            st.warning("Please enter a name.")
        else:
            # Handle auto-generation inside the button press
            if auto_generate:
                character_class = random.choice(classes)
                background = random.choice(backgrounds)

            char = generate_character(name, selected_gender, selected_race, character_class, background)
            char["History"] = generate_character_history(char, generate_history)
            image_urls = [generate_character_image(char, selected_style)]
            if generate_turnaround: image_urls.append(generate_character_image(char, selected_style))
            if generate_location: image_urls.append(generate_character_image(char, selected_style))
            if generate_extra:
                image_urls.append(generate_character_image(char, selected_style))
                image_urls.append(generate_character_image(char, selected_style))
            npc = generate_npc(generate_npc_text)
            quest = generate_quest(generate_quest_text)
            st.session_state.characters.append({"character": char, "npc": npc, "quest": quest, "images": image_urls})
            st.success(f"Character '{char['Name']}' Created!")

    for i, data in enumerate(st.session_state.characters):
        ch, npc, quest, imgs = data['character'], data['npc'], data['quest'], data['images']
        tabs = st.tabs(["Info", "History", "NPC", "Quests", "Images", "Export"])
        with tabs[0]:
            st.write(f"**{ch['Name']}** — {ch['Gender']}, {ch['Race']} {ch['Class']} ({ch['Background']})")
        with tabs[1]:
            st.write(ch.get('History', 'No history generated'))
        with tabs[2]:
            st.write(f"**{npc['name']}** ({npc['role']})")
            st.write(npc['backstory'])
        with tabs[3]:
            st.write(f"**{quest['title']}**")
            st.write(quest['description'])
        with tabs[4]:
            for url in imgs:
                st.image(url, use_container_width=True)
        with tabs[5]:
            st.download_button("Download JSON", data=json.dumps({"character": ch, "npc": npc, "quest": quest}), file_name=f"{ch['Name']}.json")
            pdf_buf = create_pdf(ch, npc, quest, imgs)
            st.download_button("Download PDF", data=pdf_buf, file_name=f"{ch['Name']}.pdf", mime="application/pdf")

# --- WORLD BUILDER ---
if mode == "World Builder":
    tab1, tab2, tab3 = st.tabs(["Party / Infinite Story Mode", "Journal", "Regions"])

    # --- PARTY / INFINITE STORY TAB ---
    with tab1:
        st.header("🧑‍🤝‍🧑 Party / Infinite Story Mode")
        if not st.session_state.characters:
            st.warning("Create at least 1 character to form a party.")
        else:
            options = [f"{i+1}. {d['character']['Name']}" for i, d in enumerate(st.session_state.characters)]
            selected = st.multiselect("Select party members:", options)

            if st.button("Generate / Continue Party Story") and selected:
                idxs = [options.index(s) for s in selected]
                members = [st.session_state.characters[i] for i in idxs]
                names = ", ".join([m['character']['Name'] for m in members])

                # Check if party exists
                existing_party = None
                for party in st.session_state.parties:
                    party_names = [m['character']['Name'] for m in party['members']]
                    if set(names.split(", ")) == set(party_names):
                        existing_party = party
                        break

                # Prepare prompt with existing story
                existing_story = existing_party['story'] if existing_party else ""
                prompt = f"Continue the story for party members: {names}.\n\n{existing_story}"

                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}]
                )
                story_text = response['choices'][0]['message']['content']

                # Update or create party
                if existing_party:
                    existing_party['story'] += "\n\n" + story_text
                else:
                    st.session_state.parties.append({"members": members, "story": story_text})

                st.success("Story generated and appended!")

            # Display all party stories
            for idx, party in enumerate(st.session_state.parties):
                exp = st.expander(f"Party {idx+1}: {', '.join([m['character']['Name'] for m in party['members']])}", expanded=True)
                with exp:
                    st.text_area("Story", value=party['story'], height=200)

    # --- JOURNAL TAB ---
    with tab2:
        st.header("📓 World Journal")

        # Build journal dynamically
        journal_entries = []

        # Characters
        if st.session_state.characters:
            journal_entries.append("**Characters:**")
            for ch in st.session_state.characters:
                c = ch['character']
                journal_entries.append(f"- {c['Name']} ({c['Race']} {c['Class']}) Background: {c['Background']}")

        # Party Stories
        if st.session_state.parties:
            journal_entries.append("\n**Party Stories:**")
            for idx, party in enumerate(st.session_state.parties):
                journal_entries.append(f"\nParty {idx+1}: {', '.join([m['character']['Name'] for m in party['members']])}")
                journal_entries.append(party['story'])

        # Store journal in session state
        st.session_state.journal_text = "\n".join(journal_entries)
        journal_text = st.text_area("World Journal", value=st.session_state.journal_text, height=400)

        # Save / Export
        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("Save Journal"):
                save_journal("world", journal_text)
                st.session_state.journal_text = journal_text
                st.success("Journal saved!")
        with col2:
            st.download_button("Download Journal (TXT)", data=journal_text, file_name="world_journal.txt", mime="text/plain")
  # --- REGIONS TAB ---
    with tab3:
        st.header("🌍 AI-Generated Regions")
        if "regions" not in st.session_state:
            st.session_state.regions = []
    
        def extract_json_from_text(text):
            import re
            try:
                match = re.search(r'\{.*\}', text, flags=re.DOTALL)
                if match:
                    return json.loads(match.group())
            except json.JSONDecodeError:
                pass
            return None
    
        if st.button("Create New Region from Journal"):
            journal_text = st.session_state.journal_text
            all_npcs = [ch['npc'] for ch in st.session_state.characters]
            all_quests = [ch['quest'] for ch in st.session_state.characters]
            party_stories = "\n\n".join([p['story'] for p in st.session_state.parties])
    
            prompt = (
                f"Using the following world journal, NPCs, quests, and party stories, generate a unique fantasy region. "
                f"Return a JSON object with 'name' and 'description'. The 'description' itself should be a JSON object "
                f"with keys: 'terrain', 'climate', 'special_features', 'quests', 'npcs'. ONLY RETURN JSON.\n\n"
                f"World Journal:\n{journal_text}\n\n"
                f"NPCs:\n{json.dumps(all_npcs, indent=2)}\n\n"
                f"Quests:\n{json.dumps(all_quests, indent=2)}\n\n"
                f"Party Stories:\n{party_stories}"
            )
    
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            content = response['choices'][0]['message']['content'].strip()
    
            # Extract JSON safely
            region_data = extract_json_from_text(content)
            if region_data:
                region_name = region_data.get("name", "Unknown Region")
                region_description = region_data.get("description", {})
            else:
                region_name = "Unknown Region"
                region_description = content
    
            st.session_state.regions.append({"name": region_name, "description": region_description})
            st.success(f"Region '{region_name}' created!")
    
        # Display all regions
        for idx, region in enumerate(st.session_state.regions):
            exp_name = region.get("name", f"Region {idx+1}")
            exp = st.expander(exp_name, expanded=False)
            with exp:
                desc = region.get("description", {})
                if isinstance(desc, dict):
                    st.markdown(f"**Terrain:** {desc.get('terrain','N/A')}")
                    st.markdown(f"**Climate:** {desc.get('climate','N/A')}")
                    
                    if 'special_features' in desc:
                        st.markdown("**Special Features:**")
                        for sf in desc['special_features']:
                            if isinstance(sf, dict):
                                st.markdown(f"- **{sf.get('name','')}**: {sf.get('description','')}")
                            else:
                                st.markdown(f"- {sf}")
                                
                    if 'quests' in desc:
                        st.markdown("**Quests:**")
                        for q in desc['quests']:
                            if isinstance(q, dict):
                                st.markdown(f"- **{q.get('title','')}**: {q.get('description','')}")
                            else:
                                st.markdown(f"- {q}")
                                
                    if 'npcs' in desc:
                        st.markdown("**NPCs:**")
                        for npc in desc['npcs']:
                            if isinstance(npc, dict):
                                st.markdown(f"- **{npc.get('name','')}** ({npc.get('role','')}): {npc.get('description','')}")
                            else:
                                st.markdown(f"- {npc}")
                else:
                    st.write(desc)
