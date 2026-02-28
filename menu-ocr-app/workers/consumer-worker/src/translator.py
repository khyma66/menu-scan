import anyio
from google.cloud import translate_v2

async def translate_table(table_json, target_lang):
    def _translate():
        client = translate_v2.Client()

        def translate_text(text):
            if not text:
                return text
            result = client.translate(text, target_language=target_lang)
            return result.get("translatedText", text)

        def translate_item(item):
            return {
                **item,
                "name": translate_text(item.get("name")),
                "description": translate_text(item.get("description")),
            }

        sections = []
        for section in table_json.get("sections", []):
            translated_items = [translate_item(i) for i in section.get("items", [])]
            sections.append({
                "name": translate_text(section.get("name")),
                "items": translated_items,
            })

        return {
            "currency": table_json.get("currency"),
            "sections": sections,
        }

    return await anyio.to_thread.run_sync(_translate)
