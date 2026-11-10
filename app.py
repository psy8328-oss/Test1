"""쇼핑 리스트 Streamlit 앱 (3단계: UI 디자인)."""

import re
import uuid
from datetime import datetime

import streamlit as st

import storage

st.set_page_config(page_title="쇼핑 리스트", page_icon="🛒", layout="centered")

MAX_NAME_LEN = 50

# ---------------------------------------------------------------------------
# 커스텀 CSS (스타일은 모두 여기서 관리)
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
/* 전체 폭을 좁혀 리스트 앱처럼 보이게 */
.block-container { max-width: 640px; padding-top: 2.5rem; }

/* 진행 현황 텍스트 */
.progress-label { display: flex; justify-content: space-between;
                  font-size: 0.95rem; margin-bottom: -0.5rem; }
.progress-label .count { font-weight: 600; }

/* 아이템 카드: 여백을 줄이고 행 높이를 균일하게 */
[class*="st-key-row_"] { padding: 0.35rem 0.75rem !important; gap: 0 !important; }
[class*="st-key-row_"] [data-testid="stCheckbox"] { min-height: 2.25rem;
                                                   display: flex; align-items: center; }
[class*="st-key-row_"] [data-testid="stCheckbox"] p { font-size: 1.05rem;
                                                     word-break: break-all; }

/* 아이콘 버튼은 작고 테두리 없이 */
[class*="st-key-edit_"] button, [class*="st-key-del_"] button {
    border: none; background: transparent; padding: 0.25rem; min-height: 2.25rem; }
[class*="st-key-edit_"] button:hover { background: rgba(128,128,128,0.15); }
[class*="st-key-del_"] button:hover { background: rgba(255,75,75,0.15); }

