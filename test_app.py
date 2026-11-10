"""PRD 9장 완료 기준 검증 (Playwright E2E)."""

import re

from playwright.sync_api import Page, expect


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------
def add(page: Page, name: str, qty: int | None = None) -> None:
    page.locator(".st-key-new_name input").fill(name)
    if qty is not None:
        page.locator(".st-key-new_qty input").fill(str(qty))
    page.get_by_role("button", name="추가").click()


def row(page: Page, text: str):
    return page.locator('[class*="st-key-row_"]').filter(has_text=text)


def checkboxes(page: Page):
    return page.get_by_role("checkbox")


# ---------------------------------------------------------------------------
# 시나리오
# ---------------------------------------------------------------------------
def test_1_add_item(app: Page):
    """아이템 이름을 입력하고 추가하면 리스트에 표시된다."""
    add(app, "우유", 2)
    expect(app.get_by_text("우유 (2)")).to_be_visible()
    expect(app.locator(".st-key-new_name input")).to_have_value("")
    expect(app.get_by_text("0 / 1 구매 완료")).to_be_visible()


def test_2_blank_name_rejected(app: Page):
    """빈 이름은 추가되지 않고 경고가 표시된다."""
    add(app, "우유")
    expect(checkboxes(app)).to_have_count(1)
    add(app, "   ")
    expect(app.get_by_text("아이템 이름을 입력해 주세요.")).to_be_visible()
    expect(checkboxes(app)).to_have_count(1)


def test_3_edit_item(app: Page):
    """아이템 이름·수량을 수정하고 저장하면 즉시 반영된다."""
    add(app, "우유", 2)
    expect(app.get_by_text("우유 (2)")).to_be_visible()
    row(app, "우유").locator('[class*="st-key-edit_"] button:visible').click()

    name_input = app.locator('[class*="st-key-edit_name_"] input')
    expect(name_input).to_have_value("우유")
    # 빈 이름은 저장 불가
    name_input.fill("")
    app.get_by_role("button", name="저장").click()
    expect(app.get_by_text("빈 이름으로는 저장할 수 없어요.")).to_be_visible()

    name_input.fill("두유")
    app.locator('[class*="st-key-edit_qty_"] input').fill("3")
    app.get_by_role("button", name="저장").click()
    expect(app.get_by_text("두유 (3)")).to_be_visible()
    expect(app.get_by_text("우유 (2)")).to_have_count(0)


def test_4_check_item(app: Page):
    """체크박스로 구매 완료 상태를 전환하고 진행 현황이 갱신된다."""
    add(app, "우유")
    expect(app.get_by_text("0 / 1 구매 완료")).to_be_visible()
    app.get_by_text("우유 (1)").click()
    expect(app.get_by_text("1 / 1 구매 완료")).to_be_visible()
    expect(app.get_by_text("모두 구매 완료! 🎉")).to_be_visible()
    expect(row(app, "우유").locator("del, s")).to_have_count(1)  # 취소선
    # 다시 해제
    app.get_by_text("우유 (1)").click()
    expect(app.get_by_text("0 / 1 구매 완료")).to_be_visible()


def test_5_delete_item(app: Page):
    """아이템을 삭제하면 리스트에서 사라진다."""
    add(app, "우유")
    add(app, "계란")
    expect(checkboxes(app)).to_have_count(2)
    row(app, "우유").locator('[class*="st-key-del_"] button:visible').click()
    expect(app.get_by_text("우유 (1)")).to_have_count(0)
    # 다시 그리는 동안 이전 행이 잠깐 남아 있을 수 있어 개수가 1이 될 때까지 대기
    expect(app.get_by_text("계란 (1)")).to_have_count(1)

    # 전체 삭제는 확인 후에만 동작
    app.get_by_role("button", name="전체 삭제").click()
    expect(app.get_by_text(re.compile("정말 아이템 1개를"))).to_be_visible()
    app.get_by_role("button", name="모두 삭제").click()
    expect(app.get_by_text("쇼핑 리스트가 비어 있어요")).to_be_visible()


def test_6_persist_after_reload(app: Page):
    """페이지를 새로고침해도 리스트가 유지된다."""
    add(app, "우유", 2)
    add(app, "계란")
    expect(checkboxes(app)).to_have_count(2)
    app.get_by_text("우유 (2)").click()
    expect(app.get_by_text("1 / 2 구매 완료")).to_be_visible()

    app.reload()
    expect(app.get_by_text("계란 (1)")).to_be_visible()
    expect(app.get_by_role("checkbox", name="우유 (2)")).to_be_checked()
    expect(app.get_by_text("1 / 2 구매 완료")).to_be_visible()


def test_7_mobile_layout(app: Page):
    """모바일 뷰포트(375x812)에서 주요 버튼이 화면 안에 보인다."""
    app.set_viewport_size({"width": 375, "height": 812})
    add(app, "크리스피 크림 오리지널 도넛 대용량 박스")
    add(app, "우유")
    expect(checkboxes(app)).to_have_count(2)

    buttons = [
        app.get_by_role("button", name="추가"),
        app.locator('[class*="st-key-edit_"] button:visible').first,
        app.locator('[class*="st-key-del_"] button:visible').first,
        app.get_by_role("button", name="체크된 항목 삭제"),
        app.get_by_role("button", name="전체 삭제"),
    ]
    for btn in buttons:
        expect(btn).to_be_visible()
        box = btn.bounding_box()
        assert box is not None
        assert box["x"] >= 0 and box["x"] + box["width"] <= 375, f"화면 밖: {box}"

    # 아이템 행이 세로로 쌓이지 않고 체크박스·버튼이 한 줄에 있는지
    r = row(app, "우유")
    check_y = r.get_by_role("checkbox").bounding_box()["y"]
    del_box = r.locator('[class*="st-key-del_"] button:visible').bounding_box()
    assert abs(check_y - del_box["y"]) < del_box["height"], "아이템 행이 줄바꿈됨"

    # 가로 스크롤 없음
    assert app.evaluate("document.documentElement.scrollWidth") <= 375


def test_8_two_tabs_do_not_overwrite(app: Page):
    """두 탭(또는 두 사용자)이 동시에 써도 서로의 변경을 덮어쓰지 않는다."""
    other = app.context.new_page()
    other.goto(app.url)
    expect(other.get_by_text("쇼핑 리스트가 비어 있어요")).to_be_visible()

    add(app, "우유")
    expect(app.get_by_text("우유 (1)")).to_be_visible()
    add(other, "계란")
    expect(other.get_by_text("계란 (1)")).to_be_visible()
    # 다른 탭에서 추가한 아이템도 보여야 한다
    expect(other.get_by_text("우유 (1)")).to_be_visible()

    app.reload()
    expect(app.get_by_text("우유 (1)")).to_be_visible()
    expect(app.get_by_text("계란 (1)")).to_be_visible()

    # 다른 탭에서 체크한 상태도 반영된다
    other.get_by_text("우유 (1)").click()
    expect(other.get_by_role("checkbox", name="우유 (1)")).to_be_checked()
    add(app, "사과")
    expect(app.get_by_text("사과 (1)")).to_be_visible()
    expect(app.get_by_role("checkbox", name="우유 (1)")).to_be_checked()
    expect(app.get_by_text("1 / 3 구매 완료")).to_be_visible()
    other.close()
