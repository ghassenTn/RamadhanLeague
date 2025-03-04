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
        st.header("🏆 Premier League Standings", divider="rainbow")
        if leaderboard:
            # Create top 5 cards
            cols = st.columns(4)
            podium_emojis = ["👑", "🥈", "🥉", "4️⃣"]
            
            for idx in range(4):
                if idx < len(leaderboard):
                    player, stats = leaderboard[idx]
                    with cols[idx]:
                        # Different card colors for top 3
                        card_color = "#37003C"  # Premier League purple
                        if idx == 0:
                            card_color = "linear-gradient(45deg, #37003C 0%, #E90052 100%)"
                        elif idx == 1:
                            card_color = "#1D428A"  # Secondary blue
                        elif idx == 2:
                            card_color = "#00A551"  # Premier League green

                        st.markdown(f"""
                            <div style="background: {card_color};
                                        padding: 1.5rem;
                                        border-radius: 15px;
                                        border: 1px solid #00FF87;
                                        text-align: center;
                                        margin-bottom: 1rem;
                                        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                                        transition: transform 0.2s;
                                        min-height: 220px;
                                        display: flex;
                                        flex-direction: column;
                                        justify-content: space-between;">
                                <div>
                                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">{podium_emojis[idx]}</div>
                                    <h3 style="margin: 0.5rem 0; 
                                            color: #00FF87; 
                                            font-family: 'Arial Black', sans-serif;
                                            text-shadow: 0 2px 4px rgba(0,0,0,0.5);">
                                        {player}
                                    </h3>
                                </div>
                                <div>
                                    <div style="background: linear-gradient(45deg, #FFD700, #FFFFFF);
                                                -webkit-background-clip: text;
                                                color: transparent;
                                                font-size: 1.8rem;
                                                font-weight: bold;
                                                margin: 0.5rem 0;">
                                        {stats['Points']} pts
                                    </div>
                                    <div style="color: #FFFFFF;
                                            font-size: 0.9rem;
                                            border-top: 1px solid #00FF87;
                                            padding-top: 0.5rem;
                                            margin: 0 1rem;">
                                        <div>🏃 GD: {stats['GD']:+}</div>
                                        <div>✅ W: {stats['Wins']}</div>
                                    </div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
            
            st.caption("""
                <div style="color: #00FF87; font-size: 0.9rem; margin-top: -1rem;">
                    🔺 Ramadhan League ranking system | GD: Goal Difference | MP: Matches Played
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("""
                ⚽ No matches played yet. 
                Standings will appear here after the first fixtures.
            """)

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
                        <div style="display: flex; justify-content: space-between;color:white; align-items: center;">
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
            # Use a round-robin algorithm to create a double round robin schedule
            n = len(players)
            # If odd number of players, add a dummy "Bye" team (these matches will be skipped)
            if n % 2 == 1:
                players.append("Bye")
                n += 1
            
            fixed = players[0]
            rotating = players[1:]
            rounds = []
            # First half rounds: generate n-1 rounds
            for r in range(n - 1):
                teams_order = [fixed] + rotating
                round_matches = []
                for i in range(n // 2):
                    home = teams_order[i]
                    away = teams_order[-(i+1)]
                    # Exclude matches involving "Bye"
                    if home != "Bye" and away != "Bye":
                        round_matches.append((home, away, f"Round {r+1}", "20:00", None, None))
                rounds.append(round_matches)
                # Rotate the teams (keep the first team fixed)
                rotating = [rotating[-1]] + rotating[:-1]
            
            # Second half: mirror the matches (swap home and away) and assign subsequent round numbers
            rounds2 = []
            for r, round_matches in enumerate(rounds):
                mirrored = []
                for match in round_matches:
                    home, away, _, time, _, _ = match
                    mirrored.append((away, home, f"Round {r + n}", time, None, None))
                rounds2.append(mirrored)
            
            full_rounds = rounds + rounds2
            # Insert all rounds into the database
            for round_matches in full_rounds:
                c.executemany(
                    "INSERT INTO matches (home_player, away_player, round, time, home_goals, away_goals) VALUES (?, ?, ?, ?, ?, ?)",
                    round_matches
                )
            conn.commit()

        # Load and display schedule
        c.execute("SELECT home_player, away_player, round, time, home_goals, away_goals FROM matches")
        schedule = [
            {
                "Match": f"{row[0]} vs {row[1]}", 
                "Round": row[2], 
                "Time": row[3], 
                "Result": (row[4], row[5]) if row[4] is not None else None
            } 
            for row in c.fetchall()
        ]
        
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
            c.execute(
                "UPDATE matches SET time = ? WHERE home_player = ? AND away_player = ?",
                (new_time, home, away)
            )
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
                        if st.session_state.get("password_verified", False):
                            c.execute(
                                """UPDATE matches 
                                SET home_goals = ?, away_goals = ? 
                                WHERE home_player = ? AND away_player = ? AND round = ?""",
                                (home_goals, away_goals, home, away, selected_round)
                            )
                            conn.commit()
                            st.success(f"✅ Result recorded: {home} {home_goals} - {away_goals} {away}")
                            st.rerun()
                        else:
                            st.session_state.pending_submission = {
                                "home": home,
                                "away": away,
                                "round": selected_round,
                                "home_goals": home_goals,
                                "away_goals": away_goals
                            }
                            st.session_state.show_password = True
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Password verification section
                if st.session_state.get("show_password", False):
                    password = st.text_input("Enter Admin Password", type="password", key="admin_pwd")
                    if password:
                        if password == "admin":
                            st.session_state.password_verified = True
                            st.session_state.show_password = False
                            submission = st.session_state.pending_submission
                            c.execute(
                                """UPDATE matches 
                                SET home_goals = ?, away_goals = ? 
                                WHERE home_player = ? AND away_player = ? AND round = ?""",
                                (submission["home_goals"], submission["away_goals"], 
                                 submission["home"], submission["away"], submission["round"])
                            )
                            conn.commit()
                            st.success(f"✅ Result recorded: {submission['home']} {submission['home_goals']} - {submission['away_goals']} {submission['away']}")
                            del st.session_state.pending_submission
                            st.rerun()
                        else:
                            st.error("Incorrect password. Please try again.")
                            if "pending_submission" in st.session_state:
                                del st.session_state.pending_submission
                            st.session_state.show_password = False
                            st.rerun()
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

        # Define functions for conditional formatting
        def highlight_top_bottom(row):
            """Highlight top and bottom positions with green and red colors."""
            position = int(row["Position"].replace("🥇", "").replace("🥈", "").replace("🥉", ""))
            styles = ["background-color: transparent"] * len(row)
            
            # Highlight top 4 positions (e.g., Champions League spots)
            if position <= 4:
                styles = ["background-color: #e8f5e9"] * len(row)  # Light green
                
            # Highlight bottom 3 positions (e.g., relegation zone)
            elif position >= len(leaderboard_data) - 2:
                styles = ["background-color: #ffebee"] * len(row)  # Light red
                
            return styles

        # Apply Premier League-inspired styling
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
            .apply(highlight_top_bottom, axis=1) \
            .applymap(lambda x: 'font-weight: bold;', subset=["Player"]) \
            .apply(lambda x: ['background-color: #f8f9fa' if i%2==0 else 'background-color: white' for i in range(len(x))]) \
            .set_properties(**{
                'text-align': 'center',
                'font-size': '14px',
                'border': '1px solid #dee2e6'
            }, subset=["Pts", "GD", "MP", "W", "D", "L", "GF", "GA"]) \
            .set_properties(**{
                'text-align': 'left',
                'padding-left': '12px'
            }, subset=["Player"]) \
            .set_table_styles([{
                'selector': 'th',
                'props': [
                    ('background-color', '#37003c'),  # Premier League purple
                    ('color', 'white'),
                    ('font-weight', 'bold'),
                    ('font-size', '15px'),
                    ('text-align', 'center'),
                    ('border', '0px solid #dee2e6')
                ]
            }, {
                'selector': 'td',
                'props': [
                    ('border', '1px solid #dee2e6'),
                    ('padding', '8px')
                ]
            }, {
                'selector': 'tr:hover',
                'props': [
                    ('background-color', '#f1f3f5')
                ]
            }])
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=(len(leaderboard_data) + 1) * 38 + 3,
            column_config={
                "Position": st.column_config.TextColumn("Pos", width="small"),
                "Player": st.column_config.TextColumn("Player", width="large"),
                "Pts": st.column_config.NumberColumn("Pts", width="small"),
                "GD": st.column_config.NumberColumn("GD", width="small"),
                "MP": st.column_config.NumberColumn("MP", width="small"),
                "W": st.column_config.NumberColumn("W", width="small"),
                "D": st.column_config.NumberColumn("D", width="small"),
                "L": st.column_config.NumberColumn("L", width="small"),
                "GF": st.column_config.NumberColumn("GF", width="small"),
                "GA": st.column_config.NumberColumn("GA", width="small")
            },
            hide_index=True
        )
        st.markdown("""
            <style>
                [data-testid="stDataFrame"] {
                    border: 0px solid #37003c;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                [data-testid="stDataFrame"] table {
                    width: 100%;
                    border-collapse: collapse;
                }
                [data-testid="stDataFrame"] th {
                    border-bottom: 2px solid #dee2e6 !important;
                }
                [data-testid="stDataFrame"] tr:first-child td {
                    background-color: #e8d4ff !important;
                    font-weight: bold !important;
                }
                [data-testid="stDataFrame"] tr:nth-child(2) td {
                    background-color: #f3e9ff !important;
                }
                [data-testid="stDataFrame"] tr:nth-child(3) td {
                    background-color: #f8f2ff !important;
                }
                [data-testid="stDataFrame"] tr td {
                    transition: background-color 0.2s ease;
                }
            </style>
        """, unsafe_allow_html=True)

# Page 5: Betting Odds (New Page)
