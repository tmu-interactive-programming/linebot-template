"""Tests for app.py: post signed webhooks through Flask's test client (no network, no LINE account)."""
import base64
import hashlib
import hmac
import json

import pytest
from linebot.v3.messaging import ImageMessage, TextMessage

import app as app_module

SECRET = "test-channel-secret"


def sign(body: str) -> str:
    digest = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def message_event(message: dict, reply_token="reply-token-1") -> dict:
    return {
        "type": "message",
        "mode": "active",
        "timestamp": 1761530000000,
        "source": {"type": "user", "userId": "U-test-user"},
        "webhookEventId": "01TESTEVENT",
        "deliveryContext": {"isRedelivery": False},
        "replyToken": reply_token,
        "message": message,
    }


def text_event(text: str, reply_token="reply-token-1") -> dict:
    return message_event({"id": "1", "type": "text", "text": text, "quoteToken": "q"}, reply_token)


@pytest.fixture
def sent():
    return []


@pytest.fixture
def client(sent):
    flask_app = app_module.create_app(SECRET, "unused-token", reply_func=lambda tok, msgs: sent.append((tok, msgs)))
    return flask_app.test_client()


def post(client, events, signature=None):
    body = json.dumps({"destination": "U-bot", "events": events})
    return client.post(
        "/",
        data=body,
        headers={"X-Line-Signature": signature or sign(body), "Content-Type": "application/json"},
    )


def test_health_check(client):
    res = client.get("/")
    assert res.status_code == 200 and "running" in res.get_data(as_text=True)


def test_text_message_is_routed_to_feature(client, sent):
    res = post(client, [text_event("鸚鵡 你好")])
    assert res.status_code == 200
    [(token, messages)] = sent
    assert token == "reply-token-1"
    assert [m.text for m in messages] == ["🦜 鸚鵡覆誦：", "鸚鵡 你好"]


def test_callback_route_also_works(client, sent):
    body = json.dumps({"destination": "U-bot", "events": [text_event("功能")]})
    res = client.post("/callback", data=body, headers={"X-Line-Signature": sign(body)})
    assert res.status_code == 200
    assert "鸚鵡" in sent[0][1][0].text


def test_bad_signature_is_rejected(client, sent):
    res = post(client, [text_event("hi")], signature="not-a-valid-signature")
    assert res.status_code == 400
    assert sent == []


def test_non_text_message_gets_fixed_reply(client, sent):
    post(client, [message_event({"id": "2", "type": "image", "contentProvider": {"type": "line"}, "quoteToken": "q"})])
    [(_, [msg])] = sent
    assert msg.text == app_module.NON_TEXT_REPLY


def test_non_message_events_are_ignored(client, sent):
    follow = {
        "type": "follow",
        "mode": "active",
        "timestamp": 1761530000000,
        "source": {"type": "user", "userId": "U-test-user"},
        "webhookEventId": "01TESTFOLLOW",
        "deliveryContext": {"isRedelivery": False},
        "replyToken": "reply-token-2",
        "follow": {"isUnblocked": False},
    }
    assert post(client, [follow]).status_code == 200
    assert sent == []


def test_multiple_events_each_get_a_reply(client, sent):
    post(client, [text_event("parrot 1", "t1"), text_event("parrot 2", "t2")])
    assert [tok for tok, _ in sent] == ["t1", "t2"]


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, [app_module.EMPTY_REPLY]),
        ([], [app_module.EMPTY_REPLY]),
        ("純文字", ["純文字"]),
        (TextMessage(text="單一訊息"), ["單一訊息"]),
        ([TextMessage(text=str(i)) for i in range(8)], ["0", "1", "2", "3", "4"]),
    ],
)
def test_build_reply_is_lenient(value, expected):
    assert [m.text for m in app_module.build_reply(value)] == expected


def test_build_reply_keeps_non_text_messages():
    img = ImageMessage(original_content_url="https://example.com/a.png", preview_image_url="https://example.com/a.png")
    assert app_module.build_reply([img]) == [img]
