import streamlit as st
import sqlite3
from itertools import permutations
import random
import pandas as pd
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

# Sidebar navigation with Dashboard as the default
st.sidebar.title("PES 2025 Ramadhan League")
page = st.sidebar.radio("Go to", ["Dashboard", "Player Registration", "Match Schedule", "League Classification"])

# Page 1: Dashboard (New Main Page)
if page == "Dashboard":
    st.title("📊 League Dashboard")
    
    # Load players
    c.execute("SELECT name FROM players")
    players = [row[0] for row in c.fetchall()]

    if not players:
        st.warning("⚠️ No players registered yet. Go to Player Registration to start.")
    else:
        standings = {p: {"Points": 0, "GD": 0, "Matches Played": 0, "Wins": 0, "Draws": 0, "Losses": 0, "Goals For": 0, "Goals Against": 0} for p in players}
        c.execute("SELECT home_player, away_player, home_goals, away_goals FROM matches WHERE home_goals IS NOT NULL")
        for home, away, home_goals, away_goals in c.fetchall():
            standings[home]["Matches Played"] += 1
            standings[away]["Matches Played"] += 1
            standings[home]["Goals For"] += home_goals
            standings[away]["Goals For"] += away_goals
            standings[home]["Goals Against"] += away_goals
            standings[away]["Goals Against"] += home_goals
            standings[home]["GD"] += home_goals - away_goals
            standings[away]["GD"] += away_goals - home_goals
            if home_goals > away_goals:
                standings[home]["Points"] += 3
                standings[home]["Wins"] += 1
                standings[away]["Losses"] += 1
            elif home_goals < away_goals:
                standings[away]["Points"] += 3
                standings[away]["Wins"] += 1
                standings[home]["Losses"] += 1
            else:
                standings[home]["Points"] += 1
                standings[away]["Points"] += 1
                standings[home]["Draws"] += 1
                standings[away]["Draws"] += 1

        # Sort leaderboard
        leaderboard = sorted(standings.items(), key=lambda x: (-x[1]["Points"], -x[1]["GD"]))
        def calculate_match_odds(position, total_players=10):
            # Odds range from 1.2 (top) to 3.5 (bottom)
            odds = 1.2 + (position - 1) * (2.3 / (total_players - 1))  # Linear scaling
            return f"{odds:.1f} $"
        # --- Current Standings Section ---
        st.header("🏅 Current Standings", divider="blue")
        if leaderboard:
            # Create top 5 cards
            cols = st.columns(5)
            podium_emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            
            for idx in range(5):
                if idx < len(leaderboard):
                    player, stats = leaderboard[idx]
                    with cols[idx]:
                        st.markdown(f"""
                            <div style="background-color: black; 
                                        padding: 1rem; 
                                        border-radius: 10px; 
                                        border: 1px solid white;
                                        text-align: center;
                                        margin-bottom: 1rem;">
                                <div style="font-size: 1.5rem;">{podium_emojis[idx]}</div>
                                <h3 style="margin: 0.5rem 0; color: white;">{player}</h3>
                                <div style="color: #4b8bff; font-size: 1.2rem; font-weight: bold;">
                                    {stats['Points']} pts
                                </div>
                                <div style="color: white;">
                                    GD: {stats['GD']:+} • W: {stats['Wins']}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
            st.caption("Top 5 players based on current standings")
        else:
            st.info("⏳ No matches played yet. Standings will appear here after first matches.")

        # --- Upcoming Matches Section ---
        st.header("⏩ Upcoming Matches", divider="orange")
        c.execute("SELECT home_player, away_player, round, time FROM matches WHERE home_goals IS NULL AND away_goals IS NULL LIMIT 5")
        upcoming_matches = c.fetchall()
        
        if upcoming_matches:
            for home, away, round_num, time in upcoming_matches:
                # Calculate odds with color coding
                leaderboard_data = [
            {"Position": idx + 1, "Player": p, "Points": s["Points"], "Goal Difference": s["GD"]}
            for idx, (p, s) in enumerate(leaderboard)
        ]
                def get_odds_badge(odds):
                    color = "#2ecc71" if float(odds[:-2]) < 2.0 else "#e74c3c"
                    return f'<span style="background-color: {color}; color: white; padding: 0.2rem 0.5rem; border-radius: 15px;">{odds}</span>'
                player_positions = {entry["Player"]: entry["Position"] for entry in leaderboard_data}
                home_odds = calculate_match_odds(player_positions.get(home, 10))
                away_odds = calculate_match_odds(player_positions.get(away, 10))
                
                st.markdown(f"""
                    <div style="background-color: black; 
                                padding: 1rem; 
                                border-radius: 10px; 
                                border: 1px solid #dee2e6;
                                margin: 0.5rem 0;">
                        <div style="display: flex; justify-content: space-between; color: white; align-items: center;">
                            <div style="flex: 1; text-align: center;">
                                <div style="font-weight: bold; font-size: 1.1rem;">{home}</div>
                                {get_odds_badge(home_odds)}
                            </div>
                            <div style="flex: 0.5; text-align: center; color: white;">
                                ⚔<br>
                                <large>{round_num}</large><br>
                                <large>{time}</large>
                            </div>
                            <div style="flex: 1; text-align: center;">
                                <div style="font-weight: bold; font-size: 1.1rem;">{away}</div>
                                {get_odds_badge(away_odds)}
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("🎉 All matches completed! Schedule new matches in the Schedule section.")

        # --- Recent Results Section ---
        st.header("📅 Recent Results", divider="green")
        c.execute("SELECT home_player, away_player, home_goals, away_goals, round FROM matches WHERE home_goals IS NOT NULL ORDER BY id DESC LIMIT 5")
        recent_matches = c.fetchall()
        
        if recent_matches:
            for home, away, hg, ag, round_num in recent_matches:
                result_color = "#2ecc71" if hg > ag else ("#e74c3c" if hg < ag else "#f1c40f")
                st.markdown(f"""
                    <div style="background-color: black; 
                                padding: 1rem; 
                                border-radius: 10px; 
                                border: 1px solid #dee2e6;
                                margin: 0.5rem 0;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="flex: 1; text-align: right; font-weight: bold;">{home}</div>
                            <div style="flex: 0.5; text-align: center; 
                                      font-size: 1.2rem; color: {result_color}; 
                                      font-weight: bold;">
                                {hg} - {ag}
                            </div>
                            <div style="flex: 1; text-align: left; font-weight: bold;">{away}</div>
                        </div>
                        <div style="text-align: center; color: white; margin-top: 0.5rem;">
                            {round_num}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("📭 No recent results to display")

        # --- League Statistics Section ---
        st.header("📈 League Statistics", divider="red")
        col1, col2, col3 = st.columns(3)
        # League Statistics
        st.subheader("League Statistics")
        c.execute("SELECT SUM(home_goals) + SUM(away_goals) FROM matches")
        total_goals = c.fetchone()[0] or 0
        c.execute("SELECT home_player, SUM(home_goals) FROM matches GROUP BY home_player ORDER BY SUM(home_goals) DESC LIMIT 1")
        top_scorer = c.fetchone()
        top_scorer_name = top_scorer[0] if top_scorer else "N/A"
        top_scorer_goals = top_scorer[1] if top_scorer else 0
        st.write(f"**Total Goals Scored:** {total_goals}")
        st.write(f"**Top Scorer:** {top_scorer_name} with {top_scorer_goals} goals")
        with col1:
            st.markdown(f"""
                <div style="background-color: #4b8bff; 
                            padding: 1.5rem; 
                            border-radius: 10px; 
                            color: white;
                            text-align: center;">
                    <div style="font-size: 2rem;">⚽</div>
                    <h3 style="margin: 0.5rem 0;">Total Goals</h3>
                    <div style="font-size: 1.5rem; font-weight: bold;">{total_goals}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div style="background-color: #2ecc71; 
                            padding: 1.5rem; 
                            border-radius: 10px; 
                            color: white;
                            text-align: center;">
                    <div style="font-size: 2rem;">👑</div>
                    <h3 style="margin: 0.5rem 0;">Top Scorer</h3>
                    <div style="font-size: 1.1rem;">{top_scorer_name}</div>
                    <div style="font-size: 1.3rem; font-weight: bold;">{top_scorer_goals} goals</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            total_matches = sum(1 for _ in c.execute("SELECT id FROM matches"))
            completed_matches = sum(1 for _ in c.execute("SELECT id FROM matches WHERE home_goals IS NOT NULL"))
            progress = completed_matches / total_matches if total_matches > 0 else 0
            
            st.markdown(f"""
                <div style="background-color: #f1c40f; 
                            padding: 1.5rem; 
                            border-radius: 10px; 
                            color: white;
                            text-align: center;">
                    <div style="font-size: 2rem;">📅</div>
                    <h3 style="margin: 0.5rem 0;">League Progress</h3>
                    <div style="font-size: 1.3rem; font-weight: bold;">
                        {int(progress*100)}% Complete
                    </div>
                    <div style="color: rgba(255,255,255,0.8);">
                        {completed_matches}/{total_matches} matches
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Custom CSS
        st.markdown("""
            <style>
                [data-testid="stHeader"] {
                    margin-bottom: -5rem;
                }
                .st-emotion-cache-1y4p8pa {
                    padding-top: 2rem;
                }
                div[data-testid="column"] {
                    padding: 0.5rem;
                }
            </style>
        """, unsafe_allow_html=True)

# Page 2: Player Registration
elif page == "Player Registration":
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

# Page 3: Match Schedule
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

elif page == "League Classification":
    st.title("🏆 League Classification")
    
    # Check if matches exist
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
            st.header("📥 Input Match Results")
            selected_round = st.selectbox("Select Round to Input Scores", pending_rounds)
            
            # Load pending matches for the selected round
            c.execute("""SELECT home_player, away_player 
                       FROM matches 
                       WHERE round = ? AND home_goals IS NULL AND away_goals IS NULL""", 
                       (selected_round,))
            pending_matches = [(row[0], row[1]) for row in c.fetchall()]
            
            if pending_matches:
                st.subheader(f"Round {selected_round} Matches")
                for home, away in pending_matches:
                    # Create a styled container for each match
                    st.markdown(f"""
                        <div style="background-color: #f8f9fa; 
                                    padding: 1.2rem; 
                                    border-radius: 10px; 
                                    margin: 1rem 0; 
                                    border: 1px solid #dee2e6;">
                            <div style="font-size: 1.1rem; 
                                      font-weight: 500; 
                                      margin-bottom: 1rem; 
                                      color: #2c3e50;">
                                ⚽ {home} vs {away}
                            </div>
                    """, unsafe_allow_html=True)
                    
                    cols = st.columns([2, 1, 2])
                    with cols[0]:
                        st.markdown(f"**{home}** (Home)")
                    with cols[1]:
                        st.markdown("<div style='text-align: center; font-weight: bold;'>vs</div>", 
                                  unsafe_allow_html=True)
                    with cols[2]:
                        st.markdown(f"**{away}** (Away)")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        home_goals = st.number_input(
                            f"Goals for {home}", 
                            min_value=0, 
                            step=1, 
                            key=f"{home}_{away}_home"
                        )
                    with col2:
                        away_goals = st.number_input(
                            f"Goals for {away}", 
                            min_value=0, 
                            step=1, 
                            key=f"{home}_{away}_away"
                        )
                    
                    if st.button("Submit Score", key=f"submit_{home}_{away}"):
                        c.execute(
                            """UPDATE matches 
                            SET home_goals = ?, away_goals = ? 
                            WHERE home_player = ? AND away_player = ? AND round = ?""",
                            (home_goals, away_goals, home, away, selected_round)
                        )
                        conn.commit()
                        st.success(f"✅ Result recorded: {home} {home_goals} - {away_goals} {away}")
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info(f"All matches in Round {selected_round} have been completed!")
        else:
            st.success("🎉 All rounds have been completed!")

        # Enhanced standings calculation
        st.header("📊 Current Standings")
        standings = {p: {"Points": 0, "GD": 0, "Matches Played": 0, 
                       "Wins": 0, "Draws": 0, "Losses": 0, 
                       "Goals For": 0, "Goals Against": 0} for p in players}
        
        c.execute("SELECT home_player, away_player, home_goals, away_goals FROM matches WHERE home_goals IS NOT NULL")
        for home, away, home_goals, away_goals in c.fetchall():
            # Update standings logic remains the same
            # ... (same as original code)
            standings[home]["Matches Played"] += 1
            standings[away]["Matches Played"] += 1
            standings[home]["Goals For"] += home_goals
            standings[away]["Goals For"] += away_goals
            standings[home]["Goals Against"] += away_goals
            standings[away]["Goals Against"] += home_goals
            standings[home]["GD"] += home_goals - away_goals
            standings[away]["GD"] += away_goals - home_goals
            if home_goals > away_goals:
                standings[home]["Points"] += 3
                standings[home]["Wins"] += 1
                standings[away]["Losses"] += 1
            elif home_goals < away_goals:
                standings[away]["Points"] += 3
                standings[away]["Wins"] += 1
                standings[home]["Losses"] += 1
            else:
                standings[home]["Points"] += 1
                standings[away]["Points"] += 1
                standings[home]["Draws"] += 1
                standings[away]["Draws"] += 1

        # Sort and display enhanced leaderboard
        leaderboard = sorted(standings.items(), key=lambda x: (-x[1]["Points"], -x[1]["GD"]))
        
        # Create styled DataFrame
        leaderboard_data = []
        for idx, (p, s) in enumerate(leaderboard):
            emoji = ""
            if idx == 0:
                emoji = "🥇"
            elif idx == 1:
                emoji = "🥈"
            elif idx == 2:
                emoji = "🥉"
                
            leaderboard_data.append({
                "Position": f"{idx+1}{emoji}",
                "Player": p,
                "Pts": s["Points"],
                "GD": s["GD"],
                "MP": s["Matches Played"],
                "W": s["Wins"],
                "D": s["Draws"],
                "L": s["Losses"],
                "GF": s["Goals For"],
                "GA": s["Goals Against"]
            })

        # Create and style DataFrame
        df = pd.DataFrame(leaderboard_data)
        df = df[["Position", "Player", "Pts", "GD", "MP", "W", "D", "L", "GF", "GA"]]
        
        # Apply styling
        styled_df = df.style \
            .hide(axis='index') \
            .format({
                "GD": "{:+}",
                "Pts": "{:d}",
                "MP": "{:d}",
                "W": "{:d}",
                "D": "{:d}",
                "L": "{:d}",
                "GF": "{:d}",
                "GA": "{:d}"
            }) \
            .background_gradient(subset=["Pts"], cmap="YlGn") \
            .background_gradient(subset=["GD"], cmap="RdYlGn") \
            .set_properties(**{'font-weight': '500'}, subset=["Player"]) \
            .set_properties(**{'text-align': 'center'}, subset=["Pts", "GD", "MP", "W", "D", "L", "GF", "GA"]) \
            .set_table_styles([{
                'selector': 'th',
                'props': [('background-color', '#4b8bff'), 
                         ('color', 'white'),
                         ('font-weight', 'bold')]
            }])

        # Display styled DataFrame
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=(len(leaderboard_data) + 1) * 35 + 3,
            column_config={
                "Position": "Position",
                "Player": "Player",
                "Pts": "Points",
                "GD": "Goal Diff",
                "MP": "Matches",
                "W": "Wins",
                "D": "Draws",
                "L": "Losses",
                "GF": "Goals For",
                "GA": "Goals Against"
            },
            hide_index=True
        )

        # Add custom styling
        st.markdown("""
            <style>
                [data-testid="stDataFrame"] {
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                [data-testid="stDataFrame"] table {
                    width: 100%;
                }
                [data-testid="stDataFrame"] th {
                    border-bottom: 2px solid #dee2e6 !important;
                }
            </style>
        """, unsafe_allow_html=True)

# Page 5: Betting Odds (New Page)
