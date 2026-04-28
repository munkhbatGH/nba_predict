from datetime import datetime
import pytz

ET = pytz.timezone("US/Eastern")
MN = pytz.timezone("Asia/Ulaanbaatar")

def convert_times(date_str, time_str):
  try:
    time_clean = time_str.replace(" ET", "").strip()
    dt_str = f"{date_str[:10]} {time_clean}"

    et = pytz.timezone("US/Eastern")
    mn = pytz.timezone("Asia/Ulaanbaatar")

    dt = datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
    dt_et = et.localize(dt)

    return {
      "us": dt_et.strftime("%Y-%m-%d %I:%M %p"),  # ET (US)
      "mongolia": dt_et.astimezone(mn).strftime("%Y-%m-%d %I:%M %p")
    }
  except Exception:
    return {
      "us": "TBD",
      "mongolia": "TBD"
    }

# =========================
# 🧠 GET NBA CORRECT DATE
# =========================
def get_nba_game_date():
    """
    NBA uses ET calendar day.
    So we DON'T add +1 blindly.
    """
    now_et = datetime.now(ET)

    # 👉 IMPORTANT: use TODAY (not tomorrow)
    return now_et.strftime("%m/%d/%Y")