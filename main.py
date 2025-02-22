import streamlit as st
import sqlite3
from itertools import permutations
import random

# Database setup
conn = sqlite3.connect('pes_league.db', check_same_thread=False)
c = conn.cursor()

# Create tables if they don't exist
c.execute('''CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)''')

c.execute('''CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    home_player TEXT,
    away_player TEXT,
    round TEXT,
    time TEXT,
    home_goals INTEGER,
    away_goals INTEGER,
    FOREIGN KEY (home_player) REFERENCES players (name),
    FOREIGN KEY (away_player) REFERENCES players (name)
)''')
conn.commit()

# Initialize session state
if 'confirmed' not in st.session_state:
    st.session_state.confirmed = False

# Sidebar navigation
st.sidebar.title("PES 2025 Ramadhan League")
page = st.sidebar.radio("Go to", ["Player Registration", "Match Schedule", "League Classification"])

# Page 1: Player Registration
if page == "Player Registration":
    st.title("Player Registration")

    # Load existing players from DB
    c.execute("SELECT name FROM players")
    players = [row[0] for row in c.fetchall()]
    
    new_player = st.text_input("Enter player name")
    if st.button("Add Player") and new_player:
        if new_player not in players and len(players) < 10:
            c.execute("INSERT OR IGNORE INTO players (name) VALUES (?)", (new_player,))
            conn.commit()
            st.success(f"Added {new_player}")
        elif new_player in players:
            st.warning("Player name must be unique!")
        else:
            st.warning("Only 10 players allowed!")

    # Display and remove players
    if players:
        st.write("Current Players:")
        for i, player in enumerate(players):
            col1, col2 = st.columns([3, 1])
            col1.write(player)
            if col2.button("Remove", key=f"remove_{i}"):
                c.execute("DELETE FROM players WHERE name = ?", (player,))
                c.execute("DELETE FROM matches WHERE home_player = ? OR away_player = ?", (player, player))
                conn.commit()
                st.rerun()

    # Confirm players
    if len(players) == 10:
        if st.button("Confirm Players"):
            st.session_state.confirmed = True
            st.success("Players confirmed! Move to Match Schedule.")
    else:
        st.warning(f"Need exactly 10 players (currently {len(players)}).")

# Page 2: Match Schedule
elif page == "Match Schedule":
    st.title("Match Schedule")
    if not st.session_state.confirmed:
        st.warning("Please register and confirm players first!")
    else:
        # Load players
        c.execute("SELECT name FROM players")
        players = [row[0] for row in c.fetchall()]
        
        # Generate schedule if not already in DB
        c.execute("SELECT COUNT(*) FROM matches")
        if c.fetchone()[0] == 0:
            matches = list(permutations(players, 2))  # 90 matches
            random.shuffle(matches)

            # Organize into 18 rounds (5 matches per round)
            match_idx = 0
            for round_num in range(1, 19):
                round_matches = []
                used_players = set()
                temp_matches = matches[match_idx:]
                attempts = 0
                while len(round_matches) < 5 and temp_matches and attempts < 100:
                    home, away = temp_matches.pop(0)
                    if home not in used_players and away not in used_players:
                        round_matches.append((home, away, f"Round {round_num}", "20:00", None, None))
                        used_players.add(home)
                        used_players.add(away)
                        match_idx += 1
                    attempts += 1
                if len(round_matches) == 5:
                    c.executemany(
                        "INSERT INTO matches (home_player, away_player, round, time, home_goals, away_goals) VALUES (?, ?, ?, ?, ?, ?)",
                        round_matches
                    )
            conn.commit()

        # Load and display schedule
        c.execute("SELECT home_player, away_player, round, time, home_goals, away_goals FROM matches")
        schedule = [{"Match": f"{row[0]} vs {row[1]}", "Round": row[2], "Time": row[3], "Result": (row[4], row[5]) if row[4] is not None else None} for row in c.fetchall()]
        
        filtered_schedule = schedule
        filter_player = st.selectbox("Filter by Player", ["All"] + players)
        filter_round = st.selectbox("Filter by Round", ["All"] + sorted(set([m["Round"] for m in schedule])))
        
        if filter_player != "All":
            filtered_schedule = [m for m in filtered_schedule if filter_player in m["Match"]]
        if filter_round != "All":
            filtered_schedule = [m for m in filtered_schedule if m["Round"] == filter_round]
        st.table(filtered_schedule)

        # Edit match time
        match_to_edit = st.selectbox("Edit a match", [m["Match"] for m in schedule])
        new_time = st.text_input("New Time (e.g., 20:00)", "20:00")
        if st.button("Update Time"):
            home, away = match_to_edit.split(" vs ")
            c.execute("UPDATE matches SET time = ? WHERE home_player = ? AND away_player = ?", (new_time, home, away))
            conn.commit()
            st.success(f"Updated time for {match_to_edit}")
            st.rerun()

