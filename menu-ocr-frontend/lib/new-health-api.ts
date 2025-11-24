/** New Health API Client - Complete rewrite with robust error handling */

export interface HealthCondition {
  condition_type: string;
  condition_name: string;
  severity?: string;
  description?: string;
}

export interface HealthProfile {
  id: string;
  user_id: string;
  profile_name?: string;
  is_active: boolean;
  conditions: HealthCondition[];
  created_at: string;
  updated_at: string;
}

export interface HealthRecommendation {
  menu_item: string;
  recommendation_type: string;
  reason: string;
  condition: string;
  confidence: number;
}

export interface HealthAnalytics {
  total_actions: number;
  conditions_by_type: Record<string, number>;
  recent_activity: Array<{
    action: string;
    condition_name?: string;
    timestamp: string;
  }>;
}

export class HealthAPIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'HealthAPIError';
  }
}

export class NewHealthAPI {
  private baseUrl: string;

  constructor(baseUrl: string = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") {
    this.baseUrl = baseUrl;
  }

  private async getAuthToken(): Promise<string> {
    try {
      // Import supabase dynamically to avoid module resolution issues
      const { supabase } = await import('./supabase');
      const { data: { session }, error } = await supabase.auth.getSession();
      if (error) {
        throw new HealthAPIError(`Authentication error: ${error.message}`);
      }
      if (!session?.access_token) {
        throw new HealthAPIError("Not authenticated. Please sign in first.");
      }
      return session.access_token;
    } catch (error) {
      if (error instanceof HealthAPIError) throw error;
      throw new HealthAPIError("Failed to get authentication token");
    }
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = await this.getAuthToken();

    const url = `${this.baseUrl}/api/v1${endpoint}`;
    console.log(`🔗 HealthAPI: ${options.method || 'GET'} ${url}`);

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
    });

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      let errorDetails: any = null;

      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
        errorDetails = errorData;
      } catch {
        // Use default error message
      }

      console.error(`❌ HealthAPI Error:`, {
        endpoint,
        status: response.status,
        message: errorMessage,
        details: errorDetails
      });

      throw new HealthAPIError(errorMessage, response.status, errorDetails);
    }

    const data = await response.json();
    console.log(`✅ HealthAPI Success:`, { endpoint, data });
    return data;
  }

  // Profile Management
  async createProfile(profileName?: string): Promise<{ success: boolean; profile: HealthProfile; message: string }> {
    console.log('🏥 Creating health profile:', { profileName });

    try {
      const params = profileName ? `?profile_name=${encodeURIComponent(profileName)}` : '';
      return await this.makeRequest(`/health/profile${params}`, {
        method: 'POST',
      });
    } catch (error) {
      console.error('❌ Failed to create health profile:', error);
      throw error;
    }
  }

  async getProfile(): Promise<HealthProfile> {
    console.log('📋 Getting health profile');

    try {
      return await this.makeRequest('/health/profile');
    } catch (error) {
      console.error('❌ Failed to get health profile:', error);
      throw error;
    }
  }

  // Condition Management
  async addCondition(condition: HealthCondition): Promise<{ success: boolean; condition_id: string; condition: HealthCondition; message: string }> {
    console.log('➕ Adding health condition:', condition);

    try {
      // Validate input
      this.validateCondition(condition);

      return await this.makeRequest('/health/conditions', {
        method: 'POST',
        body: JSON.stringify(condition),
      });
    } catch (error) {
      console.error('❌ Failed to add health condition:', error);
      throw error;
    }
  }

  async removeCondition(conditionName: string): Promise<{ success: boolean; message: string }> {
    console.log('➖ Removing health condition:', conditionName);

    try {
      return await this.makeRequest(`/health/conditions/${encodeURIComponent(conditionName)}`, {
        method: 'DELETE',
      });
    } catch (error) {
      console.error('❌ Failed to remove health condition:', error);
      throw error;
    }
  }

  async listConditions(): Promise<HealthCondition[]> {
    console.log('📝 Listing health conditions');

    try {
      return await this.makeRequest('/health/conditions');
    } catch (error) {
      console.error('❌ Failed to list health conditions:', error);
      throw error;
    }
  }

  // Recommendations
  async getRecommendations(menuItems: Array<{name: string; price?: number; description?: string; category?: string}>): Promise<{
    recommendations: HealthRecommendation[];
    total_items: number;
    analyzed_conditions: number;
    generated_at: string;
  }> {
    console.log('🎯 Getting health recommendations for', menuItems.length, 'items');

    try {
      // Convert menu items to the format expected by the API
      const menuItemsData = menuItems.map(item => ({
        name: item.name,
        price: item.price,
        description: item.description,
        category: item.category,
      }));

      return await this.makeRequest('/health/recommendations', {
        method: 'POST',
        body: JSON.stringify({ menu_items: menuItemsData }),
      });
    } catch (error) {
      console.error('❌ Failed to get health recommendations:', error);
      throw error;
    }
  }

  // Analytics
  async getAnalytics(): Promise<HealthAnalytics> {
    console.log('📊 Getting health analytics');

    try {
      return await this.makeRequest('/health/analytics');
    } catch (error) {
      console.error('❌ Failed to get health analytics:', error);
      throw error;
    }
  }

  // Validation
  private validateCondition(condition: HealthCondition): void {
    if (!condition.condition_type) {
      throw new HealthAPIError("Condition type is required");
    }

    const validTypes = ['allergy', 'illness', 'dietary', 'preference'];
    if (!validTypes.includes(condition.condition_type)) {
      throw new HealthAPIError(`Invalid condition type. Must be one of: ${validTypes.join(', ')}`);
    }

    if (!condition.condition_name || !condition.condition_name.trim()) {
      throw new HealthAPIError("Condition name is required");
    }

    if (condition.severity) {
      const validSeverities = ['mild', 'moderate', 'severe'];
      if (!validSeverities.includes(condition.severity)) {
        throw new HealthAPIError(`Invalid severity. Must be one of: ${validSeverities.join(', ')}`);
      }
    }
  }

  // Bulk Operations
  async addConditions(conditions: HealthCondition[]): Promise<{
    success: boolean;
    added: number;
    errors: Array<{ condition: string; error: string }>;
  }> {
    console.log('📦 Adding multiple health conditions:', conditions.length);

    const results = {
      success: true,
      added: 0,
      errors: [] as Array<{ condition: string; error: string }>
    };

    for (const condition of conditions) {
      try {
        await this.addCondition(condition);
        results.added++;
        console.log(`✅ Added condition: ${condition.condition_name}`);
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : String(error);
        results.errors.push({
          condition: condition.condition_name,
          error: errorMsg
        });
        console.error(`❌ Failed to add condition ${condition.condition_name}:`, error);
      }
    }

    if (results.errors.length > 0) {
      results.success = false;
      console.warn(`⚠️ Added ${results.added} conditions with ${results.errors.length} errors`);
    } else {
      console.log(`✅ Successfully added all ${results.added} conditions`);
    }

    return results;
  }

  // Health Check
  async checkHealth(): Promise<{ status: string; timestamp: string }> {
    try {
      console.log('🏥 Checking health service status');
      const response = await fetch(`${this.baseUrl}/health`, {
        signal: AbortSignal.timeout(5000),
      });

      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ Health service is operational');
      return data;
    } catch (error) {
      console.error('❌ Health service check failed:', error);
      throw new HealthAPIError('Health service is not available');
    }
  }
}

// Export singleton instance
export const newHealthAPI = new NewHealthAPI();