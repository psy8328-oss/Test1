# 쇼핑 리스트 앱 단계별 프롬프트

> `PRD.md`를 기준으로 Claude Code에 순서대로 입력하는 프롬프트입니다.
> 각 단계가 끝나면 `streamlit run app.py`로 직접 확인한 뒤 다음 단계로 넘어가세요.

---

## 1단계: 기본 뼈대 작성

```
PRD.md를 읽고 쇼핑 리스트 앱의 기본 뼈대를 만들어줘.

[만들 파일]
- app.py : Streamlit 메인 앱
- storage.py : JSON 로드/저장 함수 (load_items(), save_items(items))
- data/ 폴더 (shopping_list.json은 없으면 자동 생성)
- requirements.txt : streamlit
- README.md : 설치, 실행 방법

[이번 단계 범위]
- PRD 4장 데이터 모델(id, name, quantity, checked, created_at)을 그대로 사용
- 앱 시작 시 JSON에서 아이템을 불러와 st.session_state["items"]에 저장
- 제목 "🛒 쇼핑 리스트"와 아이템 목록을 텍스트로 표시하는 것까지만 구현
- 리스트가 비어 있으면 "쇼핑 리스트가 비어 있어요. 아이템을 추가해 보세요!" 표시
- 추가/수정/삭제/체크 기능은 아직 만들지 마. 함수 이름만 자리만 잡아둬 (add_item, update_item, delete_item, toggle_item)

[조건]
- JSON 파일이 없거나 깨져 있으면 빈 리스트로 시작하고 앱이 죽지 않게 해줘
- 저장 시 한글이 깨지지 않게 ensure_ascii=False, UTF-8 사용
- 다 만들면 streamlit run app.py로 실행해서 에러 없이 뜨는지 확인해줘
```

---

## 2단계: 기능 추가

```
PRD.md 3장 기능 요구사항에 맞춰 app.py에 기능을 구현해줘.

[구현할 기능]
1. 추가: st.form 안에 이름 text_input + 수량 number_input(최소 1, 기본 1) + [추가] 버튼
   - Enter로도 추가되게
   - 공백만 입력하면 st.warning으로 경고하고 추가하지 않기
   - 추가 후 입력창 비우기 (clear_on_submit=True)
2. 체크: 각 아이템 앞 st.checkbox로 checked 상태 전환
3. 수정: [수정] 버튼 → 해당 행이 편집 모드(이름, 수량 입력 + [저장]/[취소])로 전환
   - 편집 중인 아이템 id는 st.session_state["editing_id"]로 관리
   - 빈 이름으로는 저장 불가
4. 삭제: 각 행 [삭제] 버튼으로 개별 삭제
5. 일괄 삭제: 하단에 [체크된 항목 삭제], [전체 삭제] 버튼
6. 진행 현황: 상단에 "3 / 5 구매 완료" 텍스트 + st.progress

[조건]
- 모든 변경은 즉시 storage.save_items()로 JSON에 저장
- 위젯 key는 아이템 id 기반으로 고유하게 (예: f"check_{id}", f"del_{id}")
- 버튼 처리 후 상태가 바로 반영되도록 필요한 곳에 st.rerun() 사용
- 새로고침해도 데이터가 유지되는지 확인해줘
```

---

## 3단계: UI 디자인

```
기능은 그대로 두고 쇼핑 리스트 앱의 UI를 다듬어줘.

[디자인 요구사항]
- st.set_page_config(page_title="쇼핑 리스트", page_icon="🛒", layout="centered")
- 체크된 아이템은 취소선 + 회색으로 표시 (st.markdown에 ~~텍스트~~ 또는 CSS 사용)
- 각 행은 st.columns로 [체크박스 | 이름(수량) | 수정 | 삭제] 정렬, 버튼은 아이콘(✏️, 🗑️)으로 간결하게
- 미완료 아이템을 위에, 완료된 아이템을 아래에 정렬
- 아이템 행 사이에 얇은 구분선 또는 카드 형태로 구분
- [전체 삭제]는 실수 방지를 위해 확인 단계(한 번 더 누르기 또는 확인 체크) 추가
- 모든 아이템을 체크하면 st.success("모두 구매 완료! 🎉") 표시
- 모바일 화면(폭 375px)에서도 버튼이 줄바꿈되거나 깨지지 않게
- 커스텀 CSS는 st.markdown(unsafe_allow_html=True)로 한 곳에 모아서 관리

[조건]
- 2단계 기능이 하나도 깨지면 안 돼
- 변경 후 실행해서 화면이 정상인지 확인해줘
```

---

## 4단계: Playwright로 검증

```
Playwright를 사용해서 쇼핑 리스트 앱이 PRD 9장 완료 기준을 만족하는지 검증해줘.

[준비]
- requirements-dev.txt에 pytest, pytest-playwright 추가 후 설치
- playwright install chromium 실행
- 테스트는 tests/test_app.py에 작성
- 테스트 시작 전 data/shopping_list.json을 백업하고 비운 뒤, 끝나면 복원
- 테스트용 Streamlit 서버를 pytest fixture에서 백그라운드로 띄우고(포트 8599, --server.headless true), 끝나면 종료

[테스트 시나리오] (PRD 9장 기준)
1. 아이템 "우유", 수량 2 추가 → 리스트에 "우유 (2)" 표시
2. 공백만 입력하고 추가 → 경고 메시지 표시, 아이템 수 변화 없음
3. "우유"를 "두유"로 수정 후 저장 → "두유" 표시, "우유" 없음
4. 아이템 체크 → 진행 현황이 "1 / 1 구매 완료"로 갱신
5. 아이템 삭제 → 리스트에서 사라짐
6. 아이템 추가 후 페이지 새로고침 → 아이템이 그대로 남아 있음
7. 모바일 뷰포트(375x812)에서 주요 버튼이 화면 안에 보이는지 확인

[조건]
- Streamlit은 비동기로 다시 그려지므로 고정 sleep 대신 expect(...).to_be_visible() 같은 대기 방식 사용
- 각 시나리오 후 스크린샷을 tests/screenshots/에 저장
- pytest 실행 결과를 보여주고, 실패한 테스트가 있으면 원인을 찾아 앱 코드를 고친 뒤 다시 실행해줘
- 마지막에 통과/실패 요약표를 정리해줘
```

---

## (참고) 5단계: 배포

```
PRD 7.3에 맞춰 Streamlit Community Cloud 배포를 준비해줘.
- .gitignore 작성 (data/*.json, __pycache__, tests/screenshots 등)
- git init 후 첫 커밋
- GitHub 저장소 push와 share.streamlit.io 배포 절차를 단계별로 안내해줘
```
