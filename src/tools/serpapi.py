"""Flight search tool using SerpAPI."""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

import httpx

from ..config import Config


def _get_next_friday() -> str:
    """Return next Friday as YYYY-MM-DD."""
    today = date.today()
    days_ahead = (4 - today.weekday()) % 7  # Friday = 4
    if days_ahead == 0:
        days_ahead = 7
    return (today + timedelta(days=days_ahead)).isoformat()


SERPAPI_BASE = "https://serpapi.com/search.json"


def search_flights(
    departure_id: str = "SGN",
    arrival_id: str = "HAN",
    outbound_date: str | None = None,
    return_date: str | None = None,
    adults: int = 1,
    currency: str = "VND",
) -> str:
    """Search flights via SerpAPI Google Flights engine.

    Args:
        departure_id: IATA code (e.g. SGN, HAN, DAD)
        arrival_id: IATA code of destination
        outbound_date: YYYY-MM-DD, defaults to next Friday
        return_date: YYYY-MM-DD, defaults to outbound + 5 days
        adults: number of passengers
        currency: VND, USD, etc.

    Returns:
        Formatted string with best options + affiliate link
    """
    key = Config.serpapi_key
    outbound = outbound_date or _get_next_friday()
    ret = return_date or (
        date.fromisoformat(outbound) + timedelta(days=5)
    ).isoformat()

    params: dict[str, Any] = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound,
        "return_date": ret,
        "adults": adults,
        "currency": currency,
        "api_key": key,
    }

    try:
        resp = httpx.get(SERPAPI_BASE, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"⚠️ Lỗi search flight: {e}"

    return _format_flights(data, departure_id, arrival_id, outbound, ret)


def _format_flights(
    data: dict, dep: str, arr: str, out: str, ret: str
) -> str:
    """Format flight results into readable text."""
    best = data.get("best_flights", [])
    other = data.get("other_flights", [])
    all_flights = best + other

    if not all_flights:
        return "😕 Không tìm thấy chuyến bay nào cho tuyến này."

    lines = [
        f"✈️ *{dep} → {arr}*",
        f"📅 {out} → {ret}",
        "",
    ]

    for i, flight in enumerate(all_flights[:5], 1):
        price = f"{flight.get('price', 0):,} VND"
        airlines = set()
        total_duration = flight.get("total_duration", 0)
        hours, mins = divmod(total_duration, 60)

        for leg in flight.get("flights", []):
            airlines.add(leg.get("airline", "?"))
            dep_time = leg.get("departure_airport", {}).get("time", "?")
            arr_time = leg.get("arrival_airport", {}).get("time", "?")
            layovers = flight.get("layovers", [])

            fly_line = (
                f"  {leg.get('departure_airport', {}).get('id', '?')} "
                f"{dep_time} → "
                f"{leg.get('arrival_airport', {}).get('id', '?')} "
                f"{arr_time}"
            )

        airline_str = ", ".join(sorted(airlines))
        duration_str = f"{hours}h{mins}m" if hours else f"{mins}m"
        layover_str = ""
        if layovers:
            layover_str = f"  ⏳ Quá cảnh: {', '.join(layovers)}"

        lines.append(
            f"*{i}.* {airline_str} — *{price}* ({duration_str})"
        )
        lines.append(fly_line)
        if layover_str:
            lines.append(layover_str)
        lines.append("")

    # Inject affiliate link
    affiliate = Config.affiliate_template
    if affiliate:
        lines.append(
            f"🔗 *Affiliate:* [Đặt vé trên {affiliate}]"
        )

    return "\n".join(lines)


def search_shopping(query: str, currency: str = "VND") -> str:
    """Search products via SerpAPI Google Shopping engine.

    Args:
        query: product name to search
        currency: currency for prices

    Returns:
        Formatted product listing
    """
    key = Config.serpapi_key
    params: dict[str, Any] = {
        "engine": "google_shopping",
        "q": query,
        "currency": currency,
        "api_key": key,
    }

    try:
        resp = httpx.get(SERPAPI_BASE, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"⚠️ Lỗi search: {e}"

    results = data.get("shopping_results", [])
    if not results:
        return f"😕 Không tìm thấy \"{query}\"."

    lines = [f"🛒 *Kết quả tìm: {query}*", ""]
    for i, item in enumerate(results[:8], 1):
        title = item.get("title", "?")
        price = item.get("price", "?")
        source = item.get("source", "?")
        rating = item.get("rating", "")
        link = item.get("link", "")

        stars = f" ⭐{rating}" if rating else ""
        lines.append(f"*{i}.* {title}{stars}")
        lines.append(f"   💰 {price} — {source}")
        lines.append(f"   🔗 {link}")
        lines.append("")

    affiliate = Config.affiliate_template
    if affiliate:
        lines.append(f"🔗 *Affiliate:* {affiliate}")

    return "\n".join(lines)
