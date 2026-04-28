
# 🏀 PREDICT THE NBA GAMES
    NBA тоглолтыг AI-аар хэрхэн таамаглах вэ?
    FastAPI with AI


# ⚡ Хийх зүйлс
    - ✅ Тоглогчдын стат харуулах /Энэ жил болон өмнөх жилүүд/
    - ✅ Хоёр баг энэ жил хэдэн удаа учираа таарж тоглосон тоглолтууд
    - ✅ Start and Role тоглогчдыг ялгаж харуулах         
    - ✅ Багийн Injured тоглогчдыг олох


# EXAMPLES
    https://github.com/juliuscecilia33/NBA-Game-Predictions/blob/main/nba2024_2025preds.ipynb



## 🛠️ INSTALLATION
    - python -m venv venv
    - source venv/bin/activate  # macOS/Linux
    - venv\Scripts\activate     # Windows
    - deactivate

    - pip install fastapi uvicorn

    - pip install -r requirements.txt
    - pip freeze > requirements.txt

## POETRY
    - pip install poetry
    - poetry env use python3.10
    - poetry init
    - poetry add fastapi uvicorn nba_api pandas jinja2
    - poetry run uvicorn app.main:app --reload --port 8000

## TOML
    - pip install .

## 🚀 RUN
    - uvicorn main:app --reload --port 8000
    - uvicorn main:app --reload
    - uvicorn app.main:app --reload

## 🧩 Structure
    fastapi_nba/
    ├── app/
    │   ├── __init__.py
    │   ├── main.py          # FastAPI entry point
    │   ├── services/        # API calls (nba_api wrapper)
    │   └── routers/         # API endpoints
    ├── pyproject.toml
    ├── requirements.txt
    └── README.md


# ⚡ SOME STATISTICAL WEBSITES
https://www.sofascore.com/basketball