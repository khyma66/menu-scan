import anyio
from google.cloud import vision

async def ocr_pages(image_bytes_list):
    def _ocr():
        client = vision.ImageAnnotatorClient()
        texts = []
        for image_bytes in image_bytes_list:
            image = vision.Image(content=image_bytes)
            response = client.document_text_detection(image=image)
            if response.full_text_annotation:
                texts.append(response.full_text_annotation.text)
        return "\n---PAGE BREAK---\n".join(texts)

    return await anyio.to_thread.run_sync(_ocr)
