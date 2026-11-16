"""
Feature router: works out which feature handles a user's message.

Each team member adds one file under features/ — you normally never edit this file.
Every feature module must provide:
    NAME      : str        feature name (shown in the help menu)
    AUTHOR    : str        GitHub username of the author, e.g. "@octocat"
    KEYWORDS  : list[str]  trigger the feature when the message contains any of these
    handle(text, user_id) -> list   returns the list of LINE messages to reply with
Optional:
    match(text) -> bool    custom trigger rule (overrides KEYWORDS)
    PRIORITY  : int        higher is checked first (default 0)
"""
from __future__ import annotations

import importlib
import pkgutil
import sys
from types import ModuleType

from linebot.v3.messaging import TextMessage

import features

HELP_WORDS = ("help", "幫助", "功能", "選單", "?", "？")


def load_features(reload: bool = False) -> list[ModuleType]:
    """Auto-load every module in the features/ folder (files starting with _ are skipped)."""
    if reload:  # after git pull in Colab, reload to pick up the new code
        for name in list(sys.modules):
            if name.startswith("features."):
                del sys.modules[name]
        importlib.reload(features)

    modules = []
    for info in pkgutil.iter_modules(features.__path__):
        if info.name.startswith("_"):
            continue
        modules.append(importlib.import_module(f"features.{info.name}"))
    modules.sort(key=lambda m: getattr(m, "PRIORITY", 0), reverse=True)
    return modules


def matches(module: ModuleType, text: str) -> bool:
    if hasattr(module, "match"):
        return bool(module.match(text))
    return any(k.lower() in text.lower() for k in getattr(module, "KEYWORDS", []))


def help_message(modules: list[ModuleType]) -> list:
    lines = ["🤖 目前支援的功能："]
    for m in modules:
        kw = "、".join(getattr(m, "KEYWORDS", [])[:3]) or "（自訂規則）"
        lines.append(f"• {m.NAME}：輸入「{kw}」  by {m.AUTHOR}")
    return [TextMessage(text="\n".join(lines))]


def route(text: str, user_id: str = "local-user", modules: list[ModuleType] | None = None) -> list:
    """Takes the user's text and returns the list of LINE messages to send back."""
    modules = modules if modules is not None else load_features()
    if text.strip() in HELP_WORDS:
        return help_message(modules)
    for m in modules:
        if matches(m, text):
            try:
                return m.handle(text, user_id)
            except Exception as e:  # one feature's bug should not take down the whole bot
                print(f"[error] feature {m.__name__}: {e!r}")
                return [TextMessage(text=f"「{m.NAME}」功能暫時故障了 🛠️")]
    return [TextMessage(text="我還聽不懂這句話 😅\n輸入「功能」看看我會做什麼！")]
