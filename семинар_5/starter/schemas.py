"""
JSON schemas for tools in the OpenAI-compatible tool-calling API.

The model reads these to decide which tool to call and with what arguments.
Clearer descriptions mean fewer agent mistakes.

On the seminar we write these schemas by hand (in production they are generated
from Pydantic and type annotations, but it helps to see what goes in first).
"""

TOOL_SCHEMAS = [
    # ----- example schema (complete, for reference) -----
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": (
                "Safe mathematical calculator. Supports +, -, *, /, ^, "
                "sqrt, ln, log, exp, parentheses. Use for any arithmetic on "
                "numbers obtained from other tools — do not calculate by hand."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": (
                            "Mathematical expression, e.g. '(21 - 9.5)' or "
                            "'log(2) / log(1 + 0.17)'."
                        ),
                    },
                },
                "required": ["expression"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "get_fx_rate",
            "description": (
                "Official exchange rate of a currency to the ruble on a given date "
                "from Bank of Russia data. Call when the question is about "
                "USD/EUR/CNY/other rates — do not invent the rate."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "currency": {
                        "type": "string",
                        "description": "ISO currency code: USD, EUR, CNY, GBP, JPY, TRY, etc.",
                    },
                    "on_date": {
                        "type": ["string", "null"],
                        "description": "Date YYYY-MM-DD. If omitted — today.",
                    },
                },
                "required": ["currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_key_rate",
            "description": (
                "Bank of Russia key rate on a date, % per annum. For the current "
                "rate — from cbr.ru; for historical dates — from local archive "
                "of rate changes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "on_date": {
                        "type": ["string", "null"],
                        "description": "Date YYYY-MM-DD. If omitted — today.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_inflation",
            "description": (
                "Rosstat consumer price index, % y/y, at month-end. "
                "For inflation and real returns."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "Year, e.g. 2024"},
                    "month": {
                        "type": "integer",
                        "description": "Month 1..12 (1 = January)",
                        "minimum": 1,
                        "maximum": 12,
                    },
                },
                "required": ["year", "month"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_periods",
            "description": (
                "Compare one metric across two periods: return values a and b, "
                "difference (delta), and ratio (ratio = b/a). Use for questions "
                "like 'how many times did X increase', 'by how much did X change', "
                "'compare X in period A and period B' — do not call get_fx_rate/"
                "get_key_rate twice manually."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "enum": [
                            "key_rate",
                            "fx_USD",
                            "fx_EUR",
                            "fx_CNY",
                            "cpi",
                            "unemployment",
                        ],
                        "description": (
                            "Metric: key_rate, fx_USD/fx_EUR/fx_CNY, cpi, unemployment."
                        ),
                    },
                    "period_a": {
                        "type": "string",
                        "description": "Start period: YYYY-MM or YYYY-MM-DD.",
                    },
                    "period_b": {
                        "type": "string",
                        "description": "End period: YYYY-MM or YYYY-MM-DD.",
                    },
                },
                "required": ["metric", "period_a", "period_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_unemployment",
            "description": (
                "Rosstat unemployment rate (ILO methodology), % of labor force, "
                "at month-end. For 'misery index' (inflation + unemployment)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "Year, e.g. 2024"},
                    "month": {
                        "type": "integer",
                        "description": "Month 1..12 (1 = January)",
                        "minimum": 1,
                        "maximum": 12,
                    },
                },
                "required": ["year", "month"],
            },
        },
    },
]
