export interface MenuItem {
  name: string;
  price: string | null;
  description: string | null;
  category: string | null;
  ingredients: string[];
  taste: string | null;
  similarDish1: string | null;
  similarDish2: string | null;
  recommendation: string | null;
  recommendation_reason: string | null;
  allergens: string[];
  spiciness_level: string | null;
  preparation_method: string | null;
}

export interface OCRResponse {
  success: boolean;
  menu_items: MenuItem[];
  gemini_menu_items?: MenuItem[];
  qwen_menu_items?: MenuItem[];
  raw_text: string;
  processing_time_ms: number;
  enhanced: boolean;
  cached: boolean;
  metadata?: any;
}

export interface OCRRequest {
  image_url: string;
  use_llm_enhancement?: boolean;
  language?: string;
}

export type UserTier = "free" | "pro" | "max";
