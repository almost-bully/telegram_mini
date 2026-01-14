from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google_client import get_sheets_service
import re

app = FastAPI()

sheets = get_sheets_service()

# ===== НАСТРОЙКИ =====
MAIN_SHEET_ID = "1hICdPS-6umn4n7uV7UWF49PFwXbnms75qI2-Hc00fc8"
MAIN_SHEET_NAME = "Лист2"


# ===== МОДЕЛИ =====
class AuthRequest(BaseModel):
    ka: str


class UpdatePointRequest(BaseModel):
    sheet_url: str
    route_sheet: str
    point_id: str
    status: bool
    problem: str | None = ""


# ===== ВСПОМОГАТЕЛЬНЫЕ =====
def extract_sheet_id(url: str) -> str:
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    if not match:
        raise ValueError("Неверная ссылка на Google Sheet")
    return match.group(1)


# ===== API =====

@app.get("/")
def root():
    return {"status": "ok", "message": "API is running"}


# 1️⃣ АВТОРИЗАЦИЯ ПО КА → ТЕРРИТОРИИ
@app.post("/auth")
def auth(data: AuthRequest):
    ka = data.ka.strip()

    result = sheets.spreadsheets().values().get(
        spreadsheetId=MAIN_SHEET_ID,
        range=f"{MAIN_SHEET_NAME}!A:D"
    ).execute()

    rows = result.get("values", [])
    territories = []

    for row in rows[1:]:  # пропускаем шапку
        if len(row) >= 4 and row[3] == ka:
            territories.append({
                "territory": row[0],
                "sheet_url": row[1]
            })

    if not territories:
        raise HTTPException(status_code=403, detail="КА не найден")

    return territories


# 2️⃣ ПОЛУЧЕНИЕ МАРШРУТОВ (ВКЛАДОК)
@app.get("/routes")
def get_routes(sheet_url: str):
    sheet_id = extract_sheet_id(sheet_url)

    spreadsheet = sheets.spreadsheets().get(
        spreadsheetId=sheet_id
    ).execute()

    routes = []
    for s in spreadsheet["sheets"]:
        routes.append(s["properties"]["title"])

    return routes


# 3️⃣ ПОЛУЧЕНИЕ ТОЧЕК КОНКРЕТНОГО МАРШРУТА
@app.get("/points")
def get_points(sheet_url: str, route_sheet: str):
    sheet_id = extract_sheet_id(sheet_url)

    result = sheets.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"{route_sheet}!A:BF"
    ).execute()

    rows = result.get("values", [])
    points = []

    for row in rows[1:]:  # пропускаем шапку
        if len(row) <= 26:
            continue

        point_id = row[26].strip() if len(row) > 26 else ""
        if not point_id:
            continue

        points.append({
            "point_id": point_id,
            "route": row[33] if len(row) > 33 else "",
            "street": row[34] if len(row) > 34 else "",
            "house": row[35] if len(row) > 35 else "",
            "entrance": row[36] if len(row) > 36 else "",
            "flats": row[37] if len(row) > 37 else "",
        })

    return points


# 4️⃣ ОБНОВЛЕНИЕ СТАТУСА ТОЧКИ
@app.post("/update")
def update_point(data: UpdatePointRequest):
    sheet_id = extract_sheet_id(data.sheet_url)

    result = sheets.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"{data.route_sheet}!A:BF"
    ).execute()

    rows = result.get("values", [])

    for i, row in enumerate(rows):
        if len(row) > 26 and row[26] == data.point_id:
            row_index = i + 1

            sheets.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f"{data.route_sheet}!AM{row_index}",
                valueInputOption="USER_ENTERED",
                body={"values": [[str(data.status).upper()]]}
            ).execute()

            sheets.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f"{d
