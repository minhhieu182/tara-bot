"""Claude agent with tool-calling — Tara v2.

Upgrade từ so sánh với ota_planner (anh Tiến):
- Prompt caching: cache_control ephemeral trên system prompt (frozen)
- Adaptive thinking: Claude tự quyết khi nào dùng extended thinking
- Streaming: messages.stream() thay vì messages.create()
- Bug fix: lưu response.content (list of blocks) vào history, không phải reply_text (string)
- max_tokens tăng lên 16000 để đủ chỗ cho thinking blocks
- Dynamic content (TODAY) inject vào user message, không vào system prompt
"""

from __future__ import annotations

import json
import asyncio
from typing import Any, AsyncGenerator
from datetime import date

from anthropic import Anthropic
from anthropic.types import ToolUseBlock, TextBlock

from .config import Config
from .tools.serpapi import search_flights, search_shopping

# ── System prompt — FROZEN ────────────────────────────────────────────
# cache_control: ephemeral nhắm vào block này.
# KHÔNG đặt dynamic content (ngày, tên user) vào đây —
# bất kỳ thay đổi nào sẽ invalidate cache cho đến request tiếp theo.

SYSTEM_PROMPT = """Bạn là Tara Bot — agent thông minh chuyên tìm vé máy bay và săn giá đồ.

NGUYÊN TẮC:
- Trả lời bằng tiếng Việt tự nhiên, thân thiện.
- Khi user hỏi vé máy bay, gọi tool search_flights.
- Khi user hỏi giá sản phẩm, gọi tool search_shopping.
- Sau khi tool trả kết quả, chuyển tiếp NGUYÊN VĂN kết quả đó cho user, chỉ thêm 1-2 câu ngắn.
- KHÔNG reformat lại kết quả từ tool.
- Có thể nói chuyện thông thường — không cần gọi tool.

Mặc định cho câu hỏi mơ hồ về thời gian:
- "cuối tuần" → thứ Sáu tuần gần nhất (không quá khứ)
- "tuần sau" → tuần tiếp theo"""

# ── Tool definitions ──────────────────────────────────────────────────

FLIGHT_TOOL: dict = {
    "name": "search_flights",
    "description": "Tìm chuyến bay. Trả về giá, hãng, giờ bay.",
    "input_schema": {
        "type": "object",
        "properties": {
            "departure_id":  {"type": "string", "description": "Mã sân bay đi (IATA). Mặc định SGN"},
            "arrival_id":    {"type": "string", "description": "Mã sân bay đến (IATA)"},
            "outbound_date": {"type": "string", "description": "Ngày đi (YYYY-MM-DD)"},
            "return_date":   {"type": "string", "description": "Ngày về (YYYY-MM-DD)"},
            "adults":        {"type": "integer", "description": "Số người lớn. Mặc định 1"},
        },
        "required": ["arrival_id"],
    },
}

SHOPPING_TOOL: dict = {
    "name": "search_shopping",
    "description": "Tìm sản phẩm, so sánh giá.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Tên sản phẩm cần tìm"},
        },
        "required": ["query"],
    },
}

ALL_TOOLS = [FLIGHT_TOOL, SHOPPING_TOOL]
TOOL_FUNCTIONS: dict[str, Any] = {
    "search_flights":  search_flights,
    "search_shopping": search_shopping,
}
MAX_TOOL_ITERATIONS = 5


# ── Agent ─────────────────────────────────────────────────────────────

