from typing import Optional, List
import json
from pathlib import Path
from datetime import datetime
#
# === 儲存戰情室 log 的輔助函式（依 dev/prod 寫入詳略） ===
def save_war_room_log(question, raw_output, final_summary):
    """
    將戰情室結果存成 logs/war_room/YYYY-MM-DD_HH-MM-SS.json，依 dev/prod 寫入詳略，回傳檔案路徑。
    """
    root = Path(__file__).resolve().parents[2]
    log_dir = root / "logs" / "war_room"
    log_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    log_path = log_dir / f"{now_str}.json"
    if is_dev_mode():
        raw = raw_output
    else:
        raw = None if raw_output is None else "（僅保留 summary，詳細內容略）"
    data = {
        "timestamp": now.isoformat(),
        "question": question,
        "raw_output": raw,
        "final_summary": final_summary,
    }
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return str(log_path)
#
# === 儲存戰情室 log 的輔助函式（含回傳路徑） ===
import json
from pathlib import Path
from datetime import datetime

def save_war_room_log(question, raw_output, final_summary):
    """
    將每次戰情室結果存成 logs/war_room/日期時間.json，不覆蓋舊檔，並回傳路徑。
    """
    log_dir = Path(__file__).resolve().parents[2] / "logs" / "war_room"
    log_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d_%H%M%S")
    log_path = log_dir / f"{now_str}.json"
    data = {
        "timestamp": now.isoformat(),
        "question": question,
        "raw_output": raw_output,
        "final_summary": final_summary,
    }
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return str(log_path)
import os

import os

def is_dev_mode() -> bool:
    return os.getenv("JGOD_ENV", "prod") == "dev"
    return os.getenv("JGOD_ENV", "prod") == "dev"
#
# === 儲存戰情室 log 的輔助函式 ===
import json
from pathlib import Path
from datetime import datetime

def save_war_room_log(question, raw_output, final_summary):
    """
    將每次戰情室結果存成 logs/war_room/日期時間.json，不覆蓋舊檔。
    """
    log_dir = Path(__file__).resolve().parents[2] / "logs" / "war_room"
    log_dir.mkdir(parents=True, exist_ok=True)
    now_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    log_path = log_dir / f"{now_str}.json"
    data = {
        "question": question,
        "raw_output": raw_output,
        "final_summary": final_summary,
    }
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
#
# === 總結所有角色輸出的輔助函式 ===
def summarize_council_output(raw_output: str) -> str:
    """
    用 OpenAI GPT（或你指定的 provider）將戰情室所有角色輸出整合成一段「最終結論」。
    """

    from api_clients.openai_client import GPTProvider
    gpt = GPTProvider()

    system_prompt = """
    你是 J-GOD 戰情室的總指揮官。
    請將所有角色的輸出整合成一段「可直接採用的總結」，格式包含：

    【J-GOD 戰情總結】
    - 明日方向（多 / 空 / 震盪）
    - 三大理由（最重要，不要廢話）
    - 關鍵風險
    - 建議策略（簡短但可操作）
    """

    user_prompt = f"""
    以下是所有角色及 AI Provider 的戰情室輸出：
    {raw_output}

    請依照系統提示格式產生最終結論。
    """

    return gpt.ask(system_prompt=system_prompt, user_prompt=user_prompt)
from dataclasses import dataclass
from typing import List, Dict, Any
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed


from api_clients.openai_client import GPTProvider
from api_clients.anthropic_client import ClaudeProvider
from api_clients.perplexity_client import PerplexityProvider
from api_clients.gemini_client import GeminiProvider

# 全域 provider 登記表：key 要跟 YAML 裡的 providers 名稱一致
PROVIDER_REGISTRY: Dict[str, Any] = {
    "openai": GPTProvider(),
    "gpt": GPTProvider(),  # 兼容舊 key
    "claude": ClaudeProvider(),
    "gemini": GeminiProvider(),
    "perplexity": PerplexityProvider(),
}

