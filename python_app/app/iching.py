from __future__ import annotations

import json
import random
import time
import uuid
from dataclasses import asdict, dataclass
from enum import IntEnum
from pathlib import Path
from typing import Any


class CoinFace(IntEnum):
    BACK = 2
    FRONT = 3


class LineType(IntEnum):
    OLD_YIN = 6
    YOUNG_YANG = 7
    YOUNG_YIN = 8
    OLD_YANG = 9


@dataclass
class LineResult:
    position: int
    coins: tuple[int, int, int]
    total: int
    type: int
    timestamp: int


@dataclass
class LineInterpretation:
    name: str
    positionDesc: str
    advice: str


@dataclass
class HexagramData:
    code: str
    name: str
    pinyin: str
    description: str
    overview: str
    career: str
    love: str
    strategy: str
    lines: list[LineInterpretation]


@dataclass
class ReadingRecord:
    id: str
    timestamp: int
    question: str
    lines: list[LineResult]
    originalHexagram: HexagramData
    changedHexagram: HexagramData


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "hexagrams.json"


def load_hexagram_map(path: Path = DATA_PATH) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


HEXAGRAM_MAP = load_hexagram_map()


def toss_coin() -> CoinFace:
    return CoinFace.FRONT if random.random() > 0.5 else CoinFace.BACK


def calculate_line(coins: tuple[CoinFace, CoinFace, CoinFace], position: int) -> LineResult:
    total = sum(int(c) for c in coins)
    match total:
        case 6:
            line_type = LineType.OLD_YIN
        case 7:
            line_type = LineType.YOUNG_YANG
        case 8:
            line_type = LineType.YOUNG_YIN
        case 9:
            line_type = LineType.OLD_YANG
        case _:
            line_type = LineType.YOUNG_YANG

    return LineResult(
        position=position,
        coins=(int(coins[0]), int(coins[1]), int(coins[2])),
        total=total,
        type=int(line_type),
        timestamp=int(time.time() * 1000),
    )


def line_type_to_binary(line_type: int, is_original: bool) -> str:
    if line_type == LineType.YOUNG_YANG:
        return "1"
    if line_type == LineType.YOUNG_YIN:
        return "0"
    if line_type == LineType.OLD_YANG:
        return "1" if is_original else "0"
    if line_type == LineType.OLD_YIN:
        return "0" if is_original else "1"
    return "1"


def generate_id() -> str:
    return uuid.uuid4().hex


def get_line_name(position: int, is_yang: bool) -> str:
    nature = "九" if is_yang else "六"
    if position == 1:
        return f"初{nature}"
    if position == 6:
        return f"上{nature}"
    middle = ["二", "三", "四", "五"]
    return f"{nature}{middle[position - 2]}"


