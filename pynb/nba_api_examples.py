from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.static import teams
import pandas as pd

def get_team_avg_points(team_abbr, season_year=2025):
    """
    Тухайн багийн (team_abbr) өгөгдсөн улиралд (season_year)
    нэг тоглолтонд авсан дундаж оноог буцаана.
    """
    nba_teams = teams.get_teams()
    team_info = (next(t for t in nba_teams if t['abbreviation'] == team_abbr), None)
    if team_info is None:
        print("Team not found")

    team_id = team_info['id']

    # Тухайн багийн бүх тоглолтыг татах
    games = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id).get_data_frames()[0]
    
    # Огноо хувиргах
    games['GAME_DATE'] = pd.to_datetime(games['GAME_DATE'], errors='coerce')
    
    # Зөвхөн тухайн жилд (улиралд) хамаарах тоглолтуудыг авах
    season_games = games[games['GAME_DATE'].dt.year == season_year]
    
    # Хэрвээ тухайн жилд тоглолт байхгүй бол бүх тоглолт ашиглана (fallback)
    if season_games.empty:
        print(f"⚠️ {team_abbr}: {season_year} онд тоглолт олдсонгүй. Бүх тоглолтоор тооцож байна.")
        season_games = games

    # PTS дундаж тооцоолох
    avg_pts = season_games['PTS'].astype(float).mean()
    print(f"📊 {team_abbr} - {season_year} оны дундаж оноо: {avg_pts:.2f}")
    return avg_pts

bkn_avg = get_team_avg_points("BKN", season_year=2025)
sas_avg = get_team_avg_points("SAS", season_year=2025)

print("BKN avg points:", bkn_avg)
print("SAS avg points:", sas_avg)


# 🏠 is_home=True — Гэрийн талбайд тоглох эсэх
# NBA багууд гэрийн талбайд (home) тоглохдоо илүү сайн тоглодог хандлагатай байдаг.

# 🧩 Утга:
# Утга	Тайлбар
# True эсвэл 1	Гэрийн талбайд тоглож байна (vs. гэж тэмдэглэгддэг)
# False эсвэл 0	Зочны талбайд тоглож байна (@ гэж тэмдэглэгддэг)
# 🧠 Автомат шалгах арга:

# Хэрвээ та тухайн тоглолтын matchup мэдээлэлтэй бол (жишээ нь "BKN vs. SAS" эсвэл "BKN @ SAS") дараах байдлаар is_home-г автоматаар тодорхойлж болно:

def is_home_game(matchup, team_abbr):
    if "vs." in matchup and team_abbr in matchup:
        return True
    if "@" in matchup and team_abbr in matchup:
        return False
    return None

print(is_home_game("BKN vs. SAS", "BKN"))  # True
print(is_home_game("BKN @ SAS", "BKN"))    # False



# 🏆 last_win=1 — Сүүлийн тоглолтын үр дүн
# Энэ нь тухайн баг өмнөх тоглолтонд ялсан эсэхийг илэрхийлнэ.

# 🧩 Утга:
# Утга	Тайлбар
# 1	Баг сүүлийн тоглолтдоо ялсан
# 0	Сүүлийн тоглолтдоо хожигдсон
# 🧠 Автомат тооцох арга:

# nba_api ашиглан тухайн багийн хамгийн сүүлийн тоглолтын мэдээллийг шалгаж болно:

from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.static import teams
import pandas as pd

def get_last_game_result(team_abbr):
    nba_teams = teams.get_teams()
    team_info = next(t for t in nba_teams if t['abbreviation'] == team_abbr)
    team_id = team_info['id']

    games = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id).get_data_frames()[0]
    games = games.sort_values("GAME_DATE", ascending=False)
    last_game = games.iloc[0]

    result = 1 if last_game["WL"] == "W" else 0
    print(f"{team_abbr} last game: {last_game['MATCHUP']} ({last_game['WL']})")
    return result

# Жишээ:
last_win = get_last_game_result("BKN")