# Page 3: League Classification
elif page == "League Classification":
    st.title("League Classification")
    c.execute("SELECT COUNT(*) FROM matches")
    if c.fetchone()[0] == 0:
        st.warning("Please generate the schedule first!")
    else:
        # Load players
        c.execute("SELECT name FROM players")
        players = [row[0] for row in c.fetchall()]
        
        # Get rounds with pending matches
        c.execute("SELECT DISTINCT round FROM matches WHERE home_goals IS NULL AND away_goals IS NULL")
        pending_rounds = [row[0] for row in c.fetchall()]
        
        if pending_rounds:
            selected_round = st.selectbox("Select Round to Input Scores", pending_rounds)
            
            # Load pending matches for the selected round
            c.execute("SELECT home_player, away_player FROM matches WHERE round = ? AND home_goals IS NULL AND away_goals IS NULL", (selected_round,))
            pending_matches = [(row[0], row[1]) for row in c.fetchall()]
            
            if pending_matches:
                st.write(f"Enter scores for {selected_round}:")
                for home, away in pending_matches:
                    st.subheader(f"{home} vs {away}")
                    col1, col2 = st.columns(2)
                    home_goals = col1.number_input(f"Goals for {home} (Home)", min_value=0, step=1, key=f"{home}_{away}_home")
                    away_goals = col2.number_input(f"Goals for {away} (Away)", min_value=0, step=1, key=f"{home}_{away}_away")
                    if st.button("Submit", key=f"submit_{home}_{away}"):
                        c.execute(
                            "UPDATE matches SET home_goals = ?, away_goals = ? WHERE home_player = ? AND away_player = ? AND round = ?",
                            (home_goals, away_goals, home, away, selected_round)
                        )
                        conn.commit()
                        st.success(f"Result recorded: {home} {home_goals} - {away_goals} {away}")
                        st.rerun()
            else:
                st.write("All matches in this round have scores.")
        else:
            st.success("All rounds have been completed!")

        # Calculate standings
        standings = {p: {"Points": 0, "GD": 0, "Matches": []} for p in players}
        c.execute("SELECT home_player, away_player, home_goals, away_goals FROM matches WHERE home_goals IS NOT NULL")
        for home, away, home_goals, away_goals in c.fetchall():
            standings[home]["GD"] += home_goals - away_goals
            standings[away]["GD"] += away_goals - home_goals
            standings[home]["Matches"].append((away, home_goals, away_goals))
            standings[away]["Matches"].append((home, away_goals, home_goals))
            if home_goals > away_goals:
                standings[home]["Points"] += 3
            elif home_goals < away_goals:
                standings[away]["Points"] += 3
            else:
                standings[home]["Points"] += 1
                standings[away]["Points"] += 1

        # Sort and display leaderboard
        leaderboard = sorted(standings.items(), key=lambda x: (x[1]["Points"], x[1]["GD"]), reverse=True)
        st.write("Leaderboard")
        leaderboard_data = [{"Player": p, "Points": s["Points"], "Goal Difference": s["GD"]} for p, s in leaderboard]
        st.table(leaderboard_data)
