"""
テストA: 事前準備テスト（共通）
フロントエンドUIテスト - Playwright 6本
対象: タスク管理アプリ Vue 3フロントエンド（target-6 / TaskFlow Pro）

実行方法:
    pip install playwright pytest-playwright
    playwright install chromium
    # バックエンドとフロントエンドを起動してから実行
    pytest tests/test_ui.py -v

target-6 向けの調整点（観点・期待値・本数は変更していない）:
    - タイトル入力欄は <input type="text" placeholder="タスクのタイトルを..."> のため、
      原本の RE_TITLE_INPUT がそのまま一致する。
    - 追加/保存ボタンは「追加する」「更新する」ラベルで原本の正規表現に一致。
    - 編集・削除ボタンは Font Awesome アイコンのみでテキストを持たないため、原本の
      テキスト一致（has_text）では取得できない。class（.edit-btn / .delete-btn）で
      取得するよう変更。
    - 削除は window.confirm() のネイティブダイアログのため、page.on("dialog", accept)
      でダイアログを受理する方式に変更。
    - フィルタ用セレクトとフォーム用セレクトが同じ class（select-control）を共有して
      いるため、`select` の先頭ではなくフィルタ領域（.controls-panel）内のセレクトを
      指定するよう変更。
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
    # テスト前クリーンアップ
    response = requests.get(f"{API_URL}/tasks")
    if response.status_code == 200:
        for task in response.json():
            requests.delete(f"{API_URL}/tasks/{task['id']}")
    yield
    # テスト後クリーンアップ
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
# 共通の正規表現パターン／セレクタ
# ============================================================

RE_ADD_BUTTON = re.compile("追加|add|作成|create", re.IGNORECASE)
RE_SAVE_BUTTON = re.compile("保存|save|更新|update", re.IGNORECASE)
# target-6 のタイトル入力欄（type=text + placeholder）
RE_TITLE_INPUT = "input[type='text'], input[placeholder*='タイトル'], input[placeholder*='title']"
# target-6 の編集・削除はアイコンボタン（テキストなし）→ class で取得
EDIT_BUTTON = ".edit-btn"
DELETE_BUTTON = ".delete-btn"
# target-6 のフィルタ用 status セレクト（.controls-panel 内の先頭セレクト）
FILTER_STATUS_SELECT = ".controls-panel select"


# ============================================================
# UIテスト（6本）
# ============================================================

class TestUI:

    def test_01_add_task_appears_in_list(self, page_loaded: Page):
        """タスク追加 → 一覧に表示される"""
        page = page_loaded
        title = "UIテスト用タスク"

        # タイトル入力
        title_input = page.locator(RE_TITLE_INPUT).first
        title_input.fill(title)

        # 追加ボタンクリック
        add_button = page.locator("button").filter(has_text=RE_ADD_BUTTON).first
        add_button.click()

        # 一覧に表示されることを確認
        page.wait_for_timeout(500)
        expect(page.locator("body")).to_contain_text(title)

    def test_02_edit_task_reflects_change(self, page_loaded: Page):
        """タスク編集 → 変更が反映される"""
        page = page_loaded

        # APIでタスクを事前作成
        requests.post(f"{API_URL}/tasks", json={
            "title": "編集前タスク",
            "status": "todo",
            "priority": "medium"
        })
        page.reload()
        page.wait_for_load_state("networkidle")

        # 編集ボタン（アイコン）をクリック
        edit_button = page.locator(EDIT_BUTTON).first
        edit_button.click()
        page.wait_for_timeout(300)

        # タイトルを変更
        title_input = page.locator(RE_TITLE_INPUT).first
        title_input.clear()
        title_input.fill("編集後タスク")

        # 保存ボタンをクリック（「更新する」）
        save_button = page.locator("button").filter(has_text=RE_SAVE_BUTTON).first
        save_button.click()
        page.wait_for_timeout(500)

        # 変更が反映されていることを確認
        expect(page.locator("body")).to_contain_text("編集後タスク")

    def test_03_delete_task_disappears(self, page_loaded: Page):
        """タスク削除 → 一覧から消える"""
        page = page_loaded

        # 削除確認は window.confirm() のため、ダイアログを受理する
        page.on("dialog", lambda dialog: dialog.accept())

        # APIでタスクを事前作成
        requests.post(f"{API_URL}/tasks", json={
            "title": "削除対象タスク",
            "status": "todo",
            "priority": "medium"
        })
        page.reload()
        page.wait_for_load_state("networkidle")

        # 削除ボタン（アイコン）をクリック（confirmは上のハンドラで自動受理）
        delete_button = page.locator(DELETE_BUTTON).first
        delete_button.click()
        page.wait_for_timeout(500)

        # タスクが消えていることを確認
        expect(page.locator("body")).not_to_contain_text("削除対象タスク")

    def test_04_filter_narrows_list(self, page_loaded: Page):
        """フィルタ操作 → 絞り込まれる"""
        page = page_loaded

        # APIで複数タスクを作成
        requests.post(f"{API_URL}/tasks", json={"title": "todoタスク", "status": "todo", "priority": "medium"})
        requests.post(f"{API_URL}/tasks", json={"title": "doingタスク", "status": "doing", "priority": "medium"})
        requests.post(f"{API_URL}/tasks", json={"title": "doneタスク", "status": "done", "priority": "medium"})
        page.reload()
        page.wait_for_load_state("networkidle")

        # statusフィルタをtodoに設定（.controls-panel 内の status セレクト）
        status_filter = page.locator(FILTER_STATUS_SELECT).first
        try:
            if status_filter.is_visible(timeout=2000):
                # 値が "todo" の<option>があれば選択する
                status_filter.select_option(value="todo")
        except Exception:
            pass

        page.wait_for_timeout(500)

        # todoタスクのみ表示されていることを確認
        body_text = page.locator("body").inner_text()
        assert "todoタスク" in body_text
        assert "doingタスク" not in body_text or "doneタスク" not in body_text

    def test_05_validation_error_displayed(self, page_loaded: Page):
        """バリデーションエラー → エラーメッセージ表示"""
        page = page_loaded

        # タイトルを空のまま追加ボタンをクリック
        add_button = page.locator("button").filter(has_text=RE_ADD_BUTTON).first
        add_button.click()
        page.wait_for_timeout(500)

        # エラーメッセージが表示されることを確認
        body_text = page.locator("body").inner_text()
        has_error = any(word in body_text for word in [
            "必須", "required", "エラー", "error", "入力してください", "タイトルを"
        ])
        assert has_error, "バリデーションエラーメッセージが表示されていません"

    def test_06_overdue_warning_displayed(self, page_loaded: Page):
        """期限切れタスク → 警告表示される"""
        page = page_loaded

        # 期限切れのタスクをAPIで作成
        yesterday = str(date.today() - timedelta(days=1))
        requests.post(f"{API_URL}/tasks", json={
            "title": "期限切れタスク",
            "status": "todo",
            "priority": "high",
            "due_date": yesterday
        })
        page.reload()
        page.wait_for_load_state("networkidle")

        # 警告表示を確認（色・アイコン・テキスト等）
        body_text = page.locator("body").inner_text()
        assert "期限切れタスク" in body_text

        # 警告スタイルの要素が存在するか確認
        # （実装によって警告の表現が異なるため、複数パターンで確認）
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
                elements = page.locator(selector)
                if elements.count() > 0:
                    has_warning = True
                    break
            except Exception:
                continue

        assert has_warning, "期限切れ警告スタイルが見つかりません"
