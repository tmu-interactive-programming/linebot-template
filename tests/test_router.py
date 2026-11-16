"""Tests for router.py: help menu, keyword matching, fallback, and error isolation."""
from types import SimpleNamespace

from linebot.v3.messaging import TextMessage

import router


def fake_feature(name="假功能", keywords=("hello",), priority=0, handle=None, match=None):
    mod = SimpleNamespace(
        __name__=f"features.{name}",
        NAME=name,
        AUTHOR="@tester",
        KEYWORDS=list(keywords),
        PRIORITY=priority,
        handle=handle or (lambda text, user_id: [TextMessage(text=f"{name}:{text}")]),
    )
    if match is not None:
        mod.match = match
    return mod


def test_load_features_finds_example():
    names = [m.__name__ for m in router.load_features(reload=True)]
    assert "features.example_parrot" in names


def test_load_features_skips_private_modules():
    assert all(not m.__name__.split(".")[-1].startswith("_") for m in router.load_features())


def test_help_lists_every_feature():
    modules = [fake_feature("天氣", ["天氣"]), fake_feature("垃圾車", ["垃圾"])]
    for word in router.HELP_WORDS:
        [msg] = router.route(word, modules=modules)
        assert "天氣" in msg.text and "垃圾車" in msg.text


def test_keyword_match_is_case_insensitive():
    modules = [fake_feature("echo", ["Hello"])]
    [msg] = router.route("well HELLO there", modules=modules)
    assert msg.text == "echo:well HELLO there"


def test_custom_match_overrides_keywords():
    modules = [fake_feature("digits", [], match=lambda t: t.isdigit())]
    assert router.route("123", modules=modules)[0].text == "digits:123"
    assert "聽不懂" in router.route("abc", modules=modules)[0].text


def test_unknown_text_gets_fallback():
    [msg] = router.route("完全無關的一句話", modules=[fake_feature()])
    assert "聽不懂" in msg.text


def test_broken_feature_does_not_crash_the_bot(capsys):
    def boom(text, user_id):
        raise RuntimeError("bug")

    [msg] = router.route("hello", modules=[fake_feature("壞掉的", handle=boom)])
    assert "壞掉的" in msg.text and "故障" in msg.text
    assert "RuntimeError" in capsys.readouterr().out


def test_priority_order_from_load_features():
    modules = router.load_features()
    priorities = [getattr(m, "PRIORITY", 0) for m in modules]
    assert priorities == sorted(priorities, reverse=True)
