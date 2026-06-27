"""
target-1 UI に合わせた Playwright 6本。
"""

import re
import pytest
from playwright.sync_api import Page, expect
from datetime import date, timedelta
import requests

BASE_URL = "http://localhost:3000"
API_URL = "http://localhost:8000"

RE_ADD_BUTTON = re.compile("追加|add|作成|create|新規|新しい", re.IGNORECASE)
RE_EDIT_BUTTON = re.compile("編集|edit", re.IGNORECASE)
RE_SAVE_BUTTON = re.compile("保存|save|更新|update|追加", re.IGNORECASE)
RE_DELETE_BUTTON = re.compile("削除|delete|remove", re.IGNORECASE)
RE_CONFIRM_BUTTON = re.compile("OK|はい|confirm|削除する", re.IGNORECASE)
RE_TITLE_INPUT = "input[type='text'], input:not([type]), input[placeholder*='タイトル'], input[placeholder*='title']"


@pytest.fixture(autouse=True)
def cleanup_api():
    response = requests.get(f"{API_URL}/tasks")
    if response.status_code == 200:
        for task in response.json():
            requests.delete(f"{API_URL}/tasks/{task['id']}")
    yield
    response = requests.get(f"{API_URL}/tasks")
    if response.status_code == 200:
        for task in response.json():
            requests.delete(f"{API_URL}/tasks/{task['id']}")


@pytest.fixture
def page_loaded(page: Page):
    page.on("dialog", lambda dialog: dialog.accept())
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)
    return page


def open_create_form(page: Page):
    title_input = page.locator(RE_TITLE_INPUT).first
    try:
        if title_input.is_visible(timeout=500):
            return
    except Exception:
        pass
    page.locator("button").filter(has_text=RE_ADD_BUTTON).first.click()
    expect(page.locator(RE_TITLE_INPUT).first).to_be_visible(timeout=3000)


def title_input(page: Page):
    modal_input = page.locator(".modal, .modal-container").locator(RE_TITLE_INPUT).first
    try:
        if modal_input.is_visible(timeout=300):
            return modal_input
    except Exception:
        pass
    return page.locator(RE_TITLE_INPUT).first


def submit_visible_form(page: Page):
    modal_button = page.locator(".modal, .modal-container").locator("button[type='submit'], button").filter(has_text=RE_SAVE_BUTTON).first
    try:
        if modal_button.is_visible(timeout=300):
            modal_button.click()
            return
    except Exception:
        pass
    button = page.locator("form button[type='submit'], button.btn-submit").filter(has_text=RE_SAVE_BUTTON).first
    if button.count() == 0:
        button = page.locator("button").filter(has_text=RE_SAVE_BUTTON).first
    button.click()


def click_edit(page: Page):
    button = page.locator("button[title*='編集'], button[aria-label*='編集']").first
    if button.count() == 0:
        button = page.locator("button").filter(has_text=RE_EDIT_BUTTON).first
    button.click()
    expect(page.locator(RE_TITLE_INPUT).first).to_be_visible(timeout=3000)


def click_delete(page: Page):
    button = page.locator("button[title*='削除'], button[aria-label*='削除']").first
    if button.count() == 0:
        button = page.locator("button").filter(has_text=RE_DELETE_BUTTON).first
    button.click()
    page.wait_for_timeout(300)
    confirm = page.locator("button").filter(has_text=RE_CONFIRM_BUTTON).first
    try:
        if confirm.is_visible(timeout=1000):
            confirm.click()
    except Exception:
        pass


def select_status_filter(page: Page, value: str):
    page.evaluate(
        """value => {
            const selects = [...document.querySelectorAll('select')];
            const target = selects.find((select) => {
                const values = [...select.options].map((option) => option.value);
                return values.includes(value) && (values.includes('') || values.includes('all'));
            });
            if (!target) throw new Error('status filter select not found');
            target.value = value;
            target.dispatchEvent(new Event('change', { bubbles: true }));
        }""",
        value,
    )


class TestUI:
    def test_01_add_task_appears_in_list(self, page_loaded: Page):
        page = page_loaded
        title = "UIテスト用タスク"
        open_create_form(page)
        title_input(page).fill(title)
        submit_visible_form(page)
        page.wait_for_timeout(800)
        expect(page.locator("body")).to_contain_text(title)

    def test_02_edit_task_reflects_change(self, page_loaded: Page):
        page = page_loaded
        requests.post(f"{API_URL}/tasks", json={"title": "編集前タスク", "status": "todo", "priority": "medium"})
        page.reload()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(800)
        click_edit(page)
        field = title_input(page)
        field.clear()
        field.fill("編集後タスク")
        submit_visible_form(page)
        page.wait_for_timeout(800)
        expect(page.locator("body")).to_contain_text("編集後タスク")

    def test_03_delete_task_disappears(self, page_loaded: Page):
        page = page_loaded
        requests.post(f"{API_URL}/tasks", json={"title": "削除対象タスク", "status": "todo", "priority": "medium"})
        page.reload()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(800)
        click_delete(page)
        page.wait_for_timeout(800)
        expect(page.locator("body")).not_to_contain_text("削除対象タスク")

    def test_04_filter_narrows_list(self, page_loaded: Page):
        page = page_loaded
        requests.post(f"{API_URL}/tasks", json={"title": "todoタスク", "status": "todo", "priority": "medium"})
        requests.post(f"{API_URL}/tasks", json={"title": "doingタスク", "status": "doing", "priority": "medium"})
        requests.post(f"{API_URL}/tasks", json={"title": "doneタスク", "status": "done", "priority": "medium"})
        page.reload()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(800)
        select_status_filter(page, "todo")
        page.wait_for_timeout(800)
        body_text = page.locator("body").inner_text()
        assert "todoタスク" in body_text
        assert "doingタスク" not in body_text or "doneタスク" not in body_text

    def test_05_validation_error_displayed(self, page_loaded: Page):
        page = page_loaded
        open_create_form(page)
        page.locator(RE_TITLE_INPUT).first.evaluate("el => el.removeAttribute('required')")
        submit_visible_form(page)
        page.wait_for_timeout(500)
        body_text = page.locator("body").inner_text()
        has_error = any(word in body_text for word in ["必須", "required", "エラー", "error", "入力してください", "タイトルを"])
        assert has_error, "バリデーションエラーメッセージが表示されていません"

    def test_06_overdue_warning_displayed(self, page_loaded: Page):
        page = page_loaded
        yesterday = str(date.today() - timedelta(days=1))
        requests.post(f"{API_URL}/tasks", json={"title": "期限切れタスク", "status": "todo", "priority": "high", "due_date": yesterday})
        page.reload()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(800)
        body_text = page.locator("body").inner_text()
        assert "期限切れタスク" in body_text
        warning_selectors = [
            "[class*='overdue']",
            "[class*='expired']",
            "[class*='warning']",
            "[class*='danger']",
            "[class*='red']",
            "[style*='red']",
            "[style*='color: red']",
        ]
        has_warning = False
        for selector in warning_selectors:
            try:
                if page.locator(selector).count() > 0:
                    has_warning = True
                    break
            except Exception:
                continue
        assert has_warning, "期限切れ警告スタイルが見つかりません"
