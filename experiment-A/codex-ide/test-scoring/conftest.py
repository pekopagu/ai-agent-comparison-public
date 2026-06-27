# conftest.py
# pytest共通設定

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "normal: 正常系テスト"
    )
    config.addinivalue_line(
        "markers", "error: 異常系テスト"
    )
