"""테스트 공통 설정: 테스트 전용 Streamlit 서버와 페이지 fixture."""

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

ROOT = Path(__file__).resolve().parent.parent
PORT = 8599
BASE_URL = f"http://localhost:{PORT}"
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"

# Streamlit은 비동기로 다시 그려지므로 기본 대기 시간을 넉넉하게
expect.set_options(timeout=10_000)


@pytest.fixture(scope="session")
def data_file(tmp_path_factory) -> Path:
    """실제 data/shopping_list.json 대신 쓸 임시 데이터 파일."""
    return tmp_path_factory.mktemp("data") / "shopping_list.json"


@pytest.fixture(scope="session")
def app_server(data_file):
    """테스트 동안 백그라운드로 Streamlit 서버를 띄우고, 끝나면 종료한다."""
    env = {**os.environ, "SHOPPING_DATA_FILE": str(data_file)}
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py",
         "--server.port", str(PORT), "--server.headless", "true",
         "--browser.gatherUsageStats", "false"],
        cwd=ROOT, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.time() + 30
        while True:
            try:
                with urllib.request.urlopen(f"{BASE_URL}/_stcore/health", timeout=1) as r:
                    if r.status == 200:
                        break
            except OSError:
                pass
            if proc.poll() is not None or time.time() > deadline:
                raise RuntimeError("Streamlit 서버가 시작되지 않았어요.")
            time.sleep(0.5)
        yield BASE_URL
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture
def app(page: Page, app_server, data_file, request) -> Page:
    """빈 리스트 상태로 앱을 연 페이지. 테스트가 끝나면 스크린샷을 남긴다."""
    data_file.unlink(missing_ok=True)
    page.goto(app_server)
    expect(page.get_by_text("쇼핑 리스트가 비어 있어요")).to_be_visible()
    yield page
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    page.screenshot(path=SCREENSHOT_DIR / f"{request.node.name}.png", full_page=True)
