"""
Sample feature — copy this file to make your own.

👉 DO NOT edit other people's feature files.
👉 Each feature lives in its own file under features/, so git merges cleanly.

A feature module only needs to define:
    NAME      : str        feature name (shown in the help menu)
    AUTHOR    : str        your GitHub username, e.g. "@octocat"
    KEYWORDS  : list[str]  trigger the feature when the message contains any of these
    handle(text, user_id) -> list   returns the list of LINE messages to reply with

Optional:
    match(text) -> bool    custom trigger rule (overrides KEYWORDS)
    PRIORITY  : int        higher is checked first (default 0)
"""
from linebot.v3.messaging import TextMessage

# --- metadata shown in the /help menu --------------------------------------
NAME = "鸚鵡 Parrot"
AUTHOR = "@your-github-username"
KEYWORDS = ["鸚鵡", "parrot", "repeat"]

# --- the actual feature logic ----------------------------------------------
def handle(text: str, user_id: str) -> list:
    # `text` is exactly what the user typed.
    # Return a *list* of LINE message objects (1 to 5 messages per reply).
    return [
        TextMessage(text="🦜 鸚鵡覆誦："),
        TextMessage(text=text),
    ]