# 兼容別名：提供一個較語意化的 PROVIDER_INSTANCES 變數
PROVIDER_INSTANCES = PROVIDER_REGISTRY

# 載入角色設定
with open("config/war_room_roles.yaml", "r", encoding="utf-8") as f:
    ROLES_CONFIG = yaml.safe_load(f)

ROLES: Dict[str, Dict[str, Any]] = ROLES_CONFIG.get("roles", {})


@dataclass
class AIOpinion:
    role_id: str
    display_name: str
    provider: str
    content: str
    stance: str
    confidence: float


def build_context(jgod_state: Dict[str, Any]) -> str:
    """
    戰情室 v3：
    不在這裡重複呼叫 FinMind，而是使用 war_room_app 傳進來的 jgod_state。
    這樣 FinMind 只會被查一次，速度會快很多。
    """
    market = jgod_state or {}

    # 若明確標示休市
    if not market.get("market_open", True):
        return "今日休市（來自市場引擎判斷），僅能做整體風險與策略規劃。"

    taiex_close = market.get("taiex_close", "資料不足")
    taiex_change = market.get("taiex_change", "資料不足")
    taiex_volume = market.get("taiex_volume", "資料不足")
    tsmc_close = market.get("tsmc_close", "資料不足")
    tsmc_change = market.get("tsmc_change", "資料不足")
    foreign = market.get("foreign", "資料不足")
    trust = market.get("trust", "資料不足")
    dealer = market.get("dealer", "資料不足")

    ctx = (
        "【台股市場資料（來自 FinMind 市場引擎）】\n"
        f"- 加權收盤：{taiex_close}（變動：{taiex_change}）\n"
        f"- 成交量：{taiex_volume}\n"
        f"- 台積電：{tsmc_close}（變動：{tsmc_change}）\n"
        f"- 三大法人：外資 {foreign}｜投信 {trust}｜自營商 {dealer}\n"
    )

    return ctx


def _pick_provider(name: str):
    """
    根據 provider 名稱挑選要用的 AI。
    name 可以是：gpt / claude / perplexity / gemini
    """
    name = (name or "gpt").lower()
    # 優先從註冊表取已建立的 provider instance
    provider = PROVIDER_REGISTRY.get(name)
    if provider is not None:
        return provider

    # fallback（保險）：仍然回傳新的 GPTProvider
    return GPTProvider()


def ask_role(
    role_id: str,
    role_cfg: Dict[str, Any],
    question: str,
    context: str,
    previous_summary: str | None = None,
) -> AIOpinion:
    """
    v3：單輪戰情室 + 優先使用 YAML 的 system_prompt。
    在角色內文層面不做多輪，只求輸出短、狠、準。
    """
    display_name = role_cfg.get("display_name", role_id)
    goal = role_cfg.get("goal", "")
    style = role_cfg.get("style", "")
    provider_name = role_cfg.get("provider", "gpt")

    # 1) 優先使用 YAML 裡的 system_prompt
    system_prompt_text: str | None = role_cfg.get("system_prompt")

    # 2) 若 YAML 沒定義，就用預設簡短版，這裡改成「最多 4 行」
    if not system_prompt_text:
        system_prompt_text = f"""
你是「{display_name}」，你的任務是：{goal}

請用最多 4 行文字回答（不能超過），不要廢話：
第 1 行：今天的關鍵觀察（可以包含 1～2 個重要數字或指標）。
第 2 行：方向或風險判斷（偏多 / 偏空 / 震盪，簡短說原因）。
第 3 行：當下最大風險（1 句話）。
第 4 行：給使用者的具體建議（進場 / 觀望 / 減碼 / 控管風險 等）。

風格：{style}
禁止使用條列符號或小標題，不要超過 4 行。
""".strip()

    # 組 user prompt
    user_prompt_parts = [
        f"使用者問題：{question}",
        "",
        "=== J-GOD 戰情資料 ===",
        context,
    ]
    if previous_summary:
        user_prompt_parts.append("\n=== 其他幕僚前一輪重點摘要 ===")
        user_prompt_parts.append(previous_summary)

    user_prompt = "\n".join(user_prompt_parts)

    client = _pick_provider(provider_name)
    raw_content = client.ask(system_prompt_text, user_prompt) or ""

    # 後處理：強制最多 4 行，去掉空白行
    lines = [line.strip() for line in raw_content.strip().splitlines() if line.strip()]
    if not lines:
        lines = ["資料不足"]

    if len(lines) > 4:
        lines = lines[:4]

    content = "\n".join(lines)

    # 簡單從內容猜測立場（之後可以再優化）
    stance = "中性"
    text_for_check = content
    if "偏多" in text_for_check or "多頭" in text_for_check:
        stance = "偏多"
    if "偏空" in text_for_check or "空頭" in text_for_check:
        stance = "偏空"

    return AIOpinion(
        role_id=role_id,
        display_name=display_name,
        provider=provider_name,
        content=content,
        stance=stance,
        confidence=0.6,  # 先給固定值，之後可改成模型算
    )


