import os
import json
from pathlib import Path

from dotenv import load_dotenv
import yfinance as yf

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_DIR = Path(__file__).resolve().parents[2]  # JarvisV1 根目錄
TELEGRAM_TODOS_PATH = BASE_DIR / "telegram_todos.json"
CHAT_ID_PATH = BASE_DIR / "telegram_chat_id.txt"
def fetch_history_for_symbol(raw_symbol: str):
    """
    給一個使用者輸入的 symbol（例如 2330、2330.TW、6741…）
    回傳：(實際用來查的 symbol, yfinance history 結果)

    規則：
    - 如果有 '.'，就直接用（例如 2330.TW）
    - 如果是純數字，先試 .TW，查不到再試 .TWO
    - 其他情況就原樣丟給 yfinance
    """
    symbol = raw_symbol.strip()
    candidates = []

    if "." in symbol:
        # 已經指定市場，例如 2330.TW
        candidates = [symbol]
    elif symbol.isdigit():
        # 先試上市 .TW，再試上櫃 .TWO
        candidates = [symbol + ".TW", symbol + ".TWO"]
    else:
        candidates = [symbol]

    last_hist = None
    for s in candidates:
        ticker = yf.Ticker(s)
        hist = ticker.history(period="5d")
        # 有資料就直接回傳
        if not hist.empty:
            return s, hist
        last_hist = hist

    # 如果都沒資料，回傳最後一個嘗試過的 symbol + history（empty）
    return candidates[-1], last_hist



