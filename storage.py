"""쇼핑 리스트 데이터를 JSON 파일로 저장하고 불러오는 모듈."""

import json
import os
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

# 환경변수 SHOPPING_DATA_FILE로 저장 위치를 바꿀 수 있다 (테스트용).
DATA_FILE = Path(
    os.environ.get("SHOPPING_DATA_FILE")
    or Path(__file__).parent / "data" / "shopping_list.json"
)
DATA_DIR = DATA_FILE.parent

# 여러 세션(탭/사용자)이 동시에 읽고-수정하고-저장할 때 서로 덮어쓰지 않게 한다.
_lock = threading.RLock()


def load_items() -> list[dict]:
    """JSON 파일에서 아이템 목록을 불러온다.

    파일이 없거나 내용이 깨져 있으면 빈 리스트를 반환한다.
    """
    if not DATA_FILE.exists():
        return []
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


def save_items(items: list[dict]) -> None:
    """아이템 목록을 JSON 파일에 저장한다. 폴더가 없으면 만든다.

    임시 파일에 다 쓴 뒤 교체하므로, 저장 도중에 다른 세션이 읽어도
    반쯤 쓰인 파일을 보지 않는다.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=DATA_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DATA_FILE)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


@contextmanager
def transaction() -> Iterator[list[dict]]:
    """최신 목록을 불러와 수정한 뒤 저장한다 (다른 세션과 겹치지 않게 잠금).

    사용법:
        with transaction() as items:
            items.append(...)
    """
    with _lock:
        items = load_items()
        yield items
        save_items(items)