def summarize_for_user(
    question: str,
    context: str,
    opinions: List[AIOpinion],
) -> str:
    """
    v3：股神總結 = 短版戰報，最多 5 行。
    """
    gpt = GPTProvider()

    merged = ["以下是各幕僚的簡短發言："]
    for op in opinions:
        merged.append(
            f"【{op.display_name}（{op.provider}）】立場：{op.stance}\n{op.content}\n"
        )

    system_prompt = """
你是「股神總結人格」，請閱讀所有幕僚發言，
輸出一份「最多 5 行」的戰報給使用者：

第 1 行：今天台股 + 國際市場整體一句話總結。
第 2 行：多空結論（偏多 / 偏空 / 震盪）＋ 1 個最關鍵理由。
第 3 行：當前最大風險或變數（1～2 個，短句）。
第 4 行：當前最大機會（族群或策略方向，短句）。
第 5 行：具體操作建議（今天適合做什麼、不適合做什麼）。

規則：
- 嚴格控制在 5 行內，不要分點、不要條列符號。
- 不要重複各幕僚原話，要做「濃縮後的結論」。
""".strip()

    user_prompt = (
        f"使用者問題：{question}\n\n"
        f"=== J-GOD 戰情資料 ===\n{context}\n\n"
        "=== 幕僚發言 ===\n" + "\n".join(merged)
    )

    summary = gpt.ask(system_prompt, user_prompt) or ""
    # 也幫你做一下「最多 5 行」的保護
    lines = [line.strip() for line in summary.strip().splitlines() if line.strip()]
    if len(lines) > 5:
        lines = lines[:5]
    if not lines:
        lines = ["（目前沒有足夠資訊產出戰報）"]
    return "\n".join(lines)




