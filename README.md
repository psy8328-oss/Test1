# 🛒 쇼핑 리스트

Streamlit으로 만든 간단한 쇼핑 리스트 앱입니다. 기획 내용은 [PRD.md](PRD.md)를 참고하세요.

## 설치

```bash
pip install -r requirements.txt
```

## 실행

```bash
streamlit run app.py
```

브라우저에서 http://localhost:8501 로 접속합니다.

## 구조

```
app.py            # Streamlit 메인 앱
storage.py        # JSON 로드/저장 함수
data/             # shopping_list.json 저장 위치 (자동 생성)
requirements.txt
```

## 테스트 (Playwright E2E)

```bash
pip install -r requirements-dev.txt
playwright install chromium
pytest tests -v
```

- 테스트는 포트 8599에 전용 Streamlit 서버를 자동으로 띄우고 끝나면 종료합니다.
- 데이터는 임시 파일(`SHOPPING_DATA_FILE` 환경변수)을 사용하므로 실제 `data/shopping_list.json`은 건드리지 않습니다.
- 각 테스트의 스크린샷은 `tests/screenshots/`에 저장됩니다.
