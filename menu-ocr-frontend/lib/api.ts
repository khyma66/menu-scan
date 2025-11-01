import type { OCRRequest, OCRResponse, MenuItem } from "@/types/menu";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class OCRAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async processImage(imageUrl: string, useLLM: boolean = true): Promise<OCRResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/ocr/process`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        image_url: imageUrl,
        use_llm_enhancement: useLLM,
        language: "en",
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to process image");
    }

    return response.json();
  }

  async checkHealth(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/health`);
    return response.json();
  }
}

export const ocrApi = new OCRAPI();

