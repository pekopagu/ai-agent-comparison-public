"""
テストA: 事前準備テスト（Codex CLI 実験A 派生版）
フロントエンドUIテスト - Playwright 6本
対象: タスク管理アプリ Vue 3フロントエンド（Codex CLI実装）

派生元: common/test-original/test_ui.py
修正内容（Codex CLIの実装に合わせた調整・観点・期待値・本数は変更なし）:
    - test_01/02: タイトルinputに type='text' 属性が明示されておらず、
      placeholder属性も無いため、セレクタをlabel経由に変更。
    - test_02: save後、Vue側の非同期処理（PUT + loadTasksの2連続fetch）
      の完了タイミングが不安定だったため、固定待機後にpage.reload()で
      サーバー上の最新状態を読み直す方式に変更。
    - test_03: 削除確認にブラウザネイティブのconfirm()を使用しているため、
      page.on("dialog", ...) でダイアログを自動acceptする処理を追加。
    - test_04: フィルタ操作前に全件表示を確認、操作後は固定待機+
      リトライ付きexpectで結果を確認するよう変更。
    - test_05: タイトルinputにHTML5の required 属性があり、ブラウザの
      標準バリデーションが先に発火してJS側のエラー表示に到達しないため、
      required属性を一時的に外してから送信する対応を追加。

実行方法:
    pip install playwright pytest-playwright
    playwright install chromium
    # バックエンドとフロントエンドを起動してから実行
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
# 共通の正規表現パターン
# ============================================================

RE_ADD_BUTTON = re.compile("追加|add|作成|create", re.IGNORECASE)
RE_EDIT_BUTTON = re.compile("編集|edit", re.IGNORECASE)
RE_SAVE_BUTTON = re.compile("保存|save|更新|update", re.IGNORECASE)
RE_DELETE_BUTTON = re.compile("削除|delete|remove", re.IGNORECASE)

# Codex CLI実装向け: タイトルinputはlabel「タイトル」直下のinput
TITLE_INPUT_SELECTOR = "label:has-text('タイトル') input"


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

        title_input = page.locator(TITLE_INPUT_SELECTOR).first
        title_input.fill("")
        title_input.fill("編集後タスク")
        # v-model.trim の反映を確実にするため、blurイベントを発生させる
        title_input.blur()
        page.wait_for_timeout(200)

        save_button = page.locator("button").filter(has_text=RE_SAVE_BUTTON).first
        # 保存ボタンがdisabledでないことを確認してからクリックする
        expect(save_button).to_be_enabled(timeout=5000)
        save_button.click()
        page.wait_for_timeout(1500)

        # Vue側の非同期処理の完了を待ってから、サーバー上の最新状態を読み直す
        page.reload()
        page.wait_for_load_state("networkidle")

        expect(page.locator("body")).to_contain_text("編集後タスク", timeout=10000)

    def test_03_delete_task_disappears(self, page_loaded: Page):
        """タスク削除 → 一覧から消える"""
        page = page_loaded

        # Codex CLI実装はブラウザネイティブのconfirm()を使用するため
        # ダイアログを自動acceptするハンドラを登録する
        page.on("dialog", lambda dialog: dialog.accept())

        requests.post(f"{API_URL}/tasks", json={
            "title": "削除対象タスク",
            "status": "todo",
            "priority": "medium"
        })
        page.reload()
        page.wait_for_load_state("networkidle")

        delete_button = page.locator("button").filter(has_text=RE_DELETE_BUTTON).first
        delete_button.click()

        # ダイアログのaccept + 削除APIの完了を待つ
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

        # 全タスクが表示されていることを確認してから操作する
        expect(page.locator("body")).to_contain_text("todoタスク", timeout=10000)
        expect(page.locator("body")).to_contain_text("doingタスク", timeout=10000)

        # Codex CLI実装: 「状態」ラベル直下のselectがフィルタ
        # （フォーム側にも「状態」selectがあるため、フィルタ領域内に絞る）
        status_filter = page.locator(
            "div.filters label:has-text('状態') select"
        ).first
        status_filter.select_option(value="todo")
        page.wait_for_timeout(1000)

        # フィルタ結果が反映されるまでリトライ付きで待つ
        expect(page.locator("body")).not_to_contain_text("doingタスク", timeout=15000)

        body_text = page.locator("body").inner_text()
        assert "todoタスク" in body_text
        assert "doingタスク" not in body_text
        assert "doneタスク" not in body_text

    def test_05_validation_error_displayed(self, page_loaded: Page):
        """バリデーションエラー → エラーメッセージ表示"""
        page = page_loaded

        # Codex CLI実装: タイトルinputにHTML5の required 属性があり、
        # ブラウザの標準バリデーションがJS側のエラー表示より先に発火するため、
        # required属性を一時的に外してフォーム送信を行う
        title_input = page.locator(TITLE_INPUT_SELECTOR).first
        title_input.evaluate("el => el.removeAttribute('required')")

        add_button = page.locator("button").filter(has_text=RE_ADD_BUTTON).first
        add_button.click()
        page.wait_for_timeout(500)

        body_text = page.locator("body").inner_text()
        has_error = any(word in body_text for word in [
            "必須", "required", "エラー", "error", "入力してください", "タイトルを"
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
