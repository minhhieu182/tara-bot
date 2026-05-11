"""Gemini agent with tool-calling for flight and shopping search."""

from __future__ import annotations

from google import genai
from google.genai.types import FunctionDeclaration, Tool, Part, Content, Schema

from .config import Config
from .tools.serpapi import search_flights, search_shopping


# ── Gemini tool declarations ──────────────────────────────────────────

FLIGHT_DECL = FunctionDeclaration(
    name="search_flights",
    description="Tìm chuyến bay. Trả về giá, hãng, giờ bay.",
    parameters=Schema(
        type="OBJECT",
        properties={
            "departure_id": Schema(
                type="STRING", description="Mã sân bay đi (IATA). Mặc định SGN"
            ),
            "arrival_id": Schema(
                type="STRING", description="Mã sân bay đến (IATA)"
            ),
            "outbound_date": Schema(
                type="STRING",
                description="Ngày đi (YYYY-MM-DD). Mặc định thứ 6 tuần sau.",
            ),
            "return_date": Schema(
                type="STRING",
                description="Ngày về (YYYY-MM-DD). Mặc định đi + 5 ngày.",
            ),
            "adults": Schema(
                type="INTEGER",
                description="Số người lớn. Mặc định 1.",
            ),
        },
        required=[],
    ),
)

SHOPPING_DECL = FunctionDeclaration(
    name="search_shopping",
    description="Tìm sản phẩm, so sánh giá. Hữu ích khi user hỏi về giá đồ.",
    parameters=Schema(
        type="OBJECT",
        properties={
            "query": Schema(
                type="STRING",
                description="Tên sản phẩm cần tìm (VD: iPhone 16, máy lọc không khí)",
            ),
        },
        required=["query"],
    ),
)

FLIGHT_TOOL = Tool(function_declarations=[FLIGHT_DECL])
SHOPPING_TOOL = Tool(function_declarations=[SHOPPING_DECL])
ALL_TOOLS = [FLIGHT_TOOL, SHOPPING_TOOL]

# ── Tool call dispatch ────────────────────────────────────────────────

TOOL_FUNCTIONS = {
    "search_flights": search_flights,
    "search_shopping": search_shopping,
}


def handle_tool_call(part: Part) -> str:
    """Execute a tool call from Gemini and return result."""
    fc = part.function_call
    name = fc.name
    args = {k: v for k, v in fc.args.items()}
    fn = TOOL_FUNCTIONS.get(name)
    if not fn:
        return f"Unknown tool: {name}"
    return fn(**args)


# ── Chat session ──────────────────────────────────────────────────────

SYSTEM_PROMPT = """Bạn là Tara Bot — một agent thông minh chuyên tìm kiếm chuyến bay và săn giá đồ.

NGUYÊN TẮC:
- Trả lời bằng tiếng Việt tự nhiên, thân thiện.
- Khi user hỏi vé máy bay, dùng tool search_flights.
- Khi user hỏi giá sản phẩm / so sánh giá, dùng tool search_shopping.
- Luôn trích dẫn giá và hãng cụ thể.
- Nếu kết quả rỗng, gợi ý user thay đổi ngày/thành phố.
- Có thể nói chuyện thông thường (chào hỏi, tạm biệt) — không cần gọi tool."""


class Agent:
    def __init__(self):
        api_key = Config.gemini_api_key
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"
        self.system = SYSTEM_PROMPT
        self.history: list[Content] = []

    async def chat(self, user_message: str) -> str:
        """Send user message, execute tool calls if needed, return response."""
        user_content = Content(role="user", parts=[Part(text=user_message)])
        messages = [Content(role="user", parts=[Part(text=self.system)])]
        messages.extend(self.history)
        messages.append(user_content)

        response = self.client.models.generate_content(
            model=self.model,
            contents=messages,
            config={"tools": ALL_TOOLS},
        )

        candidate = response.candidates[0]
        part = candidate.content.parts[0]

        # If Gemini wants to call a tool
        if part.function_call:
            result = handle_tool_call(part)

            # Send tool result back to Gemini for final response
            tool_response = Content(
                role="user",
                parts=[
                    Part(
                        function_response=Part.FunctionResponse(
                            name=part.function_call.name,
                            response={"result": result},
                        )
                    )
                ],
            )

            messages.append(Content(role="model", parts=[part]))
            messages.append(tool_response)

            final = self.client.models.generate_content(
                model=self.model,
                contents=messages,
                config={"tools": ALL_TOOLS},
            )
            final_part = final.candidates[0].content.parts[0]
            reply = final_part.text

            # Save to history
            self.history.append(user_content)
            self.history.append(final.candidates[0].content)

            return reply

        # No tool call — direct response
        reply = part.text
        self.history.append(user_content)
        self.history.append(candidate.content)
        return reply
