"""
LINE bot server: receives LINE webhooks and hands each text message to router.route().

You normally never edit this file — add your feature under features/ instead.

Run it:
    python app.py           # real LINE bot on port 5000 (asks for the secret / token)
    python app.py --local   # chat with the bot in the terminal, no LINE account needed

Secrets are read from the env vars LINE_CHANNEL_SECRET / LINE_CHANNEL_ACCESS_TOKEN,
or typed in with getpass. Never write them into the code — this repo is public.
"""
from __future__ import annotations

import getpass
import os
import sys
from typing import Callable

from flask import Flask, abort, request
from linebot.v3 import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    Message,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

import router

PORT = 5000
MAX_MESSAGES = 5  # LINE allows at most 5 messages per reply
NON_TEXT_REPLY = "目前只看得懂文字訊息喔 📝\n輸入「功能」看看我會做什麼！"
EMPTY_REPLY = "（這個功能沒有回傳任何訊息 🤔）"

ReplyFunc = Callable[[str, list], None]


def build_reply(messages) -> list:
    """Make a feature's return value safe to send: always a list of 1–5 LINE messages."""
    if messages is None:
        messages = []
    elif isinstance(messages, (Message, str)):
        messages = [messages]
    fixed = [TextMessage(text=m) if isinstance(m, str) else m for m in messages]
    if not fixed:
        fixed = [TextMessage(text=EMPTY_REPLY)]
    return fixed[:MAX_MESSAGES]


def make_line_reply(access_token: str) -> ReplyFunc:
    """Returns a function that sends messages back through the LINE Messaging API."""
    configuration = Configuration(access_token=access_token)

    def reply(reply_token: str, messages: list) -> None:
        with ApiClient(configuration) as api_client:
            MessagingApi(api_client).reply_message(
                ReplyMessageRequest(reply_token=reply_token, messages=messages)
            )

    return reply


def create_app(channel_secret: str, access_token: str, reply_func: ReplyFunc | None = None) -> Flask:
    """Build the Flask app. Tests pass their own reply_func so nothing goes to the network."""
    app = Flask(__name__)
    parser = WebhookParser(channel_secret)
    reply = reply_func or make_line_reply(access_token)

    modules = router.load_features(reload=True)
    print(f"✅ 已載入 {len(modules)} 個功能：")
    for m in modules:
        print(f"   • {m.NAME}  by {m.AUTHOR}  ({m.__name__})")

    @app.get("/")
    def health():
        return f"LINE bot is running ✅ ({len(modules)} features loaded)"

    @app.post("/")
    @app.post("/callback")
    def webhook():
        signature = request.headers.get("X-Line-Signature", "")
        body = request.get_data(as_text=True)
        try:
            events = parser.parse(body, signature)
        except InvalidSignatureError:
            abort(400)  # not from LINE (or wrong channel secret)

        for event in events:
            if not isinstance(event, MessageEvent):
                continue  # follow / unfollow / postback ... are ignored for now
            if isinstance(event.message, TextMessageContent):
                text = event.message.text
                user_id = getattr(event.source, "user_id", None) or "unknown"
                print(f"[recv] {user_id}: {text}")
                messages = build_reply(router.route(text, user_id, modules))
            else:
                messages = [TextMessage(text=NON_TEXT_REPLY)]
            reply(event.reply_token, messages)
        return "OK"

    return app


def read_secret(env_name: str, prompt: str) -> str:
    value = os.environ.get(env_name, "").strip()
    if value:
        return value
    print(prompt)
    return getpass.getpass()


def local_chat() -> None:
    """A terminal chat loop: test your feature without LINE, Dev Tunnel or a token."""
    modules = router.load_features(reload=True)
    print(f"💬 本機測試模式（{len(modules)} 個功能）。輸入「功能」看選單，輸入 exit 離開。")
    while True:
        try:
            text = input("你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if text.lower() in ("exit", "quit"):
            break
        if not text:
            continue
        for m in build_reply(router.route(text, "local-user", modules)):
            print("bot>", getattr(m, "text", None) or f"[{type(m).__name__}]")


if __name__ == "__main__":
    if "--local" in sys.argv:
        local_chat()
    else:
        secret = read_secret("LINE_CHANNEL_SECRET", "貼上你的 LINE Channel secret：")
        token = read_secret("LINE_CHANNEL_ACCESS_TOKEN", "貼上你的 LINE Channel access token：")
        create_app(secret, token).run(port=PORT)