def load_telegram_todos():
    if not TELEGRAM_TODOS_PATH.exists():
        return []

    try:
        with TELEGRAM_TODOS_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        # 確保是 list
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def save_telegram_todos(todos):
    with TELEGRAM_TODOS_PATH.open("w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

if not TOKEN:
    raise RuntimeError(
        "找不到 TELEGRAM_BOT_TOKEN，請在專案根目錄的 .env 檔裡設定：\n"
        "TELEGRAM_BOT_TOKEN=你的BotFather Token"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /start 指令：順便記錄 chat_id 供 CLI 通知使用"""
    chat_id = update.effective_chat.id

    # 把 chat_id 存到檔案
    try:
        with CHAT_ID_PATH.open("w", encoding="utf-8") as f:
            f.write(str(chat_id))
        info = "（已記錄 chat_id，可由 CLI 發送通知給你）"
    except Exception as e:
        info = f"（記錄 chat_id 失敗：{e}）"

    await update.message.reply_text(
        "哈囉，我是 Jarvis Telegram Bot v0.1 ✅\n"
        "目前支援：/ping、/stock、/todo，還能聽懂一些自然語言 😎\n"
        f"{info}"
    )


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /ping 指令"""
    await update.message.reply_text("pong 🏓（Jarvis 在線上）")


async def stock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /stock 指令，查詢股票最近 5 天價格"""
    if not context.args:
        await update.message.reply_text(
            "用法：/stock 股票代號\n\n"
            "例如：\n"
            "  /stock 2330\n"
            "  /stock 2330.TW"
        )
        return

    raw_symbol = context.args[0].strip()

    try:
        # 使用共用工具，會自動處理 .TW / .TWO
        symbol, hist = fetch_history_for_symbol(raw_symbol)

        if hist is None or hist.empty:
            await update.message.reply_text(
                f"找不到 {raw_symbol}（嘗試 {symbol}）的股價資料，請確認代號是否正確。"
            )
            return

        # 把最近 5 天整理成簡單文字表
        lines = [f"最近 5 天股價：{symbol}"]
        prev_close = None
        for idx, row in hist.iterrows():
            date_str = idx.strftime("%Y-%m-%d")
            close = float(row["Close"])
            if prev_close is None:
                change_str = "-"
            else:
                change_pct = (close - prev_close) / prev_close * 100
                change_str = f"{change_pct:+.2f}%"
            lines.append(f"{date_str}  收盤 {close:.2f}  漲跌 {change_str}")
            prev_close = close

        text = "\n".join(lines)
        await update.message.reply_text(text)

    except Exception as e:
        await update.message.reply_text(f"查詢 {symbol} 發生錯誤：{e}")


async def todo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /todo 指令：
    - /todo list
    - /todo add 事情內容
    - /todo done 編號
    """
    chat_id = update.effective_chat.id

    if not context.args:
        help_text = (
            "Todo 用法：\n"
            "/todo list  - 查看待辦清單\n"
            "/todo add 買牛奶  - 新增一筆待辦\n"
            "/todo done 1  - 勾選第 1 筆為完成（並從清單移除）"
        )
        await update.message.reply_text(help_text)
        return

    subcommand = context.args[0].lower()
    todos = load_telegram_todos()

    # /todo list
    if subcommand == "list":
        if not todos:
            await update.message.reply_text("目前沒有任何待辦事項 ✅")
            return

        lines = ["目前待辦清單："]
        for idx, item in enumerate(todos, start=1):
            lines.append(f"{idx}. {item}")
        await update.message.reply_text("\n".join(lines))
        return

    # /todo add XXX
    if subcommand == "add":
        if len(context.args) < 2:
            await update.message.reply_text("用法：/todo add 事情內容")
            return
        text = " ".join(context.args[1:]).strip()
        if not text:
            await update.message.reply_text("待辦內容不能是空白。")
            return
        todos.append(text)
        save_telegram_todos(todos)
        await update.message.reply_text(f"已新增待辦：{text}\n目前共有 {len(todos)} 筆。")
        return

    # /todo done N
    if subcommand == "done":
        if len(context.args) < 2:
            await update.message.reply_text("用法：/todo done 編號\n例如：/todo done 1")
            return
        try:
            index = int(context.args[1])
        except ValueError:
            await update.message.reply_text("請提供正確的數字編號，例如：/todo done 1")
            return

        if index < 1 or index > len(todos):
            await update.message.reply_text(f"編號超出範圍，目前共有 {len(todos)} 筆待辦。")
            return

        done_item = todos.pop(index - 1)
        save_telegram_todos(todos)
        await update.message.reply_text(
            f"已完成並移除：{done_item}\n剩餘 {len(todos)} 筆待辦。"
        )
        return

    # 其他 subcommand
    await update.message.reply_text(
        "未知的子指令。\n\n"
        "Todo 用法：\n"
        "/todo list\n"
        "/todo add 買牛奶\n"
        "/todo done 1"
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    處理一般文字訊息：
    - 如果聽得出是查股票 → 當成查股價
    - 如果聽得出是待辦 / 提醒 → 當成 todo add
    - 其他 → 目前先回覆提示
    """
    text = (update.message.text or "").strip()
    lower = text.lower()

    # ---- 1) 嘗試判斷：是不是在問股票？ ----
    # 條件：句子裡有數字，且提到「股價 / 股票 / 股」
    has_digits = any(ch.isdigit() for ch in text)
    stock_keywords = ["股價", "股票", "股", "price"]

    if has_digits and any(kw in text for kw in stock_keywords):
        # 把第一段連續數字抓出來當股票代碼
        code = ""
        current = ""
        for ch in text:
            if ch.isdigit():
                current += ch
            else:
                if current:
                    code = current
                    break
        if not code and current:
            code = current

        if code:
            try:
                symbol, hist = fetch_history_for_symbol(code)

                if hist is None or hist.empty:
                    await update.message.reply_text(
                        f"我有聽懂你在問股票，但找不到 {code}（嘗試 {symbol}）的股價資料，請確認代號是否正確。"
                    )
                    return

                lines = [f"最近 5 天股價：{symbol}"]
                prev_close = None
                for idx, row in hist.iterrows():
                    date_str = idx.strftime("%Y-%m-%d")
                    close = float(row["Close"])
                    if prev_close is None:
                        change_str = "-"
                    else:
                        change_pct = (close - prev_close) / prev_close * 100
                        change_str = f"{change_pct:+.2f}%"
                    lines.append(f"{date_str}  收盤 {close:.2f}  漲跌 {change_str}")
                    prev_close = close

                await update.message.reply_text("\n".join(lines))
                return

            except Exception as e:
                await update.message.reply_text(f"查詢 {code} 發生錯誤：{e}")
                return

            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")

                if hist.empty:
                    await update.message.reply_text(
                        f"我有聽懂你在問股票，但找不到 {symbol} 的股價資料，請確認代號是否正確。"
                    )
                    return

                lines = [f"最近 5 天股價：{symbol}"]
                prev_close = None
                for idx, row in hist.iterrows():
                    date_str = idx.strftime("%Y-%m-%d")
                    close = float(row["Close"])
                    if prev_close is None:
                        change_str = "-"
                    else:
                        change_pct = (close - prev_close) / prev_close * 100
                        change_str = f"{change_pct:+.2f}%"
                    lines.append(f"{date_str}  收盤 {close:.2f}  漲跌 {change_str}")
                    prev_close = close

                await update.message.reply_text("\n".join(lines))
                return

            except Exception as e:
                await update.message.reply_text(f"查詢 {symbol} 發生錯誤：{e}")
                return

    # ---- 2) 嘗試判斷：是不是在記待辦 / 提醒？ ----
    todo_keywords = ["提醒我", "記得", "幫我記", "加到待辦", "待辦", "todo"]

    if any(kw in text for kw in todo_keywords):
        # 把提醒 / 記得 這些字拿掉，剩下的當成待辦內容
        item = text
        for kw in todo_keywords:
            item = item.replace(kw, "")
        item = item.replace("幫我", "")
        item = item.strip(" ，。.!？?")

        if not item:
            # 如果真的什麼都切不出來，就用原句
            item = text

        todos = load_telegram_todos()
        todos.append(item)
        save_telegram_todos(todos)

        await update.message.reply_text(
            f"已幫你記下：{item}\n目前共有 {len(todos)} 筆待辦。"
        )
        return

    # ---- 3) 目前還聽不懂的，就先禮貌回覆 + 教你用法 ----
    await update.message.reply_text(
        "我有收到你說的：\n"
        f"{text}\n\n"
        "目前我還不太確定要做什麼，可以試試這樣說：\n"
        "  查一下 2330 股價\n"
        "  提醒我明天去銀行\n"
        "或直接用指令：/stock 2330, /todo add 買牛奶"
    )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # 指令處理
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("stock", stock_cmd))
    app.add_handler(CommandHandler("todo", todo_cmd))

    # 一般文字訊息處理（不是 /指令 的）
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("Jarvis Telegram Bot v0.1 已啟動，按 Ctrl + C 可停止。")
    app.run_polling()


if __name__ == "__main__":
    main()

