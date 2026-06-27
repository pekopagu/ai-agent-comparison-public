"""
テストA: 事前準備テスト（target-5）
フロントエンドUIテスト - Playwright 6本
対象: タスク管理アプリ Vue 3フロントエンド
"""

import re
import pytest
from playwright.sync_api import Page, expect
from datetime import date, timedelta
import requests

BASE_URL = "http://localhost:3000"
API_URL = "http://localhost:8000"


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
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)
    return page


RE_EDIT_BUTTON = re.compile("編集|edit", re.IGNORECASE)
RE_SAVE_BUTTON = re.compile("保存|save|更新|update|変更を保存", re.IGNORECASE)
RE_DELETE_BUTTON = re.compile("削除|delete|remove", re.IGNORECASE)
RE_TITLE_INPUT = "input#title, input[type='text'], input[placeholder*='タイトル'], input[placeholder*='title']"


def open_create_form(page: Page):
    create_button = page.locator("button.btn-create").first
    if create_button.count() > 0 and create_button.is_visible(timeout=500):
        create_button.click()
        page.wait_for_timeout(300)


def title_input(page: Page):
    return page.locator(RE_TITLE_INPUT).first


def submit_button(page: Page):
    return page.locator("form button[type='submit'], button.btn-submit").first


def edit_button(page: Page):
    titled = page.locator("button[title='編集'], button[aria-label='編集']").first
    if titled.count() > 0:
        return titled
    return page.locator("button").filter(has_text=RE_EDIT_BUTTON).first


def delete_button(page: Page):
    titled = page.locator("button[title='削除'], button[aria-label='削除']").first
    if titled.count() > 0:
        return titled
    return page.locator("button").filter(has_text=RE_DELETE_BUTTON).first


def status_filter(page: Page):
    return page.locator("select[v-model='statusFilter'], select[v-model='filters.status']").first


class TestUI:

    def test_01_add_task_appears_in_list(self, page_loaded: Page):
        page = page_loaded
        title = "UIテスト用タスク"

        open_create_form(page)
        title_input(page).fill(title)
        submit_button(page).click()

        page.wait_for_timeout(800)
        expect(page.locator("body")).to_contain_text(title)

    def test_02_edit_task_reflects_change(self, page_loaded: Page):
        page = page_loaded

        requests.post(f"{API_URL}/tasks", json={
            "title": "編集前タスク",
            "status": "todo",
            "priority": "medium"
        })
        page.reload()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(800)

        edit_button(page).click()
        page.wait_for_timeout(300)

        title_input(page).clear()
        title_input(page).fill("編集後タスク")

        save_button = page.locator("form button[type='submit'], button.btn-submit").filter(has_text=RE_SAVE_BUTTON).first
        if save_button.count() == 0:
            save_button = submit_button(page)
        save_button.click()
        page.wait_for_timeout(800)

        expect(page.locator("body")).to_contain_text("編集後タスク")

    def test_03_delete_task_disappears(self, page_loaded: Page):
        page = page_loaded

        requests.post(f"{API_URL}/tasks", json={
            "title": "削除対象タスク",
            "status": "todo",
            "priority": "medium"
        })
        page.reload()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(800)

        page.once("dialog", lambda dialog: dialog.accept())
        delete_button(page).click()
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

        status_filter(page).select_option(value="todo")
        page.wait_for_timeout(800)

        body_text = page.locator("body").inner_text()
        assert "todoタスク" in body_text
        assert "doingタスク" not in body_text or "doneタスク" not in body_text

    def test_05_validation_error_displayed(self, page_loaded: Page):
        page = page_loaded

        open_create_form(page)
        title_input(page).fill("   ")
        submit_button(page).click()
        page.wait_for_timeout(500)

        body_text = page.locator("body").inner_text()
        has_error = any(word in body_text for word in [
            "必須", "required", "エラー", "error", "入力してください", "タイトルを"
        ])
        assert has_error, "バリデーションエラーメッセージが表示されていません"

    def test_06_overdue_warning_displayed(self, page_loaded: Page):
        page = page_loaded

        yesterday = str(date.today() - timedelta(days=1))
        requests.post(f"{API_URL}/tasks", json={
            "title": "期限切れタスク",
            "status": "todo",
            "priority": "high",
            "due_date": yesterday
        })
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
            ".alert-banner",
        ]
        has_warning = False
        for selector in warning_selectors:
            try:
                elements = page.locator(selector)
                if elements.count() > 0:
                    has_warning = True
                    break
            except Exception:
                continue

        assert has_warning, "期限切れ警告スタイルが見つかりません"
