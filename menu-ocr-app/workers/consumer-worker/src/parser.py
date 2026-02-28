import re

PRICE_RE = re.compile(r"(\$|€|£|₹|USD|EUR|INR|GBP)\s*\d+(?:[\.,]\d{2})?|\d+(?:[\.,]\d{2})\s*(\$|€|£|₹|USD|EUR|INR|GBP)")

CURRENCY_MAP = {
    "$": "USD",
    "USD": "USD",
    "€": "EUR",
    "EUR": "EUR",
    "£": "GBP",
    "GBP": "GBP",
    "₹": "INR",
    "INR": "INR",
}

def detect_currency(text):
    match = PRICE_RE.search(text)
    if not match:
        return None
    token = match.group(1) or match.group(2)
    return CURRENCY_MAP.get(token)

def parse_ocr_to_table(full_ocr):
    lines = [l.strip() for l in full_ocr.splitlines() if l.strip()]
    sections = []
    current_section = {"name": "Menu", "items": []}

    currency = detect_currency(full_ocr)

    last_item = None
    for line in lines:
        if line.endswith(":") or line.isupper():
            if current_section["items"]:
                sections.append(current_section)
            current_section = {"name": line.rstrip(":"), "items": []}
            last_item = None
            continue

        price_match = PRICE_RE.search(line)
        if price_match:
            price_text = price_match.group(0)
            name_part = line[:price_match.start()].strip(" -")
            desc_part = line[price_match.end():].strip(" -")
            item = {
                "name": name_part or line,
                "price": price_text,
                "description": desc_part or None,
            }
            current_section["items"].append(item)
            last_item = item
        elif last_item:
            last_item["description"] = ((last_item.get("description") or "") + " " + line).strip()
        else:
            current_section["items"].append({"name": line, "price": None, "description": None})

    if current_section["items"]:
        sections.append(current_section)

    return {
        "currency": currency,
        "sections": sections,
    }