def run_war_room(
    question: str,
    stock_id: str = None,
    start_date: str = None,
    end_date: str = None,
    jg_state: Optional[dict] = None,
    selected_providers: Optional[List[str]] = None,
) -> tuple[list[dict], str]:
    """
    支援每個角色多 provider，依照 YAML 的 providers 欄位（若無則 fallback 舊 provider 欄位），
    並可用 selected_providers 過濾。
    回傳 (opinions, final_summary)
    """
    import time
    import socket
    import requests
    context = build_context(jg_state)
    opinions: List[dict] = []
    # 若呼叫方未指定 selected_providers，預設啟用 gpt
    if not selected_providers:
        selected_providers = ["gpt"]

    def _call_provider(provider_key: str, system_prompt: str, user_prompt: str) -> str:
        provider = PROVIDER_REGISTRY.get(provider_key)
        if provider is None:
            return f"[{provider_key}] provider 未註冊，已略過。"

        max_retries = 2
        for attempt in range(1, max_retries + 1):
            try:
                # 嘗試設置 timeout，若 provider 支援
                if hasattr(provider, "ask"):
                    # 檢查 ask 是否支援 timeout 參數
                    import inspect
                    sig = inspect.signature(provider.ask)
                    if "timeout" in sig.parameters:
                        return provider.ask(system_prompt, user_prompt, timeout=10)
                    else:
                        # 若不支援 timeout，直接呼叫
                        return provider.ask(system_prompt, user_prompt)
                else:
                    return f"[{provider_key}] provider 未實作 ask() 方法"
            except Exception as e:
                # 檢查是否為暫時性錯誤（429, 500, timeout）
                err_msg = str(e)
                is_temporary = False
                if any(code in err_msg for code in ["429", "500", "timeout", "Timeout", "temporarily", "rate limit"]):
                    is_temporary = True
                if isinstance(e, (requests.exceptions.Timeout, socket.timeout)):
                    is_temporary = True
                if attempt < max_retries and is_temporary:
                    time.sleep(1.5 * attempt)  # 遞增等待
                    continue
                # dev/prod 模式切換錯誤訊息詳略
                if is_dev_mode():
                    return f"[{provider_key}] 呼叫失敗：{e}"
                else:
                    return f"[{provider_key}] 回應異常，已略過。"

    # 依照 ROLES 設定，每個角色可有多個 provider
    for role_id, role_cfg in ROLES.items():
        display_name = role_cfg.get("display_name", role_id)
        goal = role_cfg.get("goal", "")
        style = role_cfg.get("style", "")
        # 新版：支援 providers: ["openai", "claude", ...]
        role_providers = role_cfg.get("providers")
        if not role_providers:
            # fallback 舊 provider 欄位
            p = role_cfg.get("provider")
            role_providers = [p] if p else ["openai"]

        # 過濾 selected_providers
        if selected_providers is not None:
            role_providers = [p for p in role_providers if p in selected_providers]
        if not role_providers:
            continue

        system_prompt_text: str = role_cfg.get("system_prompt")
        if not system_prompt_text:
            system_prompt_text = f"你是「{display_name}」，你的任務是：{goal}\n風格：{style}"

        # 組 user prompt
        user_prompt = f"使用者問題：{question}\n\n=== J-GOD 戰情資料 ===\n{context}"

        for provider_key in role_providers:
            content = _call_provider(provider_key, system_prompt_text, user_prompt)
            
            # 檢查是否為錯誤訊息
            if content and content.startswith(f"[{provider_key}]"):
                # 這是錯誤訊息，記錄但不加入正常意見
                opinions.append({
                    "role_id": role_id,
                    "display_name": display_name,
                    "provider": provider_key,
                    "content": content,
                    "stance": "錯誤",
                    "confidence": 0.0,
                    "is_error": True,
                })
                continue
            
            # 後處理：最多 4 行，去空白行
            lines = [line.strip() for line in (content or "").strip().splitlines() if line.strip()]
            if not lines:
                lines = ["資料不足"]
            if len(lines) > 4:
                lines = lines[:4]
            content_final = "\n".join(lines)

            # 立場判斷
            stance = "中性"
            text_for_check = content_final
            if "偏多" in text_for_check or "多頭" in text_for_check:
                stance = "偏多"
            if "偏空" in text_for_check or "空頭" in text_for_check:
                stance = "偏空"

            opinions.append({
                "role_id": role_id,
                "display_name": display_name,
                "provider": provider_key,
                "content": content_final,
                "stance": stance,
                "confidence": 0.6,
                "is_error": False,
            })

    # --- 股神總結（短版戰報） ---
    final_summary = summarize_for_user(question, context, [
        AIOpinion(
            role_id=op["role_id"],
            display_name=op["display_name"],
            provider=op["provider"],
            content=op["content"],
            stance=op["stance"],
            confidence=op["confidence"],
        ) for op in opinions
    ])

    # === 自動寫 log（組合 raw_output 字串） ===
    raw_output = "\n\n".join([
        f"【{op['display_name']}｜{op['provider']}】\n{op['content']}" for op in opinions
    ])
    log_path = save_war_room_log(question, raw_output, final_summary)
    if is_dev_mode():
        print(f"[J-GOD] 戰情室 log 已儲存：{log_path}")

    return opinions, final_summary