/* 모바일: 아이템 행·추가 폼의 컬럼이 세로로 쌓이지 않게 고정 */
@media (max-width: 640px) {
  .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 1.5rem; }
  [class*="st-key-row_"] [data-testid="stHorizontalBlock"],
  .st-key-add_row [data-testid="stHorizontalBlock"],
  .st-key-bulk_row [data-testid="stHorizontalBlock"] {
      flex-wrap: nowrap !important; gap: 0.4rem !important; }
  [class*="st-key-row_"] [data-testid="stColumn"],
  .st-key-add_row [data-testid="stColumn"],
  .st-key-bulk_row [data-testid="stColumn"] { min-width: 0 !important; }
  .st-key-add_row button, .st-key-bulk_row button {
      padding-left: 0.4rem; padding-right: 0.4rem; }
  .st-key-add_row button p, .st-key-bulk_row button p { white-space: nowrap; }
  /* 좁은 화면에서는 숫자 입력의 +/- 버튼 숨김 (직접 입력) */
  .st-key-add_row [data-testid="stNumberInputStepDown"],
  .st-key-add_row [data-testid="stNumberInputStepUp"],
  [class*="st-key-row_"] [data-testid="stNumberInputStepDown"],
  [class*="st-key-row_"] [data-testid="stNumberInputStepUp"] { display: none; }
}
</style>
"""

_MD_SPECIAL = re.compile(r"([\\`*_~\[\]()<>#+\-.!|:$])")


def md_escape(text: str) -> str:
    """사용자 입력이 마크다운으로 해석되지 않게 특수문자를 이스케이프한다."""
    return _MD_SPECIAL.sub(r"\\\1", text)

# ---------------------------------------------------------------------------
# 상태 초기화
# 아이템 목록은 세션에 캐시하지 않고 매번 파일에서 읽는다.
# (여러 탭/사용자가 같은 리스트를 쓸 때 서로의 변경을 덮어쓰지 않도록)
# ---------------------------------------------------------------------------
if "editing_id" not in st.session_state:
    st.session_state["editing_id"] = None


def _find(items: list[dict], item_id: str) -> dict | None:
    return next((i for i in items if i["id"] == item_id), None)


def _warn(message: str) -> None:
    """다음 렌더링 때 표시할 경고 메시지를 등록한다."""
    st.session_state["warning"] = message


# ---------------------------------------------------------------------------
# 아이템 조작 함수 (모두 최신 파일 기준으로 읽고-수정하고-저장)
# ---------------------------------------------------------------------------
def add_item(name: str, quantity: int = 1) -> bool:
    """새 아이템을 추가한다. 이름이 비어 있으면 False."""
    name = name.strip()
    if not name:
        return False
    with storage.transaction() as items:
        items.append(
            {
                "id": str(uuid.uuid4()),
                "name": name[:MAX_NAME_LEN],
                "quantity": max(1, int(quantity)),
                "checked": False,
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
    return True


def update_item(item_id: str, name: str, quantity: int) -> bool:
    """아이템의 이름과 수량을 수정한다. 이름이 비어 있으면 False."""
    name = name.strip()
    if not name:
        return False
    with storage.transaction() as items:
        item = _find(items, item_id)
        if item is None:  # 다른 곳에서 이미 삭제됨
            return True
        item["name"] = name[:MAX_NAME_LEN]
        item["quantity"] = max(1, int(quantity))
    return True


def delete_item(item_id: str) -> None:
    """아이템을 삭제한다."""
    with storage.transaction() as items:
        items[:] = [i for i in items if i["id"] != item_id]
    if st.session_state["editing_id"] == item_id:
        st.session_state["editing_id"] = None


def toggle_item(item_id: str) -> None:
    """체크박스에 표시된 값대로 구매 완료 상태를 저장한다.

    (단순 반전이 아니라 화면 값을 그대로 쓰므로, 다른 탭에서 먼저 바꿨어도
    사용자가 보고 누른 결과가 저장된다.)
    """
    checked = bool(st.session_state.get(f"check_{item_id}"))
    with storage.transaction() as items:
        item = _find(items, item_id)
        if item is not None:
            item["checked"] = checked


def delete_checked() -> None:
    """체크된 아이템을 모두 삭제한다."""
    with storage.transaction() as items:
        items[:] = [i for i in items if not i["checked"]]
    st.session_state["editing_id"] = None


def delete_all() -> None:
    """모든 아이템을 삭제한다."""
    with storage.transaction() as items:
        items.clear()
    st.session_state["editing_id"] = None


# ---------------------------------------------------------------------------
# 위젯 콜백 (스크립트가 다시 실행되기 전에 처리되어 화면이 즉시 반영됨)
# ---------------------------------------------------------------------------
def on_add() -> None:
    name = st.session_state["new_name"]
    quantity = st.session_state["new_qty"]
    if not add_item(name, quantity):
        _warn("아이템 이름을 입력해 주세요.")


def on_start_edit(item_id: str) -> None:
    item = _find(storage.load_items(), item_id)
    if item is None:
        return
    st.session_state["editing_id"] = item_id
    st.session_state[f"edit_name_{item_id}"] = item["name"]
    st.session_state[f"edit_qty_{item_id}"] = item["quantity"]


def on_save_edit(item_id: str) -> None:
    name = st.session_state[f"edit_name_{item_id}"]
    quantity = st.session_state[f"edit_qty_{item_id}"]
    if update_item(item_id, name, quantity):
        st.session_state["editing_id"] = None
    else:
        _warn("빈 이름으로는 저장할 수 없어요.")


def on_cancel_edit() -> None:
    st.session_state["editing_id"] = None


def on_ask_delete_all() -> None:
    st.session_state["confirm_delete_all"] = True


def on_confirm_delete_all() -> None:
    delete_all()
    st.session_state["confirm_delete_all"] = False


def on_cancel_delete_all() -> None:
    st.session_state["confirm_delete_all"] = False


# ---------------------------------------------------------------------------
# 화면
# ---------------------------------------------------------------------------
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.title("🛒 쇼핑 리스트")

items = storage.load_items()
total = len(items)
done = sum(1 for i in items if i["checked"])

# 진행 현황
if total:
    st.markdown(
        f'<div class="progress-label"><span>구매 진행률</span>'
        f'<span class="count">{done} / {total} 구매 완료</span></div>',
        unsafe_allow_html=True,
    )
    st.progress(done / total)
    if done == total:
        st.success("모두 구매 완료! 🎉")

# 아이템 추가
with st.form("add_form", clear_on_submit=True):
    with st.container(key="add_row"):
        col_name, col_qty, col_btn = st.columns([5, 1.6, 1.4],
                                                vertical_alignment="bottom")
        col_name.text_input("아이템 이름", key="new_name", max_chars=MAX_NAME_LEN,
                            placeholder="예: 우유")
        col_qty.number_input("수량", key="new_qty", min_value=1, value=1, step=1)
        col_btn.form_submit_button("추가", on_click=on_add, type="primary",
                                   width="stretch")

# 경고 메시지 (한 번만 표시)
if warning := st.session_state.pop("warning", None):
    st.warning(warning, icon="⚠️")

# 아이템 목록 (미완료 → 완료 순, 같은 그룹 안에서는 추가한 순서 유지)
if not items:
    st.info("쇼핑 리스트가 비어 있어요. 아이템을 추가해 보세요!", icon="📝")
else:
    for item in sorted(items, key=lambda i: i["checked"]):
        item_id = item["id"]

        with st.container(border=True, key=f"row_{item_id}"):
            if st.session_state["editing_id"] == item_id:
                # 편집 모드: form으로 묶어 이름·수량을 저장 시점에 한 번에 전송
                with st.form(f"edit_form_{item_id}", border=False):
                    c_name, c_qty = st.columns([5, 2], vertical_alignment="bottom")
                    c_name.text_input("이름", key=f"edit_name_{item_id}",
                                      max_chars=MAX_NAME_LEN)
                    c_qty.number_input("수량", key=f"edit_qty_{item_id}",
                                       min_value=1, step=1)
                    c_save, c_cancel = st.columns(2)
                    c_save.form_submit_button("저장", on_click=on_save_edit,
                                              args=(item_id,), type="primary",
                                              width="stretch")
                    c_cancel.form_submit_button("취소", on_click=on_cancel_edit,
                                                width="stretch")
            else:
                # 보기 모드: [체크박스+이름(수량) | ✏️ | 🗑️]
                label = f"{md_escape(item['name'])} ({item['quantity']})"
                if item["checked"]:
                    label = f":gray[~~{label}~~]"
                c_check, c_edit, c_del = st.columns([8, 1, 1],
                                                    vertical_alignment="center")
                # 다른 탭에서 바뀐 체크 상태도 반영되도록 파일 값으로 맞춘다
                st.session_state[f"check_{item_id}"] = item["checked"]
                c_check.checkbox(
                    label,
                    key=f"check_{item_id}",
                    on_change=toggle_item,
                    args=(item_id,),
                )
                c_edit.button("✏️", key=f"edit_{item_id}", help="수정",
                              on_click=on_start_edit, args=(item_id,),
                              width="stretch")
                c_del.button("🗑️", key=f"del_{item_id}", help="삭제",
                             on_click=delete_item, args=(item_id,),
                             width="stretch")

    # 일괄 삭제
    st.write("")
    if st.session_state.get("confirm_delete_all"):
        st.warning(f"정말 아이템 {total}개를 모두 삭제할까요? 되돌릴 수 없어요.",
                   icon="⚠️")
        b1, b2 = st.container(key="bulk_row").columns(2)
        b1.button("모두 삭제", on_click=on_confirm_delete_all, type="primary",
                  width="stretch")
        b2.button("취소", key="cancel_delete_all", on_click=on_cancel_delete_all,
                  width="stretch")
    else:
        b1, b2 = st.container(key="bulk_row").columns(2)
        b1.button("체크된 항목 삭제", on_click=delete_checked, disabled=done == 0,
                  width="stretch")
        b2.button("전체 삭제", on_click=on_ask_delete_all, width="stretch")
