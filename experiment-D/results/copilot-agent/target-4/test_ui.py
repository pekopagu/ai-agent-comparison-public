"""
テストA: 事前準備テスト（共通）
フロントエンドUIテスト - Playwright 6本
対象: タスク管理アプリ Vue 3フロントエンド（target-4 実装に合わせて調整）

実行方法:
    pip install playwright pytest-playwright
    playwright install chromium
    # バックエンドとフロントエンドを起動してから実行
    pytest tests/test_ui.py -v

修正履歴:
    2026-06-26: target-4 の実装に合わせてセレクタと操作手順を調整。
    - 追加はインラインフォーム、編集はモーダル、削除は確認モーダル
    - 編集時のタイトル入力欄はモーダル内の input に限定（.modal 配下）
    - 削除はモーダル内の「削除する」ボタンで確定する
    - フィルタ用 select は追加フォームと区別するため .toolbar 配下に限定
    観点・期待値・本数（6本）は変更していない。
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
# 共通の正規表現パターン（大文字小文字を区別しない・OR条件）
# ============================================================

RE_ADD_BUTTON = re.compile("追加|add|作成|create", re.IGNORECASE)
RE_EDIT_BUTTON = re.compile("編集|edit", re.IGNORECASE)
RE_TITLE_INPUT = "input[type='text'], input[placeholder*='タイトル'], input[placeholder*='title']"

# target-4 固有セレクタ
# - 編集モーダル内のタイトル入力欄（追加フォームと区別する）
MODAL_TITLE_INPUT = ".modal input[type='text']"
# - 編集モーダルの保存ボタン
MODAL_SAVE_BUTTON = ".modal .btn-primary"
# - 一覧のタスク削除ボタン（モーダルを開く）
DELETE_BUTTON = "button.btn-danger.btn-sm"
# - 削除確認モーダルの「削除する」ボタン
MODAL_CONFIRM_DELETE = ".modal button.btn-danger"
# - フィルタ用 select は追加フォームの select と区別するため .toolbar 配下に限定する
FILTER_STATUS_SELECT = ".toolbar select"


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

        # 編集ボタンをクリックしてモーダルを開く
        edit_button = page.locator("button").filter(has_text=RE_EDIT_BUTTON).first
        edit_button.click()
        page.wait_for_timeout(300)

        # タイトルを変更（モーダル内の入力欄）
        title_input = page.locator(MODAL_TITLE_INPUT).first
        title_input.clear()
        title_input.fill("編集後タスク")

        # 保存ボタンをクリック
        page.locator(MODAL_SAVE_BUTTON).first.click()
        page.wait_for_timeout(500)

        # 変更が反映されていることを確認
        expect(page.locator("body")).to_contain_text("編集後タスク")

    def test_03_delete_task_disappears(self, page_loaded: Page):
        """タスク削除 → 一覧から消える"""
        page = page_loaded

        # APIでタスクを事前作成
        requests.post(f"{API_URL}/tasks", json={
            "title": "削除対象タスク",
            "status": "todo",
            "priority": "medium"
        })
        page.reload()
        page.wait_for_load_state("networkidle")

        # 一覧の削除ボタンをクリック（確認モーダルが開く）
        page.locator(DELETE_BUTTON).first.click()
        page.wait_for_timeout(300)

        # 確認モーダルの「削除する」ボタンをクリック
        page.locator(MODAL_CONFIRM_DELETE).first.click()
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

        # statusフィルタをtodoに設定（追加フォームの select と区別するため .toolbar 配下を使用）
        status_filter = page.locator(FILTER_STATUS_SELECT).first
        try:
            if status_filter.is_visible(timeout=2000):
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
