Mana Forge Character Generator
Overview
Mana Forge Character Generator is a creative tool built with Streamlit that assists game designers, developers, and writers in generating rich character profiles. It leverages AI models such as OpenAI's GPT-4, DALL·E 3, and Audiocraft's MusicGen to create text, images, and music for game characters. Outputs can be exported as PDF or JSON files.

✨ Features
🔧 Character Generation
Custom Character Name: Enter a name or generate one.

Traits:

Race selection (Human, Elf, Dwarf, etc.)

Gender options (Male, Female, Non-binary)

Class & Background:

Auto-generate or select manually

🎨 AI Content Generation
Backstory: Generate a character history using GPT-4

NPC: Create a random NPC with name and profession

Quest: Generate a fantasy quest with title and description

Character Portrait: Generate an image using DALL·E 3

360° Turnaround: Create multiple images of the character from various angles

Place of Origin: Generate an environment image based on the character's background

Extra Images: Alternate poses or outfits

Theme Song: Compose a fantasy-themed orchestral piece using MusicGen

💾 Export Options
Download PDF: Export all character data in a styled PDF

Save as JSON: Save all structured data for future use

🧪 Usage
Input Fields
Character Name

Race (dropdown)

Gender (dropdown)

Checkboxes for Options
Auto-generate class & background

Generate:

Theme song

360° turnaround

Place of origin

Extra images

Character history

NPC

Quest

Action Buttons
Generate Character: Triggers all selected content generation

Download PDF: Saves all data into a PDF

Save as JSON: Exports structured data for reuse

🔁 Workflow
Character Setup:

Input name, select race/gender

Choose auto or manual class/background

Optional Content:

Check boxes for extra assets (history, music, NPCs, etc.)

Generate Content:

Click "Generate Character" to create content using AI models

Export:

Download PDF or save JSON for reuse in other projects

🧩 Code Structure
Function	Purpose
generate_character()	Builds base character dictionary
generate_character_history()	Creates backstory via GPT-4
generate_character_image()	Uses DALL·E 3 for portraits
generate_npc()	Generates random NPC profile
generate_quest()	Produces a fantasy-themed quest
generate_theme_song()	Creates a fantasy music theme
create_pdf()	Compiles and exports a PDF
save_to_json()	Saves data as structured JSON

🧪 Example Output
After configuration and clicking Generate Character, the tool outputs:

Character name, race, gender, class, background

Character portrait

Character backstory

NPC details

A fantasy quest

Theme song (optional)

PDF and JSON download options
