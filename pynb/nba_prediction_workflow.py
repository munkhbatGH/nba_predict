# nba_prediction_workflow.py

import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.static import teams
import shap

# 1) Бэртэлтэй тоглогчдын мэдээлэл scrape хийх функц
def fetch_injury_reports(date_str):
    """
    Өгөгдсөн өдөр (YYYY-MM-DD) «injury report»–ийг авч DataFrame болгож буцаана.
    """
    url = f"https://www.nbainjuries.com/{date_str}"  # жишээ URL
    # note: өөр URL байж болно, энд асуудалтай байж болно
    try:
        from nbainjuries import injury
        df = injury.get_reportdata(pd.to_datetime(date_str), return_df=True)
        return df
    except ImportError:
        # fallback scraping
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        # энэ хэсэгт сайт-хамааралтай parsing хийх хэрэгтэй
        # жишээ:
        rows = soup.select("table tr")
        data = []
        for r in rows[1:]:
            cols = [c.text.strip() for c in r.find_all("td")]
            if len(cols) >= 6:
                data.append(cols)
        inj_df = pd.DataFrame(data, columns=["Game Date","Game Time","Matchup","Team","Player Name","Current Status","Reason"])
        return inj_df

def compute_team_injury_count(inj_df, team_abbr):
    """
    Өгөгдсөн багийн товчилсон нэр(team_abbr)-ийг тухайн өдөр хэдэн тоглогчийн бэртэлтэй байсаныг барина.
    """
    return inj_df[inj_df["Team"].str.contains(team_abbr, case=False)].shape[0]


# 2) Хоёр багийн харилцан тоглолтын статистик
def head_to_head_stats(all_games_df, team_abbr, opponent_abbr, abbr_to_id_map, teams_list):
    """
    all_games_df – бүх тоглолтын өгөгдөл.
    team_abbr, opponent_abbr – товчилсон нэрс.
    abbr_to_id_map – abbreviation → TEAM_ID map.
    teams_list – teams.get_teams() өгөгдөл.
    Буцаана: total_games, wins_by_team, win_rate_for_team.
    """
    team_id = abbr_to_id_map.get(team_abbr)
    opp_id  = abbr_to_id_map.get(opponent_abbr)
    subset = all_games_df[(all_games_df["TEAM_ID"] == team_id) & (all_games_df["OPPONENT_TEAM_ID"] == opp_id)]
    total = len(subset)
    wins  = subset["WIN"].sum()
    rate  = wins / total if total>0 else 0
    return {"total_games": total, "wins": wins, "win_rate": rate}


