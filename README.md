# 🤖 小組 LINE Bot（互動程式設計 W08）

這是全組**共用**的 LINE Bot。每個人把自己在 W07 做的功能放進 `features/` 資料夾裡的**一個檔案**，透過 **Branch → Pull Request → Review → Merge** 合併成同一隻 Bot。

```
app.py              ← LINE webhook 伺服器（不用改）
router.py           ← 自動找到所有功能、決定誰來回覆（不用改）
features/
  example_parrot.py ← 範例功能，複製它開始寫
  你的功能.py        ← ✨ 你只需要新增這一個檔案
tests/              ← 自動測試（CI 會跑）
run_in_colab.ipynb  ← 在 Colab 上啟動整組的 Bot
```

## 🧩 新增一個功能（只要瀏覽器）

1. 在 repo 頁面按鍵盤 **`.`**（句號），開啟 github.dev 線上編輯器。
2. 左下角分支名稱 `main` → **Create new branch** → 輸入 `feature/你的功能名`，例如 `feature/garbage-truck`。
3. 在 `features/` 上按右鍵 **New File**，檔名用小寫英文和底線，例如 `garbage_truck.py`。
4. 貼上下面的樣板並修改：

```python
from linebot.v3.messaging import TextMessage

NAME = "垃圾車時間"            # 功能名稱（會出現在「功能」選單）
AUTHOR = "@你的GitHub帳號"      # 一定要 @ 開頭
KEYWORDS = ["垃圾車", "倒垃圾"]  # 訊息裡有這些字就會觸發

def handle(text, user_id):
    # text：使用者輸入的文字；回傳 1～5 則 LINE 訊息的 list
    return [TextMessage(text="🚛 今天晚上 7:30 在 A 棟門口收垃圾")]
```

5. 左邊 **Source Control** 圖示 → 輸入 commit 訊息（例如 `新增垃圾車時間功能`）→ **Commit & Push**。
6. 回到 GitHub 的 repo 頁面，點 **Compare & pull request**，把 PR 樣板填完（**AI 使用聲明必填**）。
7. 請一位隊友 Review；通過後由 **Product Owner** 按 **Merge**。

> 🚫 `main` 分支受到保護：不能直接 push，一定要開 PR、而且測試要綠色 ✅，再由 PO 合併。

### 功能檔案的規則（feature contract）

| 名稱 | 必填 | 說明 |
|---|---|---|
| `NAME` | ✅ | 功能名稱，字串 |
| `AUTHOR` | ✅ | 你的 GitHub 帳號，`@` 開頭 |
| `KEYWORDS` | ✅ | 觸發關鍵字的 list（有寫 `match` 可省略） |
| `handle(text, user_id)` | ✅ | 回傳 **list**，裡面放 1～5 個 LINE 訊息物件（`TextMessage`、`ImageMessage`…） |
| `match(text)` | 選填 | 自訂觸發規則，回傳 `True` / `False`（會取代 `KEYWORDS`） |
| `PRIORITY` | 選填 | 整數，越大越先比對（預設 0） |

小提醒：
- **只改自己的檔案**。不要改 `app.py`、`router.py` 或隊友的功能檔，這樣合併就不會衝突。
- 關鍵字不要和隊友重複，否則測試會告訴你「被誰搶走了」。
- 一個功能出錯不會讓整隻 Bot 掛掉，使用者會看到「暫時故障了」。

## ✅ 自動測試（CI）

每個 PR 都會自動跑 `pytest`，檢查每個功能檔有沒有照規則寫。
- PR 頁面出現 ✅：可以 Review 了。
- 出現 ❌：點 **Details** 看是哪個檔案、哪一條規則沒過，錯誤訊息是中文的。修好後再 commit 一次，PR 會自動更新。

## 🚀 執行 Bot

### 方法 A：Colab（和 W06 一樣）
開啟 `run_in_colab.ipynb` →「檔案 → 在 GitHub 中開啟」或直接上傳到 Colab，在第一格填入你們組的 repo 網址，依序執行。
Channel secret / access token 用 `getpass` 輸入，**不會**存進程式碼。

### 方法 B：自己的電腦（選用）
```bash
pip install -r requirements.txt
python app.py --local   # 在終端機直接和 Bot 聊天，不需要 LINE 帳號
python -m pytest        # 跑測試
python app.py           # 正式啟動（port 5000，需要 secret / token，也可用環境變數）
```
環境變數：`LINE_CHANNEL_SECRET`、`LINE_CHANNEL_ACCESS_TOKEN`。

## 🔐 安全規則
- 這是**公開** repo：任何人都看得到。**絕對不要**把 Channel secret、access token、密碼寫進程式碼或 commit。
- 不要放真實姓名、學號、電話等個資。
- 不小心 commit 了 token？立刻到 LINE Developers **重新發行（reissue）** token，並告訴助教。
