Your issue is that Streamlit reruns the script from the top whenever a button is clicked, which resets all variables unless they're stored in `st.session_state`. You're already using `st.session_state` for some elements, but you need to ensure that your character, NPC, quest, and generated images persist properly.

### **Fix:**
1. Store all generated data (character, history, image, NPC, quest) in `st.session_state`.
2. Display stored session state data outside the button click event.

### **Updated Code Snippet:**
Modify your character generation button like this:

```python
# Generate character button
if st.button("Generate Character"):
    if not name.strip():  # Ensure a name is provided
        st.warning("Please enter a character name before generating.")
    else:
        # Store in session state
        st.session_state.character = generate_character(name, selected_gender, selected_race)
        st.session_state.character["History"] = generate_character_history(st.session_state.character)  
        st.session_state.character["Image"] = generate_character_image(st.session_state.character)  

        st.session_state.npc = generate_npc()  
        st.session_state.quest = generate_quest()  

        st.success("Character Created Successfully!")

# Ensure stored data persists even after button clicks
if st.session_state.character:
    st.write(f"**Name:** {st.session_state.character['Name']}")
    st.write(f"**Gender:** {st.session_state.character['Gender']}")
    st.write(f"**Race:** {st.session_state.character['Race']}")
    st.write(f"**Class:** {st.session_state.character['Class']}")
    st.write(f"**Background:** {st.session_state.character['Background']}")

    st.write("### Character History:")
    st.write(st.session_state.character["History"])

    st.write("### Character Portrait:")
    st.image(st.session_state.character["Image"], caption="Generated Character Portrait")

if st.session_state.npc:
    st.write("### NPC:")
    st.write(f"**Name:** {st.session_state.npc['name']}")
    st.write(f"**Role:** {st.session_state.npc['role']}")
    st.write(f"**Backstory:** {st.session_state.npc['backstory']}")

if st.session_state.quest:
    st.write("### Quest:")
    st.write(f"**Title:** {st.session_state.quest['title']}")
    st.write(f"**Description:** {st.session_state.quest['description']}")
```

### **Why This Works:**
- It ensures that `st.session_state` stores all generated content persistently.
- The character details, NPC, and quest persist even after interacting with buttons.
- The UI updates only when `Generate Character` is clicked but doesn’t reset when other buttons are clicked.

Try this out and let me know if you need further adjustments! 🚀
