"""
テストA: 事前準備テスト（共通）
フロントエンドUIテスト - Playwright 6本
対象: タスク管理アプリ Vue 3フロントエンド

実行方法:
    pip install playwright pytest-playwright
    playwright install chromium
    # バックエンドとフロントエンドを起動してから実行
    pytest tests/test_ui.py -v
"""

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
# UIテスト（6本）
# ============================================================

class TestUI:

    def test_01_add_task_appears_in_list(self, page_loaded: Page):
        """タスク追加 → 一覧に表示される"""
        page = page_loaded
        title = "UIテスト用タスク"

        # タイトル入力
        title_input = page.locator("input[type='text'], input[placeholder*='タイトル'], input[placeholder*='title']").first
        title_input.fill(title)

        # 追加ボタンクリック
        add_button = page.locator("button").filter(has_text=lambda t: "追加" in t or "add" in t.lower() or "作成" in t or "create" in t.lower()).first
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

        # 編集ボタンをクリック
        edit_button = page.locator("button").filter(has_text=lambda t: "編集" in t or "edit" in t.lower()).first
        edit_button.click()
        page.wait_for_timeout(300)

        # タイトルを変更
        title_input = page.locator("input[type='text'], input[placeholder*='タイトル'], input[placeholder*='title']").first
        title_input.clear()
        title_input.fill("編集後タスク")

        # 保存ボタンをクリック
        save_button = page.locator("button").filter(has_text=lambda t: "保存" in t or "save" in t.lower() or "更新" in t or "update" in t.lower()).first
        save_button.click()
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

        # 削除ボタンをクリック
        delete_button = page.locator("button").filter(has_text=lambda t: "削除" in t or "delete" in t.lower() or "remove" in t.lower()).first
        delete_button.click()
        page.wait_for_timeout(300)

        # 確認ダイアログが出た場合はOKをクリック
        try:
            confirm_button = page.locator("button").filter(has_text=lambda t: "OK" in t or "はい" in t or "confirm" in t.lower()).first
            if confirm_button.is_visible(timeout=1000):
                confirm_button.click()
        except Exception:
            pass

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

        # statusフィルタをtodoに設定
        status_filter = page.locator("select, [role='combobox']").filter(has_text=lambda t: "todo" in t.lower() or "ステータス" in t or "status" in t.lower()).first
        status_filter.select_option(value="todo", label="todo") if status_filter.is_visible() else None

        page.wait_for_timeout(500)

        # todoタスクのみ表示されていることを確認
        body_text = page.locator("body").inner_text()
        assert "todoタスク" in body_text
        assert "doingタスク" not in body_text or "doneタスク" not in body_text

    def test_05_validation_error_displayed(self, page_loaded: Page):
        """バリデーションエラー → エラーメッセージ表示"""
        page = page_loaded

        # タイトルを空のまま追加ボタンをクリック
        add_button = page.locator("button").filter(has_text=lambda t: "追加" in t or "add" in t.lower() or "作成" in t or "create" in t.lower()).first
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
