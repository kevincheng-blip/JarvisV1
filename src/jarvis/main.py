import json
from pathlib import Path
import time
from datetime import datetime

import schedule
import typer
from rich.console import Console
from .telegram_utils import send_telegram_message, TelegramNotConfiguredError
import socket
from rich.table import Table

from openai import OpenAI
import yfinance as yf

from .config import get_openai_api_key

console = Console()
app = typer.Typer(help="Jarvis V1.0 - 你的終端機 AI 助理")

# ---------- 共用設定 ----------
TODO_FILE = Path("todos.json")

# ---------- 啟動 OpenAI Client（目前你還沒用到 ask，也沒關係） ----------
_api_key = get_openai_api_key()
client = OpenAI() if _api_key else None


# ---------- 工具函式：待辦讀寫 ----------
def load_todos() -> list[str]:
    if TODO_FILE.exists():
        try:
            data = json.loads(TODO_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [str(x) for x in data]
        except Exception:
            return []
    return []


def save_todos(todos: list[str]) -> None:
    TODO_FILE.write_text(
        json.dumps(todos, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ---------- 工具函式：股票顯示（給 stock & schedule 共用） ----------
def render_stock(symbol: str, days: int) -> bool:
    console.rule(f"[bold yellow]股票查詢：{symbol}[/bold yellow]")

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=f"{days}d")
    except Exception as e:
        console.print(f"[red]抓取股價失敗：[/red]{e}")
        console.rule()
        return False

    if df.empty:
        console.print("[red]找不到這個代號的股價資料，請確認 symbol 是否正確。[/red]")
        console.rule()
        return False

    table = Table(title=f"{symbol} 最近 {len(df)} 天價格")
    table.add_column("日期")
    table.add_column("收盤價", justify="right")
    table.add_column("漲跌%", justify="right")

    prev_close = None
    for idx, row in df.iterrows():
        date_str = idx.strftime("%Y-%m-%d")
        close = float(row["Close"])
        if prev_close is None:
            change_pct = "-"
        else:
            change = (close - prev_close) / prev_close * 100
            change_pct = f"{change:.2f}%"
        table.add_row(date_str, f"{close:.2f}", change_pct)
        prev_close = close

    console.print(table)
    console.rule()
    return True


# ---------- 1) 基礎 hello 指令 ----------
@app.command()
def netcheck():
    """
    檢查常用服務（含 Telegram）是否連線正常
    """
    targets = {
        "Google": "google.com",
        "GitHub": "github.com",
        "PyPI": "pypi.org",
        "Yahoo Finance": "query1.finance.yahoo.com",
        "Telegram API": "api.telegram.org",
    }

    table = Table(title="Jarvis Network Check")
    table.add_column("服務名稱", style="cyan")
    table.add_column("狀態", style="green")

    def can_connect(host: str, port: int = 80, timeout: float = 2.0) -> bool:
        try:
            sock = socket.create_connection((host, port), timeout=timeout)
            sock.close()
            return True
        except OSError:
            return False

    for name, host in targets.items():
        status = "✔️ OK" if can_connect(host) else "❌ Fail"
        table.add_row(name, status)

    console.print(table)

@app.command()
def hello(name: str = "Kevin"):
    """
    最簡單版：跟你打招呼，確認 Jarvis 正常。
    """
    console.rule("[bold green]Jarvis V1.0[/bold green]")
    console.print(f"Hello, [bold cyan]{name}[/bold cyan]! 我已經在 Terminal 等你下指令了。")
    console.rule()


# ---------- 2) （先保留）AI 助問：ask ----------
@app.command()
def ask(prompt: str = typer.Argument(..., help="想問 Jarvis / GPT 的問題")):
    """
    使用 OpenAI 當你的腦：直接在 Terminal 問問題。
    現在你還沒申請 API key，用到時再設定 .env 就好。
    """
    if client is None:
        console.print("[red]尚未設定 OPENAI_API_KEY，未來想用再編輯 .env[/red]")
        raise typer.Exit(code=1)

    console.rule("[bold cyan]Jarvis AI 回答[/bold cyan]")
    console.print(f"[bold]你問：[/bold] {prompt}\n")

    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "你是 Jarvis，幫 Kevin 用簡潔、有條理的方式回答。"},
                {"role": "user", "content": prompt},
            ],
        )
        answer = resp.choices[0].message.content
        console.print(f"[bold green]Jarvis：[/bold green]\n{answer}")
    except Exception as e:
        console.print(f"[red]呼叫 OpenAI 發生錯誤：[/red]{e}")

    console.rule()


