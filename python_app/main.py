from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.db import clear_history, delete_reading, get_history, get_reading, init_db, save_reading
from app.iching import CoinFace, LineType, calculate_line, from_dict, generate_reading, label_for_total, to_dict, toss_coin

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="三钱起卦法 · Python 版")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class LineInput(BaseModel):
    position: int = Field(ge=1, le=6)
    coins: list[int] = Field(min_length=3, max_length=3)


class CreateReadingRequest(BaseModel):
    question: str = ""
    lines: list[LineInput] = Field(min_length=6, max_length=6)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {})


@app.get("/toss", response_class=HTMLResponse)
def toss_page(request: Request, question: str = "") -> HTMLResponse:
    return templates.TemplateResponse(request, "toss.html", {"question": question.strip()})


@app.post("/api/toss")
def toss_api() -> dict[str, object]:
    coins = (toss_coin(), toss_coin(), toss_coin())
    line = calculate_line(coins, position=1)
    return {
        "coins": list(line.coins),
        "total": line.total,
        "type": line.type,
        "label": label_for_total(line.total),
    }


@app.post("/api/readings")
def create_reading(payload: CreateReadingRequest) -> dict[str, str]:
    lines = []
    for idx, line_input in enumerate(payload.lines):
        try:
            c1, c2, c3 = (CoinFace(line_input.coins[0]), CoinFace(line_input.coins[1]), CoinFace(line_input.coins[2]))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="硬币结果非法，应为 2 或 3") from exc
        lines.append(calculate_line((c1, c2, c3), position=idx + 1))

    reading = generate_reading(payload.question.strip(), lines)
    reading_dict = to_dict(reading)
    save_reading(reading_dict)

    return {
        "id": reading.id,
        "url": f"/readings/{reading.id}",
    }


def format_ts(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d %H:%M")


def build_line_views(reading) -> list[dict[str, object]]:
    views: list[dict[str, object]] = []
    for line in reversed(reading.lines):
        original_is_yang = line.type in (LineType.YOUNG_YANG, LineType.OLD_YANG)
        if line.type == LineType.OLD_YANG:
            changed_is_yang = False
        elif line.type == LineType.OLD_YIN:
            changed_is_yang = True
        else:
            changed_is_yang = line.type == LineType.YOUNG_YANG

        if line.position == 1:
            position_label = "初"
        elif line.position == 6:
            position_label = "上"
        else:
            position_label = str(line.position)

        views.append(
            {
                "position": line.position,
                "position_label": position_label,
                "total": line.total,
                "label": label_for_total(line.total),
                "is_moving": line.type in (LineType.OLD_YANG, LineType.OLD_YIN),
                "moving_mark": "○" if line.type == LineType.OLD_YANG else ("×" if line.type == LineType.OLD_YIN else ""),
                "original_symbol": "━━━" if original_is_yang else "━ ━",
                "changed_symbol": "━━━" if changed_is_yang else "━ ━",
            }
        )
    return views


def build_moving_views(reading) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for line in reading.lines:
        if line.total not in (6, 9):
            continue

        line_data = reading.originalHexagram.lines[line.position - 1]
        trend = (
            f"此爻变动后，由{'阳变阴' if line.total == 9 else '阴变阳'}，局势将向“{reading.changedHexagram.name}”卦转变。"
            + ("刚极则柔，需注意由强转弱，适度收敛。" if line.total == 9 else "柔极则刚，新的力量正在生成，由弱转强。")
        )

        items.append(
            {
                "name": line_data.name,
                "state": "老阳 · 动" if line.total == 9 else "老阴 · 动",
                "position_desc": line_data.positionDesc,
                "advice": line_data.advice,
                "trend": trend,
            }
        )
    return items


@app.get("/readings/{reading_id}", response_class=HTMLResponse)
def reading_detail(request: Request, reading_id: str) -> HTMLResponse:
    raw = get_reading(reading_id)
    if not raw:
        raise HTTPException(status_code=404, detail="记录不存在")

    reading = from_dict(raw)
    context = {
        "reading": reading,
        "line_views": build_line_views(reading),
        "moving_views": build_moving_views(reading),
        "formatted_time": format_ts(reading.timestamp),
    }
    return templates.TemplateResponse(request, "result.html", context)


@app.get("/history", response_class=HTMLResponse)
def history_page(request: Request) -> HTMLResponse:
    rows = get_history()
    items = []
    for raw in rows:
        items.append(
            {
                "id": raw["id"],
                "question": raw.get("question") or "无事所求",
                "timestamp": format_ts(raw["timestamp"]),
                "original": raw["originalHexagram"]["name"],
                "changed": raw["changedHexagram"]["name"],
            }
        )

    return templates.TemplateResponse(request, "history.html", {"items": items})


@app.post("/history/{reading_id}/delete")
def history_delete(reading_id: str) -> RedirectResponse:
    delete_reading(reading_id)
    return RedirectResponse(url="/history", status_code=303)


@app.post("/history/clear")
def history_clear() -> RedirectResponse:
    clear_history()
    return RedirectResponse(url="/history", status_code=303)
