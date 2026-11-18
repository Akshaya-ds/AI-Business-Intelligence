
export const API_BASE = 'https://ai-business-intelligence-1-280q.onrender.com/api';
const TOKEN_KEY = 'business_platform_token';

export const auth = {
  getToken(): string | null {
    return sessionStorage.getItem(TOKEN_KEY);
  },

  setToken(token: string) {
    sessionStorage.setItem(TOKEN_KEY, token);
  },

  clearToken() {
    sessionStorage.removeItem(TOKEN_KEY);
  },

  isLoggedIn(): boolean {
    return !!this.getToken();
  }
};

async function request(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const headers = new Headers(options.headers || {});
  const token = auth.getToken();

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers
  });

  if (response.status === 401) {
    auth.clearToken();
    window.dispatchEvent(new Event('auth-expired'));
  }

  return response;
}

async function getError(response: Response, fallback: string) {
  const error = await response.json().catch(() => ({}));
  return error.detail || fallback;
}

export interface User {
  id: number;
  name: string;
  email: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Business {
  id: number;
  name: string;
  type?: string;
  description?: string;
  contact_email?: string;
  created_at: string;
  is_public?: boolean;
  is_read_only?: boolean;
}

export interface DatasetMeta {
  id: number;
  filename: string;
  uploaded_at: string;
  row_count?: number;
  has_date: number;
  has_product_name: number;
  has_category: number;
  has_quantity: number;
  has_price: number;
  has_cost: number;
  has_revenue: number;
  has_stock: number;
}

export interface AnalyticsSummary {
  total_transactions?: number;
  number_of_products?: number;
  total_revenue?: number;
  total_units_sold?: number;
  profit?: number;
  profit_margin?: number;
}

export interface TimeSeriesPoint {
  date: string;
  revenue?: number;
  units_sold?: number;
}

export interface TopProduct {
  product_name: string;
  revenue: number;
  units_sold: number;
}

export interface CategoryPerformance {
  category: string;
  revenue: number;
  units_sold: number;
}

export interface InventoryItem {
  product_name: string;
  category: string;
  current_stock: number;
  unit_price: number;
  daily_demand: number;
  demand_7d: number;
  reorder_point: number;
  safety_stock: number;
  status: string;
  alert?: string;
  recommended_reorder: number;
}

export interface MLModelInfo {
  id: number;
  business_id: number;
  dataset_id: number;
  product_name: string;
  model_type: string;
  metrics?: {
    mae?: number;
    rmse?: number;
    mape?: number;
  };
  created_at: string;
}

export interface ForecastResponse {
  product: string;
  model_type: string;
  metrics?: {
    mae?: number;
    rmse?: number;
    mape?: number;
  };
  history: Array<{ date: string; quantity: number }>;
  forecast: Array<{ date: string; quantity: number }>;
}

export const api = {
  // AUTHENTICATION

  async register(data: {
    name: string;
    email: string;
    password: string;
  }): Promise<AuthResponse> {
    const res = await request('/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    if (!res.ok) {
      throw new Error(await getError(res, 'Registration failed'));
    }

    const result: AuthResponse = await res.json();
    auth.setToken(result.access_token);
    return result;
  },

  async login(data: {
    email: string;
    password: string;
  }): Promise<AuthResponse> {
    // FastAPI OAuth2PasswordRequestForm expects form data.
    // The email must be sent using the username field.

    const formData = new URLSearchParams();
    formData.append('username', data.email);
    formData.append('password', data.password);

    const res = await request('/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: formData.toString()
    });

    if (!res.ok) {
      throw new Error(await getError(res, 'Login failed'));
    }

    const result: AuthResponse = await res.json();
    auth.setToken(result.access_token);
    return result;
  },

  async getCurrentUser(): Promise<User> {
    const res = await request('/auth/me');

    if (!res.ok) {
      throw new Error(await getError(res, 'Failed to get user'));
    }

    return res.json();
  },

  logout() {
    auth.clearToken();
  },

  // BUSINESSES

