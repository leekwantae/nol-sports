#!/usr/bin/env python3
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

PAGE_URL = "https://nol.yanolja.com/ticket/genre/sports/bears"
OUT_FILE = Path("games.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/150.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}

def download_page() -> str:
    req = Request(PAGE_URL, headers=HEADERS)
    with urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")

def decode_next_chunks(page: str) -> str:
    """
    Next.js가 self.__next_f.push([1, "..."]) 형태로 넣어 둔 문자열을 복원합니다.
    """
    chunks = []
    pattern = re.compile(
        r'self\.__next_f\.push\(\[1,\s*("(?:\\.|[^"\\])*")\]\)',
        re.DOTALL,
    )
    for match in pattern.finditer(page):
        quoted = match.group(1)
        try:
            chunks.append(json.loads(quoted))
        except json.JSONDecodeError:
            continue

    # 페이지 HTML 자체와 복원된 Next.js 데이터를 함께 검색합니다.
    return page + "\n" + "\n".join(chunks)

def extract_goods_objects(text: str) -> list[dict]:
    """
    goodsCode로 시작하는 각 경기 JSON 객체를 찾아 JSONDecoder로 안전하게 읽습니다.
    """
    text = html.unescape(text)
    decoder = json.JSONDecoder()
    games = []
    seen = set()

    markers = ['{"goodsCode":"', '{\\"goodsCode\\":\\"']

    candidate_texts = [text]
    # 일부 응답은 한 번 더 이스케이프되어 있으므로 완화한 사본도 검색
    candidate_texts.append(
        text.replace(r'\"', '"')
            .replace(r'\/', '/')
            .replace(r'\\u0026', '&')
    )

    for source in candidate_texts:
        start = 0
        while True:
            pos = source.find('{"goodsCode":"', start)
            if pos < 0:
                break
            try:
                obj, consumed = decoder.raw_decode(source[pos:])
            except json.JSONDecodeError:
                start = pos + 14
                continue

            if isinstance(obj, dict) and obj.get("goodsCode"):
                code = str(obj["goodsCode"])
                if code not in seen:
                    seen.add(code)
                    games.append(obj)
            start = pos + max(consumed, 1)

    return games

def simplify(game: dict) -> dict:
    sport = game.get("sport") or {}
    home = sport.get("homeOrganization") or {}
    away = sport.get("awayOrganization") or {}
    pre_sales = game.get("preSales") or []
    first_pre = pre_sales[0] if pre_sales else {}

    return {
        "goodsCode": game.get("goodsCode"),
        "goodsName": game.get("goodsName"),
        "playDate": sport.get("playDate") or game.get("playStartDate"),
        "playTime": sport.get("playTime"),
        "homeTeam": home.get("name"),
        "awayTeam": away.get("name"),
        "placeName": game.get("placeName"),
        "bookingOpenTime": game.get("bookingOpenTime"),
        "bookingEndTime": game.get("bookingEndTime"),
        "preBookingName": first_pre.get("preBookingKindName"),
        "preBookingOpenTime": first_pre.get("minBookingOpenTime"),
        "preBookingEndTime": first_pre.get("maxBookingEndTime"),
        "posterImageUrl": game.get("posterImageUrl"),
    }

def main() -> None:
    page = download_page()
    combined = decode_next_chunks(page)
    raw_games = extract_goods_objects(combined)

    if not raw_games:
        raise RuntimeError(
            "두산 페이지에서 경기정보를 찾지 못했습니다. "
            "NOL 페이지 구조가 변경되었을 가능성이 있습니다."
        )

    games = [simplify(g) for g in raw_games]
    games.sort(key=lambda g: (
        g.get("playDate") or "",
        g.get("playTime") or "",
        g.get("goodsCode") or "",
    ))

    output = {
        "sourcePage": PAGE_URL,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "totalElements": len(games),
        "games": games,
    }

    OUT_FILE.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"경기 {len(games)}건 저장 완료: {OUT_FILE}")

if __name__ == "__main__":
    main()
