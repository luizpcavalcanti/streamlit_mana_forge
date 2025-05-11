# Mana Forge Character Generator and Toolkit

## 🧙 Overview

**Mana Forge Character Generator** is a creative toolkit built with **Streamlit** for game designers, developers, and writers. It helps generate detailed character profiles, NPCs, quests, and entire fantasy worlds. Mana Forge uses AI models including **OpenAI's GPT-4**, **DALL·E 3**, and **Audiocraft's MusicGen** to generate text, visuals, and music. Outputs can be exported as styled **PDF** or structured **JSON**.

---

## ✨ Features

### 🔧 Character Generation
- **Custom Character Name**: Enter or generate a name
- **Traits**:
  - Race (Human, Elf, Dwarf, etc.)
  - Gender (Male, Female, Non-binary)
- **Class & Background**: Choose or auto-generate
- **Optional Elements**:
  - History (via GPT-4)
  - Character Portrait (via DALL·E 3)
  - 360° Turnaround
  - Environment Background (Place of origin)
  - Extra Poses or Outfits
  - Theme Song (via MusicGen)

---

### 👥 Party Mode
- Create and group multiple characters
- Combine individual character outputs into a single PDF or JSON
- Shared backstories or party-level narrative planned (WIP)

---

### 🧑‍🌾 NPC & Quest Generator
- **NPCs**:
  - Name, profession, personality/backstory
- **Quests**:
  - Fantasy quest title and description
  - Tied optionally to characters, regions, or NPCs

---

### 🌍 World Builder
- Grid-based world system (5x5 regions)
- Add characters, NPCs, quests to each region
- Regions can be flagged as capitals or have special traits
- Automatically generates a **world journal**
- Each world is named and saved independently

---

### 📖 Story Mode
- Merges a character, a quest, and an NPC into a short fantasy narrative
- GPT-written in a storytelling tone
- Optional export as text or PDF

---

### 💾 Export Options
- **Download PDF**: Clean visual layout of character + story content
- **Save as JSON**: All structured data for integration or reuse

---

## 🧪 Usage

### Input Fields
- Character Name
- Race (dropdown)
- Gender (dropdown)
- Art Style (Standard, 8bit, Anime)
- World + Region selector for world mode

### Checkboxes
- Auto-generate class & background
- Generate:
  - Theme song
  - 360° turnaround
  - Environment image
  - Extra images
  - Backstory
  - NPC
  - Quest

### Buttons
- `Generate Character`
- `Download PDF`
- `Save as JSON`

---

## 🔁 Workflow

1. **Character Setup**  
   Input name, select traits, choose generation settings

2. **Generate Content**  
   Click **Generate Character** to invoke AI services (GPT-4, DALL·E, MusicGen)

3. **Explore World or Party**  
   Assign character to a region or group into a party

4. **Export**  
   Use PDF or JSON export for sharing or use in projects

---

## 📦 Code Structure

| Function | Purpose |
|---------|---------|
| `generate_character()` | Builds character dictionary |
| `generate_character_history()` | GPT-4 backstory generation |
| `generate_character_image()` | DALL·E 3 portrait |
| `generate_npc()` | NPC name, job, backstory |
| `generate_quest()` | Fantasy-themed quest |
| `generate_theme_song()` | MusicGen fantasy theme |
| `initialize_world()` | Creates new 5x5 world |
| `assign_to_region()` | Places characters/NPCs in world grid |
| `generate_story()` | Combines character, quest, and NPC into narrative |
| `create_pdf()` | PDF export |
| `save_to_json()` | JSON export |

---

## 📌 Example Output

After running **Generate Character**, you'll receive:
- 🎭 Name, gender, race, class, background
- 🖼 Portrait (with optional angles and outfits)
- 📜 History and backstory
- 🧑‍🌾 NPC details
- 🧭 Quest description
- 🎶 Theme music (if enabled)
- 🗺 Region/world placement
- 📄 PDF and JSON downloads

---

## 🔮 Roadmap

- [ ] Drag-and-drop map editor for world builder
- [ ] Music playback and preview
- [ ] Tabletop system export templates (D&D 5e, Pathfinder, etc.)
- [ ] Shared party backstories and relationship mechanics
- [ ] AI-assisted world descriptions (climate, factions, etc.)

---

## 🛠 Built With

- [Streamlit](https://streamlit.io)
- [OpenAI GPT-4 + DALL·E 3](https://openai.com/)
- [Audiocraft MusicGen](https://github.com/facebookresearch/audiocraft)
- [ReportLab](https://www.reportlab.com/) – PDF generation

---

## 📃 License

MIT License – feel free to use, adapt, and contribute!

