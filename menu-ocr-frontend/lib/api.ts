import type { OCRRequest, OCRResponse, MenuItem } from "@/types/menu";
import { supabase } from "./supabase";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class OCRAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async getAuthToken(): Promise<string | null> {
    try {
      const { data: { session }, error } = await supabase.auth.getSession();
      if (error) {
        console.error("Error getting session:", error);
        return null;
      }
      if (session?.access_token) {
        return session.access_token;
      }
      console.warn("No access token in session");
      return null;
    } catch (error) {
      console.error("Exception getting auth token:", error);
      return null;
    }
  }

  async processImage(imageUrl: string, useLLM: boolean = false): Promise<OCRResponse> {
    const token = await this.getAuthToken();

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseUrl}/api/v1/ocr/process`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        image_url: imageUrl,
        use_llm_enhancement: useLLM,
        language: "auto",
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Network error" }));
      throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  async processImageFile(file: File, useLLM: boolean = false): Promise<OCRResponse> {
    const token = await this.getAuthToken();

    const formData = new FormData();
    formData.append("image", file);
    formData.append("use_llm_enhancement", useLLM.toString());
    formData.append("language", "auto");

    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(`${this.baseUrl}/api/v1/ocr/process-upload`, {
        method: "POST",
        headers,
        body: formData,
      });

      if (!response.ok) {
        if (!response.status || response.status === 0) {
          throw new Error("Connection error: Could not reach the server. Please check if the backend is running.");
        }

        const error = await response.json().catch(() => ({
          detail: `HTTP ${response.status}: ${response.statusText}`,
        }));
        throw new Error(error.detail || "Failed to process image");
      }

      const result = await response.json();
      return result;
    } catch (error: any) {
      if (error.message?.includes("fetch") || error.message?.includes("Failed to fetch")) {
        throw new Error("Connection error: Could not reach the server. Please check if the backend is running at " + this.baseUrl);
      }
      throw error;
    }
  }

  async addHealthCondition(condition: {
    condition_type: string;
    condition_name: string;
    severity?: string;
    description?: string;
  }): Promise<any> {
    const token = await this.getAuthToken();
    
    if (!token) {
      throw new Error("Not authenticated. Please sign in first.");
    }

    const response = await fetch(`${this.baseUrl}/api/v1/auth/health-conditions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify(condition),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Failed to add condition" }));
      throw new Error(error.detail || "Failed to add health condition");
    }

    return response.json();
  }

  async addHealthConditions(conditions: Array<{
    condition_type: string;
    condition_name: string;
    severity?: string;
    description?: string;
  }>): Promise<any> {
    const token = await this.getAuthToken();
    
    if (!token) {
      throw new Error("Not authenticated. Please sign in first.");
    }

    console.log("addHealthConditions: Starting with", conditions.length, "conditions");
    console.log("addHealthConditions: Token exists:", !!token);

    // Add conditions one by one
    const results = [];
    const errors = [];
    
    for (const condition of conditions) {
      try {
        console.log(`Adding condition:`, condition);
        
        const response = await fetch(`${this.baseUrl}/api/v1/auth/health-conditions`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
          },
          body: JSON.stringify(condition),
        });

        console.log(`Response status:`, response.status);
        console.log(`Response ok:`, response.ok);

        if (!response.ok) {
          let errorData;
          try {
            errorData = await response.json();
            console.error("Error response data:", errorData);
          } catch (e) {
            const text = await response.text();
            console.error("Error response text:", text);
            errorData = { detail: text || `HTTP ${response.status}: ${response.statusText}` };
          }
          
          const errorMsg = errorData.detail || errorData.message || `HTTP ${response.status}: Failed to add condition: ${condition.condition_name}`;
          console.error(`Failed to add ${condition.condition_name}:`, errorMsg);
          errors.push({ condition: condition.condition_name, error: errorMsg });
          throw new Error(errorMsg);
        }

        const result = await response.json();
        console.log(`Successfully added ${condition.condition_name}:`, result);
        results.push(result);
      } catch (error: any) {
        console.error(`Error adding condition ${condition.condition_name}:`, error);
        // Don't throw immediately - collect all errors
        errors.push({ condition: condition.condition_name, error: error.message });
      }
    }

    if (errors.length > 0) {
      const errorMsg = `Failed to add ${errors.length} condition(s): ${errors.map(e => `${e.condition} (${e.error})`).join(", ")}`;
      throw new Error(errorMsg);
    }

    return { success: true, added: results.length };
  }

  async getHealthConditions(): Promise<any[]> {
    const token = await this.getAuthToken();
    
    if (!token) {
      return [];
    }

    try {
      const response = await fetch(`${this.baseUrl}/api/v1/auth/health-conditions`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        return [];
      }

      const result = await response.json();
      return result;
    } catch {
      return [];
    }
  }

  async translateOCR(rawText: string, detectedLanguage: string = "auto"): Promise<OCRResponse> {
    const token = await this.getAuthToken();

    const formData = new FormData();
    formData.append("raw_text", rawText);
    formData.append("detected_language", detectedLanguage);

    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(`${this.baseUrl}/api/v1/ocr/translate`, {
        method: "POST",
        headers,
        body: formData,
      });

      if (!response.ok) {
        if (!response.status || response.status === 0) {
          throw new Error("Connection error: Could not reach the server. Please check if the backend is running.");
        }

        const error = await response.json().catch(() => ({
          detail: `HTTP ${response.status}: ${response.statusText}`,
        }));
        throw new Error(error.detail || "Failed to translate OCR result");
      }

      const result = await response.json();
      return result;
    } catch (error: any) {
      if (error.message?.includes("fetch") || error.message?.includes("Failed to fetch")) {
        throw new Error("Connection error: Could not reach the server. Please check if the backend is running at " + this.baseUrl);
      }
      throw error;
    }
  }

  async checkHealth(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: "GET",
        signal: AbortSignal.timeout(5000),
      });
      const result = await response.json();
      return result;
    } catch (error: any) {
      if (error.name === "AbortError" || error.message?.includes("fetch")) {
        throw new Error("Connection error: Could not reach the backend server");
      }
      throw error;
    }
  }
}

export const ocrApi = new OCRAPI();