def get_general_line_text(position: int, is_yang: bool) -> tuple[str, str]:
    if position == 1:
        return (
            "【时位：初难】处于事物的萌芽或基层阶段，地位未定，力量微弱。",
            "阳气潜藏，如“潜龙勿用”。此时应韬光养晦，充实自己，不宜急于表现或行动。"
            if is_yang
            else "阴柔居下，基础薄弱。应安分守己，脚踏实地，切勿好高骛远，等待时机成熟。",
        )
    if position == 2:
        return (
            "【时位：二佳】处于下卦的中位，象征地方骨干或中层管理者，位置得当。",
            "刚中之德，才华初显。利于进取，可得贵人赏识（利见大人），适合展现能力。"
            if is_yang
            else "柔顺中正，不仅有才，且能包容。适合配合上级，稳健发展，运势平顺。",
        )
    if position == 3:
        return (
            "【时位：三劳】处于下卦之极，将进上卦。位置尴尬，多劳多忧，极其凶险。",
            "过刚不中，处于变革边缘。必须极其勤勉警惕（终日乾乾），虽有危险，但谨慎可无咎。"
            if is_yang
            else "阴柔不正，才不配位。不要逞强，不要追求虚名，应守住本分，否则容易招致羞辱。",
        )
    if position == 4:
        return (
            "【时位：四惧】进入上卦，伴君如伴虎。虽地位高，但最需小心谨慎。",
            "刚居柔位，虽有能力但需收敛。如龙“或跃在渊”，进退需看时机，不可功高震主。"
            if is_yang
            else "柔顺得正，能妥善辅佐君王。只要顺应形势，尽心服务，就不会有灾祸。",
        )
    if position == 5:
        return (
            "【时位：五尊】全卦之主，君王之位。象征事物的顶峰或核心领导。",
            "刚健中正，如“飞龙在天”。得位得势，利于施展抱负，造福众人，是大吉之象。"
            if is_yang
            else "阴居尊位，柔弱之主。应学会“垂拱而治”，重用贤能（如下方的阳爻），不可独断专行。",
        )
    if position == 6:
        return (
            "【时位：上亢】事物发展的终极，物极必反。象征退休的元老或局势的边缘。",
            "亢龙有悔，进无可进。切忌傲慢固执，应知进退，及时引退或转变方向，否则必有悔恨。"
            if is_yang
            else "阴柔居极，虽然位高但无权。应保持低调，安享成果，避免卷入新的纷争。",
        )
    return ("", "")


def get_hexagram_data(binary_string: str) -> HexagramData:
    data = HEXAGRAM_MAP.get(binary_string)
    lines: list[LineInterpretation] = []
    for i in range(6):
        is_yang = binary_string[i] == "1"
        position = i + 1
        line_name = get_line_name(position, is_yang)
        position_desc, advice = get_general_line_text(position, is_yang)
        lines.append(LineInterpretation(name=line_name, positionDesc=position_desc, advice=advice))

    if not data:
        return HexagramData(
            code=binary_string,
            name="未知卦",
            pinyin="Wei Zhi",
            description="卦象计算异常",
            overview="数据缺失",
            career="暂无",
            love="暂无",
            strategy="暂无",
            lines=lines,
        )

    return HexagramData(
        code=binary_string,
        name=data["name"],
        pinyin="",
        description=data["desc"],
        overview=data["overview"],
        career=data["career"],
        love=data["love"],
        strategy=data["strategy"],
        lines=lines,
    )


def generate_reading(question: str, lines: list[LineResult]) -> ReadingRecord:
    original_binary = "".join(line_type_to_binary(line.type, True) for line in lines)
    changed_binary = "".join(line_type_to_binary(line.type, False) for line in lines)

    return ReadingRecord(
        id=generate_id(),
        timestamp=int(time.time() * 1000),
        question=question,
        lines=lines,
        originalHexagram=get_hexagram_data(original_binary),
        changedHexagram=get_hexagram_data(changed_binary),
    )


def to_dict(reading: ReadingRecord) -> dict[str, Any]:
    return asdict(reading)


def from_dict(raw: dict[str, Any]) -> ReadingRecord:
    lines = [LineResult(**line) for line in raw["lines"]]

    original_lines = [LineInterpretation(**x) for x in raw["originalHexagram"]["lines"]]
    changed_lines = [LineInterpretation(**x) for x in raw["changedHexagram"]["lines"]]

    original_hex = HexagramData(**{**raw["originalHexagram"], "lines": original_lines})
    changed_hex = HexagramData(**{**raw["changedHexagram"], "lines": changed_lines})

    return ReadingRecord(
        id=raw["id"],
        timestamp=raw["timestamp"],
        question=raw.get("question", ""),
        lines=lines,
        originalHexagram=original_hex,
        changedHexagram=changed_hex,
    )


def label_for_total(total: int) -> str:
    if total == 6:
        return "老阴 (变)"
    if total == 7:
        return "少阳 (静)"
    if total == 8:
        return "少阴 (静)"
    if total == 9:
        return "老阳 (变)"
    return "未知"
