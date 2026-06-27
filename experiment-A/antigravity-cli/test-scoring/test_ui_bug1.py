"""
テストA: 事前準備テスト（Antigravity CLI 実験A 派生版）
フロントエンドUIテスト - Playwright 6本
対象: タスク管理アプリ Vue 3フロントエンド（Antigravity CLI実装）

派生元: common/test-original/test_ui.py
修正内容（Antigravity CLIの実装に合わせた調整・観点・期待値・本数は変更なし）:
    - test_02: 保存ボタンのラベルが編集時「更新する」になっており、
      「保存|save」のみの正規表現では検出できない（Claude Codeと同一パターン）。
      「更新する」を追加して解決。Antigravity CLIの実装には競合する
      別の「更新」ボタン（リフレッシュ用）は存在しないため問題ない。
    - test_03: 削除確認にブラウザネイティブのconfirm()を使用しているため、
      page.on("dialog", ...) でダイアログを自動acceptする処理を追加。
    - test_04: ページ内に「ステータス」を持つ<select>が2つ存在する
      （フォーム側のform.statusとフィルタ側のfilters.status）。
      フィルタ側は@change="fetchTasks"属性で識別できるため、
      この属性を持つselectに絞るセレクタへ変更。

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
# 共通の正規表現パターン
# ============================================================

RE_ADD_BUTTON = re.compile("追加|add|作成|create", re.IGNORECASE)
RE_EDIT_BUTTON = re.compile("編集|edit", re.IGNORECASE)
RE_SAVE_BUTTON = re.compile("保存|save|更新する|update", re.IGNORECASE)
RE_DELETE_BUTTON = re.compile("削除|delete|remove", re.IGNORECASE)
TITLE_INPUT_SELECTOR = "input[type='text'], input[placeholder*='タイトル'], input[placeholder*='title']"


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

        page.wait_for_timeout(500)
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

        save_button = page.locator("button").filter(has_text=RE_SAVE_BUTTON).first
        save_button.click()
        page.wait_for_load_state("networkidle")

        expect(page.locator("body")).to_contain_text("編集後タスク")

    def test_03_delete_task_disappears(self, page_loaded: Page):
        """タスク削除 → 一覧から消える"""
        page = page_loaded

        # Antigravity CLI実装はブラウザネイティブのconfirm()を使用するため
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

        # Antigravity CLI実装: フィルタ用selectは @change="fetchTasks" 属性で識別
        # （フォーム側にも同名v-modelのselectがあるため、属性で絞り込む）
        status_filter = page.locator("select[\\@change='fetchTasks']").first
        if status_filter.count() == 0:
            # 属性セレクタが効かない場合はフィルタセクション内のselectで代替
            status_filter = page.locator("select").nth(2)
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
