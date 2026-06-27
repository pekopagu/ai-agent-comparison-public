"""
テストA: 事前準備テスト（Antigravity IDE 実験A 派生版）
フロントエンドUIテスト - Playwright 6本
対象: タスク管理アプリ Vue 3フロントエンド（Antigravity IDE実装）

派生元: common/test-original/test_ui.py
修正内容（Antigravity IDEの実装に合わせた調整・観点・期待値・本数は変更なし）:
    - test_01【根本原因】: 「追加」を含むボタンが2つ存在する。
      ① ヘッダーの「タスクを追加」（モーダルを開くだけ）
      ② モーダル内の「タスクを追加」（実際の送信、type="submit"）
      .firstで①が誤って取得され、入力フォーム自体がまだ表示されて
      いない状態になる。先に①をクリックしてモーダルを開き、
      その後モーダル内のtype="text"inputに入力 → ②をクリックする
      2段階の操作に変更。
    - test_01/02: 新規・編集ともにモーダル形式のUI。タイトルinputは
      type="text"で明示されている。
    - test_02【根本原因】: 保存ボタンのラベルが編集時「変更を保存」、
      新規時「タスクを追加」であり、「保存|save|更新|update」のいずれ
      にも一部しか一致しない。type="submit"属性を持つボタンに絞る
      セレクタへ変更（モーダル内には他にtype="submit"のボタンがない
      ため安全）。
    - test_03: 削除確認にブラウザネイティブのconfirm()を使用している
      ため、page.on("dialog", ...) でダイアログを自動acceptする処理
      を追加。編集・削除ボタンはアイコンのみでtitle属性に
      ラベルがあるため、属性セレクタを使用（Antigravity CLIと同様）。
    - test_04: フィルタ用selectは.control-group内に配置されている。
      フォーム用select（モーダル内）とは別構造のため、モーダルが
      閉じている状態であれば .control-group select で一意に取得できる。

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

RE_OPEN_CREATE_MODAL = re.compile("タスクを追加", re.IGNORECASE)
EDIT_BUTTON_SELECTOR = "button[title='編集']"
DELETE_BUTTON_SELECTOR = "button[title='削除']"
TITLE_INPUT_SELECTOR = "input[type='text']"
# モーダル内のsubmitボタン（新規「タスクを追加」/編集「変更を保存」の両方を含む唯一のtype=submitボタン）
SUBMIT_BUTTON_SELECTOR = "button[type='submit']"
# フィルタ用select（モーダルが閉じている前提でページ全体から取得可能）
FILTER_STATUS_SELECT_SELECTOR = ".control-group select"


# ============================================================
# UIテスト（6本）
# ============================================================

class TestUI:

    def test_01_add_task_appears_in_list(self, page_loaded: Page):
        """タスク追加 → 一覧に表示される"""
        page = page_loaded
        title = "UIテスト用タスク"

        # ヘッダーの「タスクを追加」ボタンでモーダルを開く
        open_button = page.locator("button").filter(has_text=RE_OPEN_CREATE_MODAL).first
        open_button.click()
        page.wait_for_timeout(300)

        # モーダル内のタイトル入力欄に入力
        title_input = page.locator(TITLE_INPUT_SELECTOR).first
        title_input.fill(title)

        # モーダル内の送信ボタン（type="submit"）をクリック
        submit_button = page.locator(SUBMIT_BUTTON_SELECTOR).first
        submit_button.click()

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

        edit_button = page.locator(EDIT_BUTTON_SELECTOR).first
        edit_button.click()
        page.wait_for_timeout(300)

        title_input = page.locator(TITLE_INPUT_SELECTOR).first
        title_input.fill("")
        title_input.fill("編集後タスク")

        submit_button = page.locator(SUBMIT_BUTTON_SELECTOR).first
        submit_button.click()
        page.wait_for_load_state("networkidle")

        expect(page.locator("body")).to_contain_text("編集後タスク")

    def test_03_delete_task_disappears(self, page_loaded: Page):
        """タスク削除 → 一覧から消える"""
        page = page_loaded

        # Antigravity IDE実装はブラウザネイティブのconfirm()を使用するため
        # ダイアログを自動acceptするハンドラを登録する
        page.on("dialog", lambda dialog: dialog.accept())

        requests.post(f"{API_URL}/tasks", json={
            "title": "削除対象タスク",
            "status": "todo",
            "priority": "medium"
        })
        page.reload()
        page.wait_for_load_state("networkidle")

        delete_button = page.locator(DELETE_BUTTON_SELECTOR).first
        delete_button.click()

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

        # Antigravity IDE実装: フィルタ用selectは .control-group 内の最初の要素（ステータス）
        status_filter = page.locator(FILTER_STATUS_SELECT_SELECTOR).first
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

        # モーダルを開く
        open_button = page.locator("button").filter(has_text=RE_OPEN_CREATE_MODAL).first
        open_button.click()
        page.wait_for_timeout(300)

        # タイトルを空のまま送信
        submit_button = page.locator(SUBMIT_BUTTON_SELECTOR).first
        submit_button.click()
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
        # Antigravity IDE実装は明示的に「期限切れ」というバッジテキストを表示する
        assert "期限切れ" in body_text

        warning_selectors = [
            "[class*='overdue']",
            ".badge.overdue",
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