  async getBusinesses(): Promise<Business[]> {
    const res = await request('/businesses/');

    if (!res.ok) {
      throw new Error(await getError(res, 'Failed to fetch businesses'));
    }

    return res.json();
  },

  async createBusiness(data: {
    name: string;
    type?: string;
    description?: string;
    contact_email?: string;
  }): Promise<Business> {
    const res = await request('/businesses/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    if (!res.ok) {
      throw new Error(await getError(res, 'Failed to create business'));
    }

    return res.json();
  },

  // DATASETS

  async getDatasets(businessId: number): Promise<DatasetMeta[]> {
    const res = await request(`/datasets/${businessId}`);

    if (!res.ok) {
      throw new Error(await getError(res, 'Failed to fetch datasets'));
    }

    return res.json();
  },

  async uploadDataset(businessId: number, file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await request(`/datasets/${businessId}`, {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      throw new Error(await getError(res, 'Failed to upload dataset'));
    }

    return res.json();
  },

  async previewDataset(datasetId: number): Promise<any[]> {
    const res = await request(`/datasets/preview/${datasetId}`);

    if (!res.ok) {
      throw new Error(await getError(res, 'Failed to preview dataset'));
    }

    return res.json();
  },

  // ANALYTICS

  async getSummary(businessId: number): Promise<AnalyticsSummary> {
    const res = await request(`/analytics/summary/${businessId}`);

    if (!res.ok) {
      throw new Error(await getError(res, 'Failed to fetch analytics summary'));
    }

    return res.json();
  },

  async getSalesTrend(businessId: number): Promise<{ points: TimeSeriesPoint[] }> {
    const res = await request(`/analytics/sales-trend/${businessId}`);

    if (!res.ok) {
      throw new Error(await getError(res, 'Failed to fetch sales trend'));
    }

    return res.json();
  },

  async getTopProducts(businessId: number): Promise<TopProduct[]> {
    const res = await request(`/analytics/top-products/${businessId}`);

    if (!res.ok) {
      throw new Error(await getError(res, 'Failed to fetch top products'));
    }

    return res.json();
  },

  async getCategoryPerformance(businessId: number): Promise<CategoryPerformance[]> {
    const res = await request(`/analytics/category-performance/${businessId}`);

    if (!res.ok) {
      throw new Error(await getError(res, 'Failed to fetch category performance'));
    }

    return res.json();
  },

  // INVENTORY

  async getInventory(businessId: number): Promise<{
    lead_time_days: number;
    safety_stock: number;
    items: InventoryItem[];
    has_stock_data?: boolean;
  }> {
    const res = await request(`/inventory/${businessId}`);

    if (!res.ok) {
      throw new Error(await getError(res, 'Failed to fetch inventory'));
    }

    return res.json();
  },

  // MACHINE LEARNING

  async getModels(businessId: number): Promise<MLModelInfo[]> {
    const res = await request(`/ml/models/${businessId}`);

    if (!res.ok) {
      throw new Error(await getError(res, 'Failed to fetch ML models'));
    }

    return res.json();
  },

  async startTraining(businessId: number): Promise<{ status: string }> {
    const res = await request(`/ml/train/${businessId}`, {
      method: 'POST'
    });

    if (!res.ok) {
      throw new Error(await getError(res, 'Failed to start ML training'));
    }

    return res.json();
  },

  // FORECASTING

  async getForecast(
    businessId: number,
    productName: string,
    days: number = 7
  ): Promise<ForecastResponse> {
    const res = await request(
      `/forecast/forecast/${businessId}/${encodeURIComponent(productName)}?days=${days}`
    );

    if (!res.ok) {
      throw new Error(await getError(res, 'Failed to fetch forecast'));
    }

    return res.json();
  },

  // AI ASSISTANT

  async askAssistant(
    businessId: number,
    question: string
  ): Promise<{
    answer: string;
    grounded_data?: string[];
    gemini_active?: boolean;
  }> {
    const res = await request(`/assistant/${businessId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ question })
    });

    if (!res.ok) {
      throw new Error(
        await getError(res, 'Failed to communicate with AI Assistant')
      );
    }

    return res.json();
  }
};