# 3) Бүх workflow-г нэгтгэх
def main_workflow(team_abbr, opponent_abbr, average_points_per_game, is_home=True, last_game_win=1, injury_date_str=None):
    # 3a) Өгөгдөл татах
    nba_teams = teams.get_teams()
    abbr_to_id = {t["abbreviation"]: t["id"] for t in nba_teams}
    
    all_games = pd.DataFrame()
    for t in nba_teams:
        gf = leaguegamefinder.LeagueGameFinder(team_id_nullable=t["id"])
        tmp = gf.get_data_frames()[0]
        all_games = pd.concat([all_games, tmp], ignore_index=True)
    
    all_games["GAME_DATE"] = pd.to_datetime(all_games["GAME_DATE"])
    all_games["WIN"]       = all_games["WL"].apply(lambda x: 1 if x=="W" else 0)
    all_games["PTS"]       = all_games["PTS"].astype(float)
    all_games["Points_Per_Game"] = all_games.groupby("TEAM_ID")["PTS"].transform("mean")
    
    def get_opponent_id(row):
        m = row["MATCHUP"]
        # та өөрийн тохирох логик бичнэ
        parts = m.split()
        # жишээ: "BKN vs. SAS" эсвэл "SAS @ BKN"
        if "vs." in m:
            opp_ab = parts[-1]
        elif "@" in m:
            opp_ab = parts[-1]
        else:
            return None
        return abbr_to_id.get(opp_ab.strip(), None)
    
    all_games["OPPONENT_TEAM_ID"] = all_games.apply(get_opponent_id, axis=1)
    all_games["HOME_GAME"]        = all_games["MATCHUP"].apply(lambda x: 1 if "vs." in str(x) else 0)
    all_games["LAST_GAME_RESULT"] = all_games.groupby("TEAM_ID")["WIN"].shift(1).fillna(0)
    
    # LabelEncoding TEAM_ID and OPPONENT_TEAM_ID
    le = LabelEncoder()
    all_games["TEAM_ID_enc"]      = le.fit_transform(all_games["TEAM_ID"])
    all_games["OPPONENT_TEAM_ID_enc"] = le.fit_transform(all_games["OPPONENT_TEAM_ID"].fillna(-1))
    
    # 3b) Бэртэл тоо авах
    injury_count = 0
    if injury_date_str:
        inj_df = fetch_injury_reports(injury_date_str)
        injury_count = compute_team_injury_count(inj_df, team_abbr)
    
    # 3c) Хоёр багийн head-to-head статистик
    h2h = head_to_head_stats(all_games, team_abbr, opponent_abbr, abbr_to_id, nba_teams)
    
    # 3d) Шинж чанаруудыг бэлдэж шинэ хүснэгт
    new_data = pd.DataFrame({
        "TEAM_ID_enc": [ le.transform([abbr_to_id[team_abbr]])[0] ],
        "OPPONENT_TEAM_ID_enc": [ le.transform([abbr_to_id[opponent_abbr]])[0] ],
        "Points_Per_Game": [ average_points_per_game ],
        "HOME_GAME": [ 1 if is_home else 0 ],
        "LAST_GAME_RESULT": [ last_game_win ],
        "injury_count": [ injury_count ],
        "head_to_head_win_rate": [ h2h["win_rate"] ]
    })
    
    # 3e) Моделийг бэлдэж сургах
    X = all_games[["TEAM_ID_enc","OPPONENT_TEAM_ID_enc","Points_Per_Game","HOME_GAME","LAST_GAME_RESULT"]]
    # нэмэлт шинж чанаруудыг тохируулах боломжтой (injury_count, head_to_head_win_rate) хэрвээ all_games дээр байгаа бол
    y = all_games["WIN"]
    
    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X, y)
    
    # 3f) Таамаг гаргах
    pred        = model.predict(new_data)
    pred_probs  = model.predict_proba(new_data)
    print("Prediction: ",        pred)
    print("Prediction probabilities: ", pred_probs)
    
    # 3g) Feature importance / SHAP
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    shap.summary_plot(shap_values, X)
    
    return model

if __name__ == "__main__":
    # Жишээ: баг BKN эсрэг SAS
    team_abbr      = "BKN"
    opponent_abbr  = "SAS"
    avg_pts        = 110.5
    home_flag      = True
    last_win_flag  = 1
    injury_date    = "2025-10-26"
    
    model = main_workflow(team_abbr, opponent_abbr, avg_pts, home_flag, last_win_flag, injury_date)


# 🔍 Тайлбар

# fetch_injury_reports() — өгөгдсөн өдөрт багийн бэртэлтэй тоглогчдын мэдээлэл авах. nbainjuries пакетыг ашиглах боломжтой. 
# PyPI
# compute_team_injury_count() — тухайн багийн бэртэлтэй тоглогчдын тоогоор нэг шинж чанар гаргаж байна.
# head_to_head_stats() — бүх тоглолтын өгөгдлөөс тухайн хоёр багийн хоорондын тоглолтын тоо, ялалт болон ялалтын хувь гаргана.
# main_workflow() — өгөгдлөө татаж, боловсруулж, шинж чанарууд бэлдэж, RandomForestClassifier-ээр сургаж, шинэ тоглолтонд таамаг гаргадаг.

# ⚠️ Анхаарах зүйлс
# injury_date_str дээр өгөгдөх өдөрт үзэгдэх URL, сайтаас scrape хийх код таны орчинд ажиллахгүй байж болно — сайт өөрчлөгдөж болно.
# get_opponent_id() функцэд MATCHUP талбарын формат дээр тулгуурлаад тооцоолсон, таны өгөгдлийн формат өөр байж магадгүй.
# X = all_games[...] хэсэгт шинэ шинж чанарууд (injury_count, head_to_head_win_rate) оруулаагүй байгаа — хэрвээ all_games дээр боломжтой бол оруулж сургах өгөгдөлд багтааж болно.
# LabelEncoder хоёр удаа ашиглаад байна — нэг нь TEAM_ID, дараа нь OPPONENT_TEAM_ID дээр — үүнийг зөв тохируулах шаардлагатай.
# shap.summary_plot() нь график гаргадаг тул notebook эсвэл график гаргах орчинд ажиллаж байвал тохиромжтой.