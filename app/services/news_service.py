import feedparser
from urllib.parse import quote
from datetime import datetime, timedelta

NEWS_SOURCES = [
  # {
  #   "name": "NBA",
  #   "type": "rss",
  #   "url": "https://www.nba.com/news/rss.xml"
  # },
  {
    "name": "GOOGLE",
    "type": "google",
    "url": "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
  }
]

def parse_date(date_str):
  formats = [
    "%a, %d %b %Y %H:%M:%S %Z",
    "%a, %d %b %Y %H:%M:%S GMT",
    "%Y-%m-%dT%H:%M:%SZ"
  ]
  for fmt in formats:
    try:
      return datetime.strptime(date_str, fmt)
    except:
      continue
  return None


def normalize_game_date(game_date):
  if isinstance(game_date, str):
    return datetime.strptime(game_date[:10], "%Y-%m-%d")
  return game_date or datetime.now()


def safe_in_range(dt, start, end):
  if not dt:
    return True
  return start <= dt <= end


def get_team_news(team1, team2, game_date=None):
  query = f"{team1} {team2} NBA"

  results = []

  base_date = normalize_game_date(game_date)
  start = base_date - timedelta(days=2)
  end = base_date + timedelta(days=2)

  for source in NEWS_SOURCES:
    try:

      if source["type"] == "google":
        url = source["url"].format(query=quote(query))
      else:
        url = source["url"]
      feed = feedparser.parse(url)

      for entry in feed.entries:

        published = parse_date(entry.get("published", ""))

        if not safe_in_range(published, start, end):
          continue

        title = entry.title.lower()

        if team1.lower() not in title and team2.lower() not in title:
          continue

        results.append({
          "source": source["name"],
          "title": entry.title,
          "link": entry.link,
          "published": entry.get("published", "")
        })

        if len(results) >= 15:
          return results

    except Exception as e:
      print(f"News error ({source['name']}): {e}")

  return results