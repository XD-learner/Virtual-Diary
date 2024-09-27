import streamlit as st
import json
from datetime import datetime
from openai import OpenAI
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])

def get_start_and_end_of_week():
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday
    return start_of_week, end_of_week
def analyserr(entry):
    prompt = (
        "You are an empathetic assistant. "
        "Analyze the following journal entry, focusing on mood, stress level, emotional tone, and coping strategies. "
        "You will be given a journal entry. Below is the JSON format you must follow. Do not mention JSON.\n"
        "Example Response format: {"
        "\"mood\": \"\", "
        "\"stress_level\": 0, "
        "\"emotional_tone\": \"\", "
        "\"feedback\": \"\", "
        "\"coping_strategies\": [] "
        "}"
    )

    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': entry}
        ],
        temperature=1.3
    )

    response_content = response.choices[0].message.content.strip()
    print(response.usage)

    if not response_content:
        raise ValueError("Empty response from the API.")

    try:
        parsed_analysis = json.loads(response_content)
        return parsed_analysis
    except json.JSONDecodeError:
        raise ValueError("Failed to parse the analysis response as JSON.")

DATA_FILE = "journal_entries.json"
def load_entries():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as file:
            content = file.read()
            if content:
                try:
                    
                    return json.loads(content)
                except json.JSONDecodeError:
                    st.error("Error reading the journal entries. The file may be corrupted.")
                    return []
    return []

def save_entries(new_entry):
    existing_entries = load_entries()
    existing_entries.append(new_entry)
    with open(DATA_FILE, 'w') as file:
        json.dump(existing_entries, file, indent=4)

st.title("Virtual Diary with Mood Tracking")
today = datetime.now().strftime("%Y-%m-%d")
selected_date = st.date_input("Select a date", value=datetime.now())
selected_date_str = selected_date.strftime("%Y-%m-%d")
journal_entry = st.text_area("Reflect on your day:", value="")

if st.button("Analyze"):
    existing_entries = load_entries()
    entries_list = [entries for entries in load_entries()]
    if journal_entry:
        try:
            analysis = analyserr(journal_entry)
            mood = analysis.get("mood", "unknown")
            feedback = analysis.get("feedback", "No feedback provided.")
            stress_level = analysis.get("stress_level", 0)
            emotional_tone = analysis.get("emotional_tone", "unknown")
            coping_strategies = analysis.get("coping_strategies", [])

            entry = {
                "date": selected_date_str,
                "content": journal_entry,
                "mood": mood,
                "stress_level": stress_level,
                "emotional_tone": emotional_tone,
                "analysis": feedback,
                "coping_strategies": coping_strategies
            }

            save_entries(entry)

            st.write("Analysis:")
            st.write(feedback)
            st.write(f"Mood detected: {mood}")
            st.write(f"Stress level detected: {stress_level}")
            st.write(f"Emotional tone detected: {emotional_tone}")
            if coping_strategies:
                st.write("Coping Strategies:")
                for strategy in coping_strategies:
                    st.write(f"- {strategy}")
        except ValueError as e:
            st.error(str(e))
    else:
        st.error("Please enter a journal entry before analyzing.")

if st.button("View Past Entries"):
    existing_entries = load_entries()
    entries_list = [entries for entries in load_entries()]
    if existing_entries:
        st.write("### Your Journal Entries:")
        for entry in entries_list:
            st.markdown(f"#### Date: {entry['date']}")
            st.write(f"**Content:** {entry.get('content', 'No content provided.')}")
            st.write(f"**Mood:** {entry.get('mood', 'N/A')}")
            st.write(f"**Analysis:** {entry.get('analysis', 'No analysis provided.')}")
            st.write(f"**Stress Level:** {entry.get('stress_level', 'N/A')}")
            st.write(f"**Emotional Tone:** {entry.get('emotional_tone', 'N/A')}")
            st.write("**Coping Strategies:**")
            coping_strategies = entry.get('coping_strategies', [])
            if coping_strategies:
                for strategy in coping_strategies:
                    st.write(f"- {strategy}")
            else:
                st.write("- No coping strategies provided.")
    else:
        st.write("No entries found.")



if st.button("Show Mood Trends"):
    existing_entries = load_entries()
    
    if existing_entries:
        df = pd.DataFrame(existing_entries)
        df['date'] = pd.to_datetime(df['date'])

        mood_counts = df['mood'].value_counts()

        plt.figure(figsize=(8, 6))
        plt.pie(mood_counts, labels=mood_counts.index, autopct='%1.1f%%', startangle=140)
        plt.title('Mood Distribution')
        plt.axis('equal')

        st.write("Mood Distribution")
        st.pyplot(plt)
    else:
        st.write("No entries found for mood tracking.")
if st.button("Show Stress Level Trends for This Week"):
    existing_entries = load_entries()
    
    if existing_entries:
        df = pd.DataFrame(existing_entries)
        df['date'] = pd.to_datetime(df['date'])

        # Get the start and end date of the current week
        start_date, end_date = get_start_and_end_of_week()

        # Filter the DataFrame for this week
        filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

        if not filtered_df.empty:
            # Group by date and calculate average stress level
            stress_trends = filtered_df.groupby('date')['stress_level'].mean()

            # Create the plot
            plt.figure(figsize=(10, 6))
            plt.plot(stress_trends.index, stress_trends.values, marker='o', linestyle='-', color='blue')
            plt.title('Average Stress Level Over Time This Week')
            plt.xlabel('Date')
            plt.ylabel('Average Stress Level')

            # Set x-ticks to show only the dates of the current week
            plt.xticks(stress_trends.index, rotation=45)
            plt.xlim([start_date, end_date])

            # Format the x-axis to only show the year
            plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))

            # Remove other years from the x-axis by limiting ticks to this year's dates
            current_year = datetime.now().year
            plt.gca().set_xticks([date for date in stress_trends.index if date.year == current_year])

            st.write("Average Stress Level Trends for This Week")
            st.pyplot(plt)
        else:
            st.write("No stress entries found for this week.")
    else:
        st.write("No entries found for mood tracking.")


