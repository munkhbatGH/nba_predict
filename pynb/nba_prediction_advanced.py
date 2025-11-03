import os
import pickle
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.static import teams
import shap

CACHE_FILE = "cached_games.pkl"
MODEL_FILE = "nba_win_model.pkl"

# ----------------------------
# 1. Бэртлийн мэдээлэл татах
# ----------------------------
def fetch_injury_reports():
    """Scrape current ESPN NBA injury list."""
    url = "https://www.espn.com/nba/injuries"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    injuries = []
    for team_section in soup.select(".ResponsiveTable"):
        team_name = team_section.find("span", class_="flex items-center").text.strip()
        players = [p.text for p in team_section.select("tbody tr td:nth-child(1) a")]
        injuries.append({"team": team_name, "injured_players": players})

    return pd.DataFrame(injuries)


def compute_team_injury_count(inj_df, team_name):
    """Count injured players for given team name"""
    row = inj_df[inj_df["team"].str.contains(team_name, case=False, na=False)]
    if row.empty:
        return 0
    return len(row.iloc[0]["injured_players"])


# ----------------------------
# 2. NBA тоглолтын өгөгдөл татах
# ----------------------------
def load_or_fetch_games():
    if os.path.exists(CACHE_FILE):
        print("✅ Cached data found — loading from file...")
        return pd.read_pickle(CACHE_FILE)

    print("⏳ Fetching NBA games from API...")
    nba_teams = teams.get_teams()
    all_games = pd.DataFrame()

    for team in nba_teams:
        team_id = team["id"]
        gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id)
        games = gamefinder.get_data_frames()[0]
        all_games = pd.concat([all_games, games], ignore_index=True)

    pd.to_pickle(all_games, CACHE_FILE)
    print("✅ Data cached for future runs.")
    return all_games


# ----------------------------
# 3. Өгөгдөл боловсруулах
# ----------------------------
def preprocess_data(all_games):
    nba_teams = teams.get_teams()
    abbr_to_id = {t["abbreviation"]: t["id"] for t in nba_teams}

    all_games["GAME_DATE"] = pd.to_datetime(all_games["GAME_DATE"])
    all_games["WIN"] = all_games["WL"].apply(lambda x: 1 if x == "W" else 0)
    all_games["PTS"] = all_games["PTS"].astype(float)
    all_games["Points_Per_Game"] = all_games.groupby("TEAM_ID")["PTS"].transform("mean")

    def get_opponent_id(matchup):
        if not isinstance(matchup, str):
            return None
        if "@" in matchup:
            opp = matchup.split(" @ ")[-1]
        elif "vs." in matchup:
            opp = matchup.split(" vs. ")[-1]
        else:
            return None
        return abbr_to_id.get(opp.strip())

    all_games["OPPONENT_TEAM_ID"] = all_games["MATCHUP"].apply(get_opponent_id)
    all_games["HOME_GAME"] = all_games["MATCHUP"].apply(lambda x: 1 if "vs." in str(x) else 0)
    all_games["LAST_GAME_RESULT"] = all_games.groupby("TEAM_ID")["WIN"].shift(1).fillna(0)

    le = LabelEncoder()
    all_games["TEAM_ID_enc"] = le.fit_transform(all_games["TEAM_ID"].fillna(-1))
    all_games["OPPONENT_TEAM_ID_enc"] = le.fit_transform(all_games["OPPONENT_TEAM_ID"].fillna(-1))

    return all_games, le


# ----------------------------
# 4. Head-to-head статистик
# ----------------------------
def head_to_head_stats(all_games, team_id, opp_id):
    subset = all_games[(all_games["TEAM_ID"] == team_id) & (all_games["OPPONENT_TEAM_ID"] == opp_id)]
    total = len(subset)
    wins = subset["WIN"].sum()
    return wins / total if total > 0 else 0


# ----------------------------
# 5. Моделийг сургах + Hyperparameter tuning
# ----------------------------
def train_or_load_model(X, y):
    if os.path.exists(MODEL_FILE):
        print("✅ Loading pre-trained model...")
        with open(MODEL_FILE, "rb") as f:
            return pickle.load(f)

    print("⏳ Training model with GridSearchCV...")
    param_grid = {
        "n_estimators": [100, 200, 300],
        "max_depth": [5, 10, 20, None],
        "min_samples_split": [2, 5, 10]
    }

    rf = RandomForestClassifier(random_state=42)
    grid = GridSearchCV(rf, param_grid, cv=3, scoring="accuracy", n_jobs=-1, verbose=1)
    grid.fit(X, y)

    print("✅ Best parameters:", grid.best_params_)
    print("✅ Best score:", grid.best_score_)

    best_model = grid.best_estimator_
    with open(MODEL_FILE, "wb") as f:
        pickle.dump(best_model, f)
    return best_model


# ----------------------------
# 6. Таамаг гаргах
# ----------------------------
def predict_game(team_abbr, opponent_abbr, avg_pts, is_home, last_win):
    all_games = load_or_fetch_games()
    all_games, le = preprocess_data(all_games)

    nba_teams = teams.get_teams()
    abbr_to_id = {t["abbreviation"]: t["id"] for t in nba_teams}

    # Бэртэлтэй тоглогчдын тоо
    injuries = fetch_injury_reports()
    team_injury = compute_team_injury_count(injuries, team_abbr)
    opp_injury = compute_team_injury_count(injuries, opponent_abbr)

    # Head-to-head win rate
    win_rate = head_to_head_stats(all_games, abbr_to_id[team_abbr], abbr_to_id[opponent_abbr])

    # Training set
    X = all_games[["TEAM_ID_enc", "OPPONENT_TEAM_ID_enc", "Points_Per_Game", "HOME_GAME", "LAST_GAME_RESULT"]]
    y = all_games["WIN"]

    model = train_or_load_model(X, y)

    new_data = pd.DataFrame({
        "TEAM_ID_enc": [le.transform([abbr_to_id[team_abbr]])[0]],
        "OPPONENT_TEAM_ID_enc": [le.transform([abbr_to_id[opponent_abbr]])[0]],
        "Points_Per_Game": [avg_pts],
        "HOME_GAME": [1 if is_home else 0],
        "LAST_GAME_RESULT": [last_win],
    })

    pred = model.predict(new_data)[0]
    prob = model.predict_proba(new_data)[0]

    print(f"🏀 {team_abbr} vs {opponent_abbr}")
    print(f"🩹 {team_abbr} injuries: {team_injury}, {opponent_abbr} injuries: {opp_injury}")
    print(f"📊 Head-to-head win rate ({team_abbr}): {win_rate:.2f}")
    print(f"🔮 Predicted: {'WIN' if pred == 1 else 'LOSS'} ({prob[pred]*100:.1f}%)")

    return {"prediction": "WIN" if pred == 1 else "LOSS", "probability": prob[pred], "injuries": (team_injury, opp_injury)}


# ----------------------------
# Run example
# ----------------------------
if __name__ == "__main__":
    result = predict_game("BKN", "SAS", avg_pts=110.5, is_home=True, last_win=1)
    print(result)
