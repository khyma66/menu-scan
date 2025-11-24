export interface MenuItem {
  name: string;
  price: string | null;
  description: string | null;
  category: string | null;
}

export interface OCRResponse {
  success: boolean;
  menu_items: MenuItem[];
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

