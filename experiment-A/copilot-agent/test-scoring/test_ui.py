"""
テストA: 事前準備テスト（Copilot Agent 実験A 派生版）
フロントエンドUIテスト - Playwright 6本
対象: タスク管理アプリ Vue 3フロントエンド（Copilot Agent実装）

派生元: common/test-original/test_ui.py
修正内容（Copilot Agentの実装に合わせた調整・観点・期待値・本数は変更なし）:
    - test_01: 追加ボタンのラベルは「追加する」。タイトルinputは
      ページ上部の常設フォーム内にtype="text"で配置されている
      （モーダルではない）。
    - test_02【根本原因】: 編集はモーダル形式。「編集」ボタンで
      モーダルを開き、モーダル内の「保存する」ボタンで確定する。
      保存ボタンの正規表現に「保存」を含める。
    - test_03【根本原因】: 削除確認がブラウザネイティブのconfirm()
      ではなく、カスタムUIモーダル（これまでの全エージェントと
      異なる唯一の実装）。「削除」ボタンクリック後に表示される
      確認モーダル内の「削除する」ボタンをクリックする2段階操作
      に変更。page.on("dialog", ...)は不要。
    - test_04: フィルタ用selectは.toolbar内に配置され、
      @change="fetchTasks"属性で識別できる。
    - test_05: タイトルinputにHTML5の required 属性は無く、JS側の
      バリデーション（trim()チェック）のみのため、追加の対応は不要。

実行方法:
    pip install playwright pytest-playwright
    playwright install chromium
    pytest test_ui.py -v
"""

import re
import pytest
from playwright.sync_api import Page, expect
from datetime import date, timedelta
import requests

BASE_URL = "http://localhost:3000"
API_URL = "http://localhost:8000"


# ============================================================
# フィクスチャ
# ============================================================

@pytest.fixture(autouse=True)
def cleanup_api():
    """各テスト前後にAPIデータをクリーンアップ"""
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
    """アプリを開いてロード完了まで待機"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    return page


# ============================================================
# 共通の正規表現パターン・セレクタ
# ============================================================

RE_ADD_BUTTON = re.compile("追加する|追加|add|作成|create", re.IGNORECASE)
RE_EDIT_BUTTON = re.compile("編集|edit", re.IGNORECASE)
RE_SAVE_BUTTON = re.compile("保存する|保存|save", re.IGNORECASE)
RE_DELETE_BUTTON = re.compile("削除|delete|remove", re.IGNORECASE)
RE_DELETE_CONFIRM_BUTTON = re.compile("削除する", re.IGNORECASE)
TITLE_INPUT_SELECTOR = "input[type='text']"
FILTER_SELECT_SELECTOR = ".toolbar select"


# ============================================================
# UIテスト（6本）
# ============================================================

class TestUI:

    def test_01_add_task_appears_in_list(self, page_loaded: Page):
        """タスク追加 → 一覧に表示される"""
        page = page_loaded
        title = "UIテスト用タスク"

        title_input = page.locator(TITLE_INPUT_SELECTOR).first
        title_input.fill(title)

        add_button = page.locator("button").filter(has_text=RE_ADD_BUTTON).first
        add_button.click()

        page.wait_for_load_state("networkidle")
        expect(page.locator("body")).to_contain_text(title)

    def test_02_edit_task_reflects_change(self, page_loaded: Page):
        """タスク編集 → 変更が反映される"""
        page = page_loaded

        requests.post(f"{API_URL}/tasks", json={
            "title": "編集前タスク",
            "status": "todo",
            "priority": "medium"
        })
        page.reload()
        page.wait_for_load_state("networkidle")

        edit_button = page.locator("button").filter(has_text=RE_EDIT_BUTTON).first
        edit_button.click()
        page.wait_for_timeout(300)

        # 編集モーダル内のタイトル入力欄
        modal_title_input = page.locator(".modal " + TITLE_INPUT_SELECTOR).first
        modal_title_input.fill("")
        modal_title_input.fill("編集後タスク")

        save_button = page.locator(".modal button").filter(has_text=RE_SAVE_BUTTON).first
        save_button.click()
        page.wait_for_load_state("networkidle")

        expect(page.locator("body")).to_contain_text("編集後タスク")

    def test_03_delete_task_disappears(self, page_loaded: Page):
        """タスク削除 → 一覧から消える"""
        page = page_loaded

        requests.post(f"{API_URL}/tasks", json={
            "title": "削除対象タスク",
            "status": "todo",
            "priority": "medium"
        })
        page.reload()
        page.wait_for_load_state("networkidle")

        # Copilot Agent実装はカスタムUIモーダルでの削除確認
        # （ブラウザネイティブのconfirm()ではない）
        delete_button = page.locator("button").filter(has_text=RE_DELETE_BUTTON).first
        delete_button.click()
        page.wait_for_timeout(300)

        # 確認モーダル内の「削除する」ボタンをクリック
        confirm_button = page.locator(".modal button").filter(has_text=RE_DELETE_CONFIRM_BUTTON).first
        confirm_button.click()

        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(300)

        expect(page.locator("body")).not_to_contain_text("削除対象タスク")

    def test_04_filter_narrows_list(self, page_loaded: Page):
        """フィルタ操作 → 絞り込まれる"""
        page = page_loaded

        requests.post(f"{API_URL}/tasks", json={"title": "todoタスク", "status": "todo", "priority": "medium"})
        requests.post(f"{API_URL}/tasks", json={"title": "doingタスク", "status": "doing", "priority": "medium"})
        requests.post(f"{API_URL}/tasks", json={"title": "doneタスク", "status": "done", "priority": "medium"})
        page.reload()
        page.wait_for_load_state("networkidle")

        expect(page.locator("body")).to_contain_text("todoタスク", timeout=10000)
        expect(page.locator("body")).to_contain_text("doingタスク", timeout=10000)

        # Copilot Agent実装: フィルタ用selectは.toolbar内の最初の要素（ステータス）
        status_filter = page.locator(FILTER_SELECT_SELECTOR).first
        status_filter.select_option(value="todo")
        page.wait_for_timeout(1000)

        expect(page.locator("body")).not_to_contain_text("doingタスク", timeout=15000)

        body_text = page.locator("body").inner_text()
        assert "todoタスク" in body_text
        assert "doingタスク" not in body_text
        assert "doneタスク" not in body_text

    def test_05_validation_error_displayed(self, page_loaded: Page):
        """バリデーションエラー → エラーメッセージ表示"""
        page = page_loaded

        add_button = page.locator("button").filter(has_text=RE_ADD_BUTTON).first
        add_button.click()
        page.wait_for_timeout(500)

        body_text = page.locator("body").inner_text()
        has_error = any(word in body_text for word in [
            "必須", "required", "エラー", "error", "入力してください", "タイトルは"
        ])
        assert has_error, "バリデーションエラーメッセージが表示されていません"

    def test_06_overdue_warning_displayed(self, page_loaded: Page):
        """期限切れタスク → 警告表示される"""
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

        body_text = page.locator("body").inner_text()
        assert "期限切れタスク" in body_text
        assert "期限切れ" in body_text

        warning_selectors = [
            "[class*='overdue']",
            ".badge-overdue",
            "[class*='danger']",
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
