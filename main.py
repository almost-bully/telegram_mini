# main.py

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google_client import get_sheets_service
from config import MAIN_SHEET_ID, MAIN_SHEET_NAME
import re
import logging

# ================== Настройка ==================
logging.basicConfig(level=logging.DEBUG)

app = FastAPI(title="Telegram Mini App Backend")

# CORS для веб-frontend (Mini App)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Google Sheets API
sheets = get_sheets_service()

# ================== МОДЕЛИ ==================

class AuthRequest(BaseModel):
    ka: str


class UpdatePointRequest(BaseModel):
    sheet_id: str
    sheet_name: str
    point_id: str  # AA
    status: bool
    problem: str | None = ""


# ================== ВСПОМОГАТЕЛЬНЫЕ ==================

def extract_sheet_id(url: str) -> str:
    """Извлечение ID Google Sheet из ссылки"""
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    if not match:
        raise ValueError("Неверная ссылка на Google Sheet")
    return match.group(1)


# ================== ЭНДПОИНТЫ ==================

@app.post("/auth")
def auth(data: AuthRequest):
    ka = data.ka.strip()

    result = sheets.spreadsheets().values().get(
        spreadsheetId=MAIN_SHEET_ID,
        range=f"{MAIN_SHEET_NAME}!A:D",
        valueRenderOption='UNFORMATTED_VALUE',
        majorDimension='ROWS'
    ).execute()

    rows = result.get("values", [])
    territories = []

    for row in rows[1:]:
        if len(row) >= 4 and str(row[3]).strip() == ka:
            territories.append({
                "territory": row[0],
                "sheet_url": row[1]
            })

    if not territories:
        raise HTTPException(status_code=403, detail="КА не найден")

    return territories


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


@app.get("/points")
def get_points(sheet_url: str, sheet_name: str):
    sheet_id = extract_sheet_id(sheet_url)

    result = sheets.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"{sheet_name}!A:BF",
        valueRenderOption='UNFORMATTED_VALUE',
        majorDimension='ROWS'
    ).execute()

    rows = result.get("values", [])

    # расширяем каждую строку до 58 столбцов (A–BF)
    for i, row in enumerate(rows):
        while len(row) < 58:
            row.append("")

    points = []
    for row in rows:
        point_id = str(row[26]).strip()  # AA
        if point_id == "":
            continue
        points.append({
            "point_id": point_id,
            "street": str(row[34]),
            "house": str(row[35]),
            "entrance": str(row[36]),
            "status": str(row[38]),
            "problem": str(row[41])
        })
    return points


@app.post("/update")
def update_point(data: UpdatePointRequest):
    try:
        sheet_id = extract_sheet_id(data.sheet_id)

        result = sheets.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"{data.sheet_name}!A:BF",
            valueRenderOption='UNFORMATTED_VALUE',
            majorDimension='ROWS'
        ).execute()

        rows = result.get("values", [])

        # расширяем строки до 58 столбцов
        for i, row in enumerate(rows):
            while len(row) < 58:
                row.append("")

        # ищем строку по point_id
        row_index = None
        for i, row in enumerate(rows):
            if str(row[26]).strip() == data.point_id:
                row_index = i + 1  # Google Sheets нумерация с 1
                break

        if row_index is None:
            raise HTTPException(status_code=404, detail="Точка с таким point_id не найдена")

        # обновляем статус (AM = 39-й)
        sheets.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"{data.sheet_name}!AM{row_index}",
            valueInputOption="USER_ENTERED",
            body={"values": [[data.status]]}
        ).execute()

        # обновляем проблему (AP = 42-й)
        sheets.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"{data.sheet_name}!AP{row_index}",
            valueInputOption="USER_ENTERED",
            body={"values": [[data.problem or ""]]}
        ).execute()

        return {"status": "ok"}

    except Exception as e:
        logging.exception("Ошибка в update_point:")
        return JSONResponse(status_code=500, content={"error": str(e)})