# ---------- 3) 股票助理：即時查詢 stock ----------
@app.command()
def stock(
    symbol: str = typer.Argument(..., help="股票代號，例如：2330.TW 或 TSM"),
    days: int = typer.Option(5, help="往前抓幾天的資料"),
):
    """
    立即顯示最近幾天的股價與漲跌。
    """
    render_stock(symbol, days)


@app.command()
def notify(
    message: str = typer.Argument(
        ...,
        help="要發送到 Telegram 的訊息內容",
    )
):
    """
    從 CLI 發送一則訊息到你的 Telegram Jarvis Bot chat。
    """
    try:
        send_telegram_message(message)
        console.print(f"[green]已發送 Telegram 通知：[/green] {message}")
    except TelegramNotConfiguredError as e:
        console.print(f"[yellow]{e}[/yellow]")
    except Exception as e:
        console.print(f"[red]發送 Telegram 通知失敗：{e}[/red]")


# ---------- 4) 待辦清單：todo（寫入 todos.json，永久記憶） ----------
todo_app = typer.Typer(help="簡易待辦清單（會寫入 todos.json）")
app.add_typer(todo_app, name="todo")


@todo_app.command("add")
def todo_add(item: str = typer.Argument(..., help="要加入的待辦事項")):
    todos = load_todos()
    todos.append(item)
    save_todos(todos)
    console.print(f"[green]已加入待辦：[/green]{item}")


@todo_app.command("list")
def todo_list():
    todos = load_todos()
    if not todos:
        console.print("[yellow]目前沒有任何待辦事項。[/yellow]")
        return

    table = Table(title="Jarvis 待辦清單")
    table.add_column("#", justify="right")
    table.add_column("事項")

    for i, item in enumerate(todos, start=1):
        table.add_row(str(i), item)

    console.print(table)


@todo_app.command("clear")
def todo_clear():
    todos = load_todos()
    if not todos:
        console.print("[yellow]本來就沒有待辦事項。[/yellow]")
        return

    save_todos([])
    console.print("[red]已清空所有待辦事項。[/red]")


# ---------- 5) 排程：schedule（目前先做「每天跑股票」） ----------
schedule_app = typer.Typer(help="排程相關指令")
app.add_typer(schedule_app, name="schedule")


@schedule_app.command("stock")
def schedule_stock(
    symbol: str = typer.Argument(..., help="股票代號，例如：2330.TW"),
    days: int = typer.Option(3, help="往前抓幾天的資料"),
    time_str: str = typer.Option("09:00", "--time", "-t", help="每天執行時間，格式 HH:MM"),
):
    """
    每天固定時間自動查詢一次股票，Terminal 要保持開啟。
    按 Ctrl + C 可停止排程。
    """
    # 簡單檢查時間格式
    try:
        hour_str, minute_str = time_str.split(":")
        hour = int(hour_str)
        minute = int(minute_str)
        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError
    except Exception:
        console.print("[red]時間格式錯誤，請用 HH:MM，例如 09:00 或 14:30[/red]")
        raise typer.Exit(code=1)

    console.rule("[bold magenta]Jarvis 排程：股票[/bold magenta]")
    console.print(f"已設定：每天 [bold]{time_str}[/bold] 查詢 [cyan]{symbol}[/cyan] 最近 {days} 天股價。")
    console.print("[yellow]請保持此視窗開啟，按 Ctrl + C 可停止排程。[/yellow]")
    console.rule()

    def job():
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        console.print(f"\n[bold]⏰ 執行時間：[/bold]{now}")
        render_stock(symbol, days)

    schedule.clear()  # 先清除舊排程（簡化）
    schedule.every().day.at(time_str).do(job)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]已停止股票排程。[/yellow]")
        console.rule()


if __name__ == "__main__":
    app()

