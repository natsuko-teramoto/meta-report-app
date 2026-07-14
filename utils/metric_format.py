def format_number(value):
    return f"{value:,.0f}"


def format_rate(value):
    if value is None:
        return ""
    return f"{value:.2f}"


def format_percent(value):
    if value is None:
        return ""
    return f"{value:.2f}%"


def format_change_rate(value):
    if value is None:
        return ""

    if value > 0:
        return f"前月比 ▲{value:.1f}%"

    if value < 0:
        return f"前月比 ▼{abs(value):.1f}%"

    return "前月比 ±0.0%"