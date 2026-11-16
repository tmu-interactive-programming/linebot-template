"""
Contract test: every file in features/ must follow the feature contract (see router.py).

Each feature file gets its own test cases, so CI tells you exactly whose file broke.
Read the assert messages — they explain what to fix (in zh-TW).
"""
import importlib
import inspect
import pkgutil

import pytest
from linebot.v3.messaging import Message

import features
import router

PLACEHOLDER_AUTHOR = "@your-github-username"
MAX_MESSAGES = 5

FEATURE_NAMES = sorted(
    info.name for info in pkgutil.iter_modules(features.__path__) if not info.name.startswith("_")
)


def load(name):
    # Import inside the test, so a SyntaxError in one file fails only that file's tests.
    return importlib.import_module(f"features.{name}")


def test_there_is_at_least_one_feature():
    assert FEATURE_NAMES, "features/ 資料夾裡沒有任何功能檔"


@pytest.mark.parametrize("name", FEATURE_NAMES)
def test_file_name_is_snake_case(name):
    assert name == name.lower() and name.isidentifier(), (
        f"檔名 features/{name}.py 請用小寫英文、數字、底線，例如 features/garbage_truck.py"
    )


@pytest.mark.parametrize("name", FEATURE_NAMES)
def test_imports_cleanly(name):
    load(name)


@pytest.mark.parametrize("name", FEATURE_NAMES)
def test_metadata(name):
    mod = load(name)
    assert isinstance(getattr(mod, "NAME", None), str) and mod.NAME.strip(), "請設定 NAME = \"功能名稱\""

    author = getattr(mod, "AUTHOR", None)
    assert isinstance(author, str) and author.startswith("@") and len(author) > 1, (
        "AUTHOR 要是你的 GitHub 帳號並以 @ 開頭，例如 AUTHOR = \"@octocat\""
    )
    if not name.startswith("example_"):
        assert author != PLACEHOLDER_AUTHOR, "請把 AUTHOR 改成你自己的 GitHub 帳號"

    keywords = getattr(mod, "KEYWORDS", None)
    if hasattr(mod, "match"):
        assert callable(mod.match), "match 必須是函式：def match(text): ..."
        assert keywords is None or isinstance(keywords, list), "KEYWORDS 必須是 list"
    else:
        assert isinstance(keywords, list) and keywords, "請設定 KEYWORDS = [\"關鍵字1\", \"關鍵字2\"]"
        assert all(isinstance(k, str) and k.strip() for k in keywords), "KEYWORDS 裡每一個都要是非空字串"
        assert not any(k.strip() in router.HELP_WORDS for k in keywords), (
            f"KEYWORDS 不能用系統保留字 {router.HELP_WORDS}"
        )

    priority = getattr(mod, "PRIORITY", 0)
    assert isinstance(priority, int), "PRIORITY 必須是整數"


@pytest.mark.parametrize("name", FEATURE_NAMES)
def test_handle_signature(name):
    mod = load(name)
    assert callable(getattr(mod, "handle", None)), "請定義 def handle(text, user_id): ..."
    try:
        inspect.signature(mod.handle).bind("hi", "U123")
    except TypeError:
        pytest.fail("handle 要接收兩個參數：def handle(text, user_id):")


def importable_features():
    """Like router.load_features(), but a broken teammate file doesn't fail *your* test."""
    modules = []
    for other in FEATURE_NAMES:
        try:
            modules.append(load(other))
        except Exception:
            pass
    return sorted(modules, key=lambda m: getattr(m, "PRIORITY", 0), reverse=True)


def sample_text(mod):
    keywords = getattr(mod, "KEYWORDS", None) or []
    return keywords[0] if keywords else None


@pytest.mark.parametrize("name", FEATURE_NAMES)
def test_handle_returns_line_messages(name):
    mod = load(name)
    text = sample_text(mod)
    if text is None:
        pytest.skip("只有自訂 match()、沒有 KEYWORDS，無法自動產生測試輸入")
    result = mod.handle(text, "U-test-user")
    assert isinstance(result, list), (
        f"handle 要回傳 list，例如 [TextMessage(text=\"...\")]，但拿到 {type(result).__name__}"
    )
    assert 1 <= len(result) <= MAX_MESSAGES, f"一次回覆要有 1～{MAX_MESSAGES} 則訊息，現在是 {len(result)} 則"
    for msg in result:
        assert isinstance(msg, Message), (
            f"清單裡要放 LINE 訊息物件（TextMessage、ImageMessage…），不是 {type(msg).__name__}"
        )


@pytest.mark.parametrize("name", FEATURE_NAMES)
def test_keyword_reaches_this_feature(name):
    """If another feature grabs your keyword first, users can never reach your feature."""
    mod = load(name)
    text = sample_text(mod)
    if text is None:
        pytest.skip("沒有 KEYWORDS")
    modules = importable_features()
    winner = next((m for m in modules if router.matches(m, text)), None)
    assert winner is not None and winner.__name__ == mod.__name__, (
        f"輸入「{text}」會被 {winner.__name__ if winner else '（沒有人）'} 搶走，"
        f"請換一個關鍵字，或和隊友討論 PRIORITY"
    )