class Agent:
    def __init__(self):
        self.client  = Anthropic(api_key=Config.anthropic_api_key)
        self.model   = "claude-sonnet-4-6"
        self.history: list[dict] = []

    def _system(self) -> list[dict]:
        """System prompt với cache_control. Frozen — không thay đổi giữa các request."""
        return [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}]

    def _with_date(self, user_message: str) -> str:
        """Inject ngày hôm nay vào user message — KHÔNG vào system prompt."""
        today = date.today().strftime("%A, %d/%m/%Y")
        return f"[Hôm nay: {today}]\n{user_message}"

    def chat(self, user_message: str) -> str:
        """Sync chat — tool-use loop, trả về text cuối cùng."""
        messages = list(self.history)
        injected = self._with_date(user_message)
        messages.append({"role": "user", "content": injected})

        for iteration in range(MAX_TOOL_ITERATIONS):
            response = self._call_claude(messages)

            # BUG FIX so với agents.py cũ:
            # Lưu response.content (list of blocks), KHÔNG phải reply_text (string).
            # Khi bật thinking, thinking blocks phải tồn tại trong history —
            # nếu chỉ lưu text string, API sẽ báo lỗi ở turn tiếp theo.
            messages.append({"role": "assistant", "content": response.content})

            u = response.usage
            print(
                f"[iter {iteration + 1}] "
                f"cache_read={getattr(u, 'cache_read_input_tokens', 0)} "
                f"cache_create={getattr(u, 'cache_creation_input_tokens', 0)} "
                f"input={u.input_tokens} output={u.output_tokens} "
                f"stop={response.stop_reason}"
            )

            if response.stop_reason == "end_turn":
                reply = "\n".join(
                    b.text for b in response.content if isinstance(b, TextBlock)
                )
                # Persist vào history sau khi xong turn
                self.history.append({"role": "user",      "content": injected})
                self.history.append({"role": "assistant", "content": response.content})
                return reply

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if not isinstance(block, ToolUseBlock):
                        continue
                    result = self._execute_tool(block)
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     str(result),
                    })
                messages.append({"role": "user", "content": tool_results})
                continue

            break  # stop_reason khác

        return "Xin lỗi, em không thể xử lý yêu cầu này. Thử lại với câu hỏi đơn giản hơn nhé!"

    async def stream_chat(self, user_message: str) -> AsyncGenerator[str | dict, None]:
        """Async generator stream cho Telegram fake-streaming.

        Yields:
            str  — text chunk để bot edit_message realtime
            dict — {"type": "tool_use", "name": "..."} để hiện pill trạng thái
        """
        messages = list(self.history)
        injected = self._with_date(user_message)
        messages.append({"role": "user", "content": injected})

        for iteration in range(MAX_TOOL_ITERATIONS):
            with self.client.messages.stream(
                model=self.model,
                max_tokens=16000,
                system=self._system(),
                tools=ALL_TOOLS,
                thinking={"type": "adaptive"},
                messages=messages,
            ) as stream:
                for chunk in stream.text_stream:
                    yield chunk

                final = stream.final_message()

            u = final.usage
            print(
                f"[stream iter {iteration + 1}] "
                f"cache_read={getattr(u, 'cache_read_input_tokens', 0)} "
                f"stop={final.stop_reason}"
            )

            messages.append({"role": "assistant", "content": final.content})

            if final.stop_reason == "end_turn":
                self.history.append({"role": "user",      "content": injected})
                self.history.append({"role": "assistant", "content": final.content})
                return

            if final.stop_reason == "tool_use":
                tool_results = []
                for block in final.content:
                    if not isinstance(block, ToolUseBlock):
                        continue
                    yield {"type": "tool_use", "name": block.name}
                    result = self._execute_tool(block)
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     str(result),
                    })
                messages.append({"role": "user", "content": tool_results})
                continue

            break

    def _call_claude(self, messages: list) -> Any:
        import time
        for attempt in range(3):
            try:
                return self.client.messages.create(
                    model=self.model,
                    max_tokens=16000,
                    system=self._system(),
                    tools=ALL_TOOLS,
                    thinking={"type": "adaptive"},
                    messages=messages,
                )
            except Exception as exc:
                if "429" in str(exc) or "rate_limit" in str(exc).lower():
                    time.sleep(30 * (attempt + 1))
                    continue
                raise
        raise Exception("Claude API: rate limit exceeded after 3 retries")

    def _execute_tool(self, block: ToolUseBlock) -> str:
        fn = TOOL_FUNCTIONS.get(block.name)
        if not fn:
            return f"Unknown tool: {block.name}"
        try:
            return fn(**block.input)
        except Exception as e:
            return f"Lỗi khi chạy {block.name}: {e}"
