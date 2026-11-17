
import React, { useEffect, useMemo, useState } from 'react';
import {
  api,
  auth,
  type User,
  type Business,
  type DatasetMeta,
  type AnalyticsSummary,
  type TimeSeriesPoint,
  type TopProduct,
  type CategoryPerformance,
  type InventoryItem,
  type MLModelInfo,
  type ForecastResponse
} from './services/api';
import './index.css';

type NavTab =
  | 'overview' | 'sales' | 'products' | 'inventory'
  | 'datasets' | 'ml_training' | 'forecasting'
  | 'assistant' | 'settings';

type AuthMode = 'login' | 'register';

const navGroups = [
  {
    title: 'WORKSPACE',
    items: [
      { id: 'overview' as NavTab, icon: '⌂', label: 'Overview' },
      { id: 'sales' as NavTab, icon: '↗', label: 'Sales Analytics' },
      { id: 'products' as NavTab, icon: '◇', label: 'Products' },
      { id: 'inventory' as NavTab, icon: '▤', label: 'Inventory' }
    ]
  },
  {
    title: 'INTELLIGENCE',
    items: [
      { id: 'ml_training' as NavTab, icon: '✳', label: 'ML Training' },
      { id: 'forecasting' as NavTab, icon: '⌁', label: 'Demand Forecasting' },
      { id: 'assistant' as NavTab, icon: '✧', label: 'AI Assistant' }
    ]
  },
  {
    title: 'MANAGEMENT',
    items: [
      { id: 'datasets' as NavTab, icon: '▧', label: 'Datasets' },
      { id: 'settings' as NavTab, icon: '⚙', label: 'Settings' }
    ]
  }
];

const pageTitles: Record<NavTab, string> = {
  overview: 'Overview',
  sales: 'Sales analytics',
  products: 'Product performance',
  inventory: 'Inventory intelligence',
  datasets: 'Dataset management',
  ml_training: 'Machine learning',
  forecasting: 'Demand forecasting',
  assistant: 'AI business assistant',
  settings: 'Workspace settings'
};

function money(value?: number | null) {
  if (value == null || !Number.isFinite(Number(value))) return '—';
  return `$${Number(value).toLocaleString(undefined, {
    maximumFractionDigits: 2
  })}`;
}

function number(value?: number | null) {
  if (value == null || !Number.isFinite(Number(value))) return '—';
  return Number(value).toLocaleString();
}

function shortDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function initials(value?: string) {
  return (value || 'User')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part[0].toUpperCase())
    .join('');
}

function AuthScreen({
  mode,
  setMode,
  onSuccess
}: {
  mode: AuthMode;
  setMode: (mode: AuthMode) => void;
  onSuccess: (user: User | null) => void;
}) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError('');

    try {
      const result = mode === 'register'
        ? await api.register({
            name: name.trim(),
            email: email.trim(),
            password
          })
        : await api.login({
            email: email.trim(),
            password
          });

      onSuccess(result.user);
    } catch (err: any) {
      setError(err.message || 'Unable to authenticate. Please try again.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-screen">
      <div className="auth-decoration auth-decoration-one" />
      <div className="auth-decoration auth-decoration-two" />

      <div className="auth-brand">
        <div className="brand-mark">O</div>
        <div>
          <div className="brand-name">ORIEN</div>
          <div className="brand-caption">BUSINESS INTELLIGENCE</div>
        </div>
      </div>

      <div className="auth-layout">
        <section className="auth-story">
          <span className="eyebrow">
            <span className="eyebrow-dot" /> INTELLIGENCE, MADE SIMPLE
          </span>

          <h1>
            See your business
            <br />
            <em>with clarity.</em>
          </h1>

          <p>
            Turn your business data into meaningful insights.
            Understand performance, anticipate demand, and make
            confident decisions — all in one workspace.
          </p>

          <div className="auth-feature-list">
            <div className="auth-feature">
              <span className="feature-icon">↗</span>
              <div>
                <strong>Understand performance</strong>
                <small>Clear sales and revenue insights</small>
              </div>
            </div>

            <div className="auth-feature">
              <span className="feature-icon">⌁</span>
              <div>
                <strong>Plan what comes next</strong>
                <small>Forecast product demand with ML</small>
              </div>
            </div>

            <div className="auth-feature">
              <span className="feature-icon">✧</span>
              <div>
                <strong>Make smarter decisions</strong>
                <small>AI-powered business assistance</small>
              </div>
            </div>
          </div>

          <div className="auth-note">
            <span>✦</span> Your data. Your workspace. Your decisions.
          </div>
        </section>

        <section className="auth-card">
          <div className="auth-card-top">
            <span className="auth-card-kicker">YOUR WORKSPACE AWAITS</span>
            <div className="auth-card-symbol">✳</div>
          </div>

          <h2>{mode === 'login' ? 'Welcome back' : 'Create your account'}</h2>

          <p className="auth-subtitle">
            {mode === 'login'
              ? 'Sign in to continue to your business dashboard.'
              : 'Start building a clearer picture of your business.'}
          </p>

          <div className="auth-tabs">
            <button
              className={mode === 'login' ? 'selected' : ''}
              onClick={() => {
                setMode('login');
                setError('');
              }}
            >
              Sign in
            </button>

            <button
              className={mode === 'register' ? 'selected' : ''}
              onClick={() => {
                setMode('register');
                setError('');
              }}
            >
              Create account
            </button>
          </div>

          <form onSubmit={submit} className="auth-form">
            {mode === 'register' && (
              <label className="field-label">
                Full name
                <input
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="Your name"
                  required
                  autoComplete="name"
                />
              </label>
            )}

            <label className="field-label">
              Email address
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                autoComplete="email"
              />
            </label>

            <label className="field-label">
              Password
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                minLength={6}
                autoComplete={
                  mode === 'login' ? 'current-password' : 'new-password'
                }
              />
            </label>

            {error && <div className="auth-error">{error}</div>}

            <button className="auth-submit" type="submit" disabled={busy}>
              {busy
                ? 'Please wait…'
                : mode === 'login'
                  ? 'Sign in to workspace'
                  : 'Create my account'}
              <span>→</span>
            </button>
          </form>

          <div className="auth-divider"><span>OR</span></div>

          <button
            className="demo-access"
            onClick={() => onSuccess(null)}
          >
            Explore the public demo <span>↗</span>
          </button>

          <p className="auth-privacy">
            Public demo is available without an account.
            Private business data remains protected.
          </p>
        </section>
      </div>

      <div className="auth-footer">
        <span>ORIEN BUSINESS INTELLIGENCE</span>
        <span>Designed for clearer decisions · © 2026</span>
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  note,
  icon,
  tone
}: {
  label: string;
  value: string;
  note: string;
  icon: string;
  tone: string;
}) {
  return (
    <div className="metric-card">
      <div className="metric-top">
        <span className="metric-label">{label}</span>
        <span className={`metric-icon ${tone}`}>{icon}</span>
      </div>
      <div className="metric-value">{value}</div>
      <div className="metric-note">{note}</div>
    </div>
  );
}

function LineChart({ points }: { points: TimeSeriesPoint[] }) {
  const values = points.slice(-14);

  if (!values.length) {
    return (
      <div className="empty-chart">
        Upload a dataset with date and revenue columns to see your sales trend.
      </div>
    );
  }

  const nums = values.map(p => Number(p.revenue || 0));
  const max = Math.max(...nums, 1);
  const min = Math.min(...nums, 0);
  const range = Math.max(max - min, 1);

  const coords = nums.map((value, index) => ({
    x: 35 + (index * 630) / Math.max(nums.length - 1, 1),
    y: 190 - ((value - min) / range) * 150
  }));

  const line = coords.map(p => `${p.x},${p.y}`).join(' ');
  const area = `35,190 ${line} 665,190`;

  return (
    <div className="chart-wrap">
      <div className="chart-legend">
        <span className="legend-dot" /> Revenue
      </div>

      <svg
        viewBox="0 0 700 230"
        className="line-chart"
        role="img"
        aria-label="Revenue trend chart"
      >
        {[40, 90, 140, 190].map(y => (
          <line
            key={y}
            x1="35"
            y1={y}
            x2="665"
            y2={y}
            className="chart-gridline"
          />
        ))}

        <polygon points={area} className="chart-area" />
        <polyline points={line} className="chart-line" />

        {coords.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r="3.5"
            className="chart-point"
          />
        ))}

        {values.map((p, i) =>
          i % Math.max(1, Math.ceil(values.length / 7)) === 0 ||
          i === values.length - 1 ? (
            <text
              key={i}
              x={coords[i].x}
              y="216"
              textAnchor="middle"
              className="chart-label"
            >
              {shortDate(p.date)}
            </text>
          ) : null
        )}
      </svg>

      <div className="chart-range">
        <span>Lowest: {money(min)}</span>
        <span>Highest: {money(max)}</span>
      </div>
    </div>
  );
}

function DonutChart({ categories }: { categories: CategoryPerformance[] }) {
  const sorted = categories
    .filter(c => Number(c.revenue) > 0)
    .slice(0, 5);

  const total = sorted.reduce(
    (sum, c) => sum + Number(c.revenue || 0),
    0
  );

  const colors = ['#6f8975', '#c28c62', '#a9b9a7', '#8d7892', '#d6b995'];

  let running = 0;

  const gradient = total > 0
    ? sorted.map((item, index) => {
        const start = running;
        running += (Number(item.revenue) / total) * 100;
        return `${colors[index % colors.length]} ${start}% ${running}%`;
      }).join(', ')
    : '#e9e8e1 0% 100%';

  return (
    <div className="donut-layout">
      <div
        className="donut"
        style={{ background: `conic-gradient(${gradient})` }}
      >
        <div className="donut-hole">
          <strong>{total ? money(total) : '—'}</strong>
          <span>Total revenue</span>
        </div>
      </div>

      <div className="donut-legend">
        {sorted.length ? sorted.map((item, index) => (
          <div className="donut-legend-item" key={item.category}>
            <span
              className="donut-color"
              style={{ background: colors[index % colors.length] }}
            />
            <span className="donut-category">{item.category}</span>
            <strong>
              {total
                ? `${((Number(item.revenue) / total) * 100).toFixed(0)}%`
                : '0%'}
            </strong>
          </div>
        )) : (
          <div className="muted-text">
            Category data will appear after uploading a dataset.
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [authMode, setAuthMode] = useState<AuthMode>('login');
  const [showAuth, setShowAuth] = useState(!auth.isLoggedIn());

  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [selectedBizId, setSelectedBizId] = useState<number | null>(null);
  const [currentTab, setCurrentTab] = useState<NavTab>('overview');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [showNewBizModal, setShowNewBizModal] = useState(false);
  const [newBizName, setNewBizName] = useState('');
  const [newBizType, setNewBizType] = useState('Retail');
  const [newBizEmail, setNewBizEmail] = useState('');

  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [salesTrend, setSalesTrend] = useState<TimeSeriesPoint[]>([]);
  const [topProducts, setTopProducts] = useState<TopProduct[]>([]);
  const [categories, setCategories] = useState<CategoryPerformance[]>([]);
  const [datasets, setDatasets] = useState<DatasetMeta[]>([]);

  const [inventory, setInventory] = useState<{
    lead_time_days: number;
    safety_stock: number;
    items: InventoryItem[];
    has_stock_data?: boolean;
  } | null>(null);

  const [models, setModels] = useState<MLModelInfo[]>([]);
  const [selectedForecastProduct, setSelectedForecastProduct] = useState('');
  const [forecastDays, setForecastDays] = useState(7);
  const [forecastData, setForecastData] = useState<ForecastResponse | null>(null);

  const [chatMessages, setChatMessages] = useState<
    Array<{ sender: 'user' | 'assistant'; text: string }>
  >([
    {
      sender: 'assistant',
      text: 'Hello! I am your AI Business Assistant. Ask me about revenue, sales trends, product performance, inventory risks, or demand forecasts.'
    }
  ]);

  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState('');

  const currentBiz =
    businesses.find(b => b.id === selectedBizId) || null;

  const isDemoBusiness = !!currentBiz && (
    !!currentBiz.is_public ||
    !!currentBiz.is_read_only ||
    currentBiz.name.trim().toLowerCase() === 'demo'
  );

  const isReadOnly = !user || isDemoBusiness;
  const hasDataset = datasets.length > 0;

  const latestDatasetId = datasets.length
    ? Math.max(...datasets.map(d => Number(d.id)))
    : null;

  const currentDatasetModels = latestDatasetId === null
    ? []
    : models.filter(m => Number(m.dataset_id) === latestDatasetId);

  const loadBusinesses = async (preferredId?: number | null) => {
    try {
      setLoading(true);
      setError('');

      const list = await api.getBusinesses();
      setBusinesses(list);

      setSelectedBizId(previous => {
        if (preferredId && list.some(b => b.id === preferredId)) {
          return preferredId;
        }

        if (previous && list.some(b => b.id === previous)) {
          return previous;
        }

        return list[0]?.id ?? null;
      });
    } catch (err: any) {
      setError(err.message || 'Could not load businesses.');
    } finally {
      setLoading(false);
    }
  };

  const loadDashboardData = async (businessId: number) => {
    setLoading(true);
    setError('');

    try {
      const [sum, trend, top, cats, dsets, inv, mList] =
        await Promise.all([
          api.getSummary(businessId).catch(() => null),
          api.getSalesTrend(businessId).catch(() => ({ points: [] })),
          api.getTopProducts(businessId).catch(() => []),
          api.getCategoryPerformance(businessId).catch(() => []),
          api.getDatasets(businessId).catch(() => []),
          api.getInventory(businessId).catch(() => null),
          api.getModels(businessId).catch(() => [])
        ]);

      setSummary(sum);
      setSalesTrend(trend?.points || []);
      setTopProducts(top || []);
      setCategories(cats || []);
      setDatasets(dsets || []);
      setInventory(inv);
      setModels(mList || []);

      const newestId = dsets?.length
        ? Math.max(...dsets.map((d: any) => Number(d.id)))
        : null;

      const newestModels = newestId === null
        ? []
        : (mList || []).filter(
            (m: any) => Number(m.dataset_id) === newestId
          );

      if (newestModels.length) {
        setSelectedForecastProduct(previous =>
          newestModels.some((m: any) => m.product_name === previous)
            ? previous
            : newestModels[0].product_name
        );
      } else {
        setSelectedForecastProduct('');
        setForecastData(null);
      }
    } catch (err: any) {
      setError(err.message || 'Unable to load dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let active = true;

    const verifySession = async () => {
      if (auth.isLoggedIn()) {
        try {
          const currentUser = await api.getCurrentUser();
          if (active) setUser(currentUser);
        } catch {
          auth.clearToken();
          if (active) setUser(null);
        }
      }

      if (active) {
        await loadBusinesses();
        if (active) setAuthChecked(true);
      }
    };

    verifySession();

    const handleExpired = () => {
      setUser(null);
      setShowAuth(true);
      setAuthMode('login');
    };

    window.addEventListener('auth-expired', handleExpired);

    return () => {
      active = false;
      window.removeEventListener('auth-expired', handleExpired);
    };
  }, []);

  useEffect(() => {
    if (selectedBizId !== null) {
      loadDashboardData(selectedBizId);
    } else {
      setSummary(null);
      setSalesTrend([]);
      setTopProducts([]);
      setCategories([]);
      setDatasets([]);
      setInventory(null);
      setModels([]);
    }
  }, [selectedBizId]);

  const handleAuthSuccess = async (loggedInUser: User | null) => {
    if (!loggedInUser) {
      setShowAuth(false);
      setUser(null);
      await loadBusinesses();
      return;
    }

    setUser(loggedInUser);
    setShowAuth(false);
    await loadBusinesses();
  };

  const handleLogout = () => {
    api.logout();
    auth.clearToken();

    setUser(null);
    setShowAuth(true);
    setAuthMode('login');

    setBusinesses([]);
    setSelectedBizId(null);
    setCurrentTab('overview');

    setSummary(null);
    setSalesTrend([]);
    setTopProducts([]);
    setCategories([]);
    setDatasets([]);
    setInventory(null);
    setModels([]);
    setForecastData(null);

    void loadBusinesses();
  };

  const handleCreateBusiness = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!user) {
      setShowAuth(true);
      return;
    }

    if (!newBizName.trim()) return;

    try {
      setLoading(true);

      const created = await api.createBusiness({
        name: newBizName.trim(),
        type: newBizType,
        contact_email: newBizEmail || undefined
      });

      setShowNewBizModal(false);
      setNewBizName('');
      setNewBizEmail('');

      await loadBusinesses(created.id);
    } catch (err: any) {
      alert(err.message || 'Unable to create business.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!selectedBizId || !uploadFile || isReadOnly) return;

    try {
      setUploading(true);
      setUploadMessage('');

      const result = await api.uploadDataset(selectedBizId, uploadFile);

      setUploadMessage(
        `"${uploadFile.name}" uploaded successfully · ${result.dataset?.row_count || 0} rows processed.`
      );

      setUploadFile(null);
      await loadDashboardData(selectedBizId);
    } catch (err: any) {
      setUploadMessage(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleStartTraining = async () => {
    if (!selectedBizId || isReadOnly) return;

    try {
      setLoading(true);
      await api.startTraining(selectedBizId);

      alert(
        'Model training started. Refresh the page shortly to view the updated models.'
      );

      window.setTimeout(() => {
        if (selectedBizId) void loadDashboardData(selectedBizId);
      }, 3000);
    } catch (err: any) {
      alert(err.message || 'Training could not be started.');
    } finally {
      setLoading(false);
    }
  };

  const handleFetchForecast = async (product: string, days: number) => {
    if (!selectedBizId || !product) return;

    try {
      const result = await api.getForecast(
        selectedBizId,
        product,
        days
      );
      setForecastData(result);
    } catch (err: any) {
      setForecastData(null);
      console.error('Forecast error:', err);
    }
  };

  useEffect(() => {
    if (
      currentTab === 'forecasting' &&
      selectedBizId &&
      selectedForecastProduct
    ) {
      void handleFetchForecast(selectedForecastProduct, forecastDays);
    }
  }, [
    currentTab,
    selectedForecastProduct,
    forecastDays,
    selectedBizId
  ]);

  const handleSendMessage = async (prompt?: string) => {
    const message = prompt || chatInput;

    if (!message.trim() || !selectedBizId || chatLoading) return;

    setChatMessages(prev => [
      ...prev,
      { sender: 'user', text: message }
    ]);

    if (!prompt) setChatInput('');
    setChatLoading(true);

    try {
      const result = await api.askAssistant(selectedBizId, message);

      setChatMessages(prev => [
        ...prev,
        { sender: 'assistant', text: result.answer }
      ]);
    } catch (err: any) {
      setChatMessages(prev => [
        ...prev,
        {
          sender: 'assistant',
          text: `I couldn't complete that request: ${err.message}`
        }
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const profitMargin = summary?.profit_margin != null
    ? `${(summary.profit_margin * 100).toFixed(1)}% margin`
    : 'Profit data not available';

  const aiInsight = useMemo(() => {
    if (!hasDataset) {
      return 'Upload a business dataset to generate insights tailored to your records.';
    }

    if (topProducts.length) {
      return `${topProducts[0].product_name} is currently your highest revenue contributor in the available product data. Review its sales trend to plan your next move.`;
    }

    if (categories.length) {
      const best = [...categories].sort(
        (a, b) => Number(b.revenue) - Number(a.revenue)
      )[0];

      return `${best.category} is leading your category revenue. Explore the category breakdown to understand where sales are concentrated.`;
    }

    return 'Your dataset has been processed. Explore the analytics pages to understand the available business metrics.';
  }, [hasDataset, topProducts, categories]);

  if (!authChecked) {
    return (
      <div className="boot-screen">
        <div className="boot-mark">O</div>
        <span>Preparing your workspace…</span>
      </div>
    );
  }

  if (showAuth) {
    return (
      <AuthScreen
        mode={authMode}
        setMode={setAuthMode}
        onSuccess={handleAuthSuccess}
      />
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark">O</div>
          <div>
            <div className="brand-name">ORIEN</div>
            <div className="brand-caption">BUSINESS INTELLIGENCE</div>
          </div>
        </div>

        <div className="workspace-label">YOUR WORKSPACE</div>

        <div className="business-switcher">
          <label>ACTIVE BUSINESS</label>

          <select
            value={selectedBizId ?? ''}
            onChange={e =>
              setSelectedBizId(
                e.target.value ? Number(e.target.value) : null
              )
            }
          >
            {businesses.map(b => (
              <option key={b.id} value={b.id}>
                {b.name}{b.is_public ? ' · Demo' : ''}
              </option>
            ))}
          </select>

          {isDemoBusiness && (
            <span className="demo-pill">PUBLIC DEMO · READ ONLY</span>
          )}

          {user && (
            <button
              className="add-business-button"
              onClick={() => setShowNewBizModal(true)}
            >
              ＋ Add business
            </button>
          )}
        </div>

        <nav className="sidebar-navigation">
          {navGroups.map(group => (
            <div className="nav-group" key={group.title}>
              <div className="nav-group-title">{group.title}</div>

              {group.items.map(item => (
                <button
                  key={item.id}
                  className={`nav-link ${
                    currentTab === item.id ? 'active' : ''
                  }`}
                  onClick={() => setCurrentTab(item.id)}
                >
                  <span className="nav-link-icon">{item.icon}</span>
                  <span>{item.label}</span>
                  {currentTab === item.id && (
                    <span className="nav-active-indicator" />
                  )}
                </button>
              ))}
            </div>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-help">
            <span className="help-sparkle">✧</span>
            <strong>Need a little clarity?</strong>
            <p>
              Your AI assistant is ready to help you understand your business.
            </p>
            <button onClick={() => setCurrentTab('assistant')}>
              Talk to AI <span>→</span>
            </button>
          </div>

          <div className="profile-row">
            <div className="avatar">
              {initials(user?.name || 'Guest')}
            </div>

            <div className="profile-info">
              <strong>{user?.name || 'Guest visitor'}</strong>
              <span>{user?.email || 'Public demo access'}</span>
            </div>

            {user ? (
              <button
                className="logout-button"
                title="Sign out"
                onClick={handleLogout}
              >
                ↗
              </button>
            ) : (
              <button
                className="logout-button"
                title="Sign in"
                onClick={() => setShowAuth(true)}
              >
                ＋
              </button>
            )}
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div>
            <div className="breadcrumb">
              Workspace <span>/</span> {pageTitles[currentTab]}
            </div>
            <h1>{pageTitles[currentTab]}</h1>
            <p className="topbar-subtitle">
              {currentBiz
                ? `A clear view of ${currentBiz.name}`
                : 'Your business, thoughtfully understood.'}
            </p>
          </div>

          <div className="topbar-actions">
            <div className="topbar-date">
              <span>◷</span>{' '}
              {new Date().toLocaleDateString(undefined, {
                weekday: 'short',
                month: 'short',
                day: 'numeric'
              })}
            </div>

            <button
              className="icon-button"
              title="Refresh data"
              onClick={() =>
                selectedBizId && void loadDashboardData(selectedBizId)
              }
              disabled={loading}
            >
              ↻
            </button>

            {!user && (
              <button
                className="topbar-login"
                onClick={() => setShowAuth(true)}
              >
                Sign in <span>→</span>
              </button>
            )}
          </div>
        </header>

        <div className="content-area">
          {error && (
            <div className="notice notice-error">
              <span>!</span>{error}
            </div>
          )}

          {!selectedBizId ? (
            <section className="welcome-card">
              <span className="eyebrow">WELCOME TO ORIEN</span>
              <h2>
                Your business story
                <br />
                <em>starts with data.</em>
              </h2>
              <p>
                Select the public demo or sign in to open your private
                business workspace.
              </p>
              {!user && (
                <button
                  className="primary-button"
                  onClick={() => setShowAuth(true)}
                >
                  Sign in to get started →
                </button>
              )}
              {user && (
                <button
                  className="primary-button"
                  onClick={() => setShowNewBizModal(true)}
                >
                  Create your business →
                </button>
              )}
            </section>
          ) : (
            <>
              {currentTab === 'overview' && (
                <div className="page-stack">
                  <section className="welcome-strip">
                    <div>
                      <span className="eyebrow">
                        YOUR BUSINESS AT A GLANCE
                      </span>
                      <h2>
                        {user
                          ? `Welcome back, ${user.name.split(' ')[0]}`
                          : 'Explore the business demo'}
                      </h2>
                      <p>
                        {hasDataset
                          ? 'Here is what your business data is telling you today.'
                          : 'Start with a dataset to reveal your business performance and insights.'}
                      </p>
                    </div>

                    <div className="welcome-art">
                      <span className="art-circle art-circle-one" />
                      <span className="art-circle art-circle-two" />
                      <span className="art-leaf">✳</span>
                    </div>
                  </section>

                  {!hasDataset ? (
                    <section className="empty-state-card">
                      <div className="empty-state-icon">▧</div>
                      <span className="eyebrow">
                        DATA FIRST, INSIGHTS NEXT
                      </span>
                      <h3>
                        {isDemoBusiness
                          ? 'The demo workspace is ready to explore'
                          : 'Bring your business data to life'}
                      </h3>
                      <p>
                        {isDemoBusiness
                          ? 'This public demo has no dataset available yet. Sign in to create your own workspace and upload your business records.'
                          : 'Upload a CSV or Excel file. We will use the available columns to build your analytics, product insights, and forecasting workspace.'}
                      </p>
                      {!isReadOnly && (
                        <button
                          className="primary-button"
                          onClick={() => setCurrentTab('datasets')}
                        >
                          Go to dataset upload →
                        </button>
                      )}
                      {isReadOnly && !user && (
                        <button
                          className="primary-button"
                          onClick={() => setShowAuth(true)}
                        >
                          Create an account →
                        </button>
                      )}
                    </section>
                  ) : (
                    <>
                      <div className="metrics-grid">
                        <MetricCard
                          label="Total revenue"
                          value={money(summary?.total_revenue)}
                          note="Revenue from recorded sales"
                          icon="$"
                          tone="sage"
                        />
                        <MetricCard
                          label="Units sold"
                          value={number(summary?.total_units_sold)}
                          note="Total quantity sold"
                          icon="↗"
                          tone="copper"
                        />
                        <MetricCard
                          label="Total profit"
                          value={money(summary?.profit)}
                          note={profitMargin}
                          icon="✧"
                          tone="lavender"
                        />
                        <MetricCard
                          label="Products / categories"
                          value={number(
                            summary?.number_of_products ??
                            categories.length ??
                            topProducts.length
                          )}
                          note={`${datasets.length} dataset(s) available`}
                          icon="◇"
                          tone="blue"
                        />
                      </div>

                      <div className="dashboard-grid dashboard-grid-main">
                        <section className="panel chart-panel">
                          <div className="panel-heading">
                            <div>
                              <span className="eyebrow">
                                PERFORMANCE OVER TIME
                              </span>
                              <h3>Sales & revenue trend</h3>
                              <p>
                                Revenue movement across your available records
                              </p>
                            </div>
                            <span className="panel-icon">⌁</span>
                          </div>
                          <LineChart points={salesTrend} />
                        </section>

                        <section className="panel">
                          <div className="panel-heading">
                            <div>
                              <span className="eyebrow">REVENUE MIX</span>
                              <h3>Category performance</h3>
                              <p>How revenue is distributed</p>
                            </div>
                            <span className="panel-icon">◌</span>
                          </div>
                          <DonutChart categories={categories} />
                        </section>
                      </div>

                      <div className="dashboard-grid dashboard-grid-bottom">
                        <section className="panel">
                          <div className="panel-heading">
                            <div>
                              <span className="eyebrow">WHAT'S SELLING</span>
                              <h3>Top performers</h3>
                              <p>
                                Your highest revenue products or categories
                              </p>
                            </div>
                            <button
                              className="text-link"
                              onClick={() => setCurrentTab('products')}
                            >
                              View all →
                            </button>
                          </div>

                          <div className="product-list">
                            {topProducts.slice(0, 5).map((p, i) => (
                              <div className="product-row" key={p.product_name}>
                                <div className="product-rank">
                                  {String(i + 1).padStart(2, '0')}
                                </div>
                                <div className="product-row-name">
                                  <strong>{p.product_name}</strong>
                                  <span>{number(p.units_sold)} units sold</span>
                                </div>
                                <strong className="product-revenue">
                                  {money(p.revenue)}
                                </strong>
                              </div>
                            ))}

                            {!topProducts.length && (
                              <div className="empty-inline">
                                No product-level performance data is available.
                              </div>
                            )}
                          </div>
                        </section>

                        <section className="panel insight-panel">
                          <div className="insight-heading">
                            <span className="insight-sparkle">✧</span>
                            <span className="eyebrow">AI BUSINESS INSIGHT</span>
                          </div>
                          <h3>A little perspective goes a long way.</h3>
                          <p>{aiInsight}</p>
                          <button
                            className="insight-link"
                            onClick={() => setCurrentTab('assistant')}
                          >
                            Explore with AI assistant <span>→</span>
                          </button>
                        </section>
                      </div>

                      <section className="panel inventory-overview">
                        <div className="panel-heading">
                          <div>
                            <span className="eyebrow">STOCK AWARENESS</span>
                            <h3>Inventory health</h3>
                            <p>
                              Availability based on the columns in your dataset
                            </p>
                          </div>
                          <button
                            className="text-link"
                            onClick={() => setCurrentTab('inventory')}
                          >
                            Open inventory →
                          </button>
                        </div>

                        {inventory?.has_stock_data && inventory.items?.length ? (
                          <div className="inventory-mini-grid">
                            {inventory.items.slice(0, 4).map(item => (
                              <div
                                className="inventory-mini-card"
                                key={item.product_name}
                              >
                                <span
                                  className={`status-dot ${
                                    item.status?.toLowerCase().includes('low')
                                      ? 'warning'
                                      : ''
                                  }`}
                                />
                                <strong>{item.product_name}</strong>
                                <span>
                                  {number(item.current_stock)} units available
                                </span>
                                <small>{item.status}</small>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="stock-unavailable">
                            <span>ⓘ</span>
                            <div>
                              <strong>Stock quantities are not available</strong>
                              <p>
                                Your current dataset does not include a stock
                                quantity column. Upload stock data to enable
                                reorder intelligence.
                              </p>
                            </div>
                          </div>
                        )}
                      </section>
                    </>
                  )}
                </div>
              )}

              {currentTab === 'sales' && (
                <div className="page-stack">
                  <section className="page-intro">
                    <span className="eyebrow">SALES PERFORMANCE</span>
                    <h2>Understand the story behind your numbers.</h2>
                    <p>
                      Explore revenue and sales activity recorded in your dataset.
                    </p>
                  </section>

                  <div className="metrics-grid">
                    <MetricCard label="Total revenue" value={money(summary?.total_revenue)} note="Recorded revenue" icon="$" tone="sage" />
                    <MetricCard label="Units sold" value={number(summary?.total_units_sold)} note="Recorded quantity" icon="↗" tone="copper" />
                    <MetricCard label="Transactions" value={number(summary?.total_transactions)} note="Sales records" icon="▤" tone="lavender" />
                    <MetricCard label="Profit margin" value={summary?.profit_margin != null ? `${(summary.profit_margin * 100).toFixed(1)}%` : '—'} note="When cost data is available" icon="✧" tone="blue" />
                  </div>

                  <section className="panel">
                    <div className="panel-heading">
                      <div>
                        <span className="eyebrow">REVENUE MOVEMENT</span>
                        <h3>Sales trend</h3>
                        <p>Daily revenue and units sold</p>
                      </div>
                    </div>
                    <LineChart points={salesTrend} />
                  </section>

                  <section className="panel">
                    <div className="panel-heading">
                      <div>
                        <span className="eyebrow">TRANSACTION HISTORY</span>
                        <h3>Recent sales records</h3>
                      </div>
                    </div>
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr><th>Date</th><th>Revenue</th><th>Units sold</th></tr>
                        </thead>
                        <tbody>
                          {salesTrend.slice(-30).reverse().map((p, i) => (
                            <tr key={`${p.date}-${i}`}>
                              <td>{p.date}</td>
                              <td>{money(p.revenue)}</td>
                              <td>{number(p.units_sold)}</td>
                            </tr>
                          ))}
                          {!salesTrend.length && (
                            <tr><td colSpan={3} className="table-empty">No sales trend data found.</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </section>
                </div>
              )}

              {currentTab === 'products' && (
                <div className="page-stack">
                  <section className="page-intro">
                    <span className="eyebrow">PRODUCT INTELLIGENCE</span>
                    <h2>Discover your strongest performers.</h2>
                    <p>
                      Compare product and category contribution using your uploaded records.
                    </p>
                  </section>

                  <section className="panel">
                    <div className="panel-heading">
                      <div>
                        <span className="eyebrow">TOP REVENUE CONTRIBUTORS</span>
                        <h3>Product performance</h3>
                      </div>
                    </div>

                    <div className="product-card-grid">
                      {topProducts.map((p, i) => (
                        <div className="product-card" key={p.product_name}>
                          <div className="product-card-top">
                            <span className="product-rank">#{i + 1}</span>
                            <span className="product-card-icon">◇</span>
                          </div>
                          <h3>{p.product_name}</h3>
                          <strong>{money(p.revenue)}</strong>
                          <span className="product-card-caption">Revenue generated</span>
                          <div className="product-card-footer">
                            <span>{number(p.units_sold)} units sold</span>
                            <span>Product insight</span>
                          </div>
                        </div>
                      ))}
                      {!topProducts.length && (
                        <div className="empty-inline">
                          No product-level data available in this dataset.
                        </div>
                      )}
                    </div>
                  </section>

                  <section className="panel">
                    <div className="panel-heading">
                      <div>
                        <span className="eyebrow">CATEGORY BREAKDOWN</span>
                        <h3>Category performance</h3>
                      </div>
                    </div>
                    <DonutChart categories={categories} />
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr><th>Category</th><th>Revenue</th><th>Units sold</th></tr>
                        </thead>
                        <tbody>
                          {categories.map(c => (
                            <tr key={c.category}>
                              <td><strong>{c.category}</strong></td>
                              <td>{money(c.revenue)}</td>
                              <td>{number(c.units_sold)}</td>
                            </tr>
                          ))}
                          {!categories.length && (
                            <tr><td colSpan={3} className="table-empty">No category data available.</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </section>
                </div>
              )}

              {currentTab === 'inventory' && (
                <div className="page-stack">
                  <section className="page-intro">
                    <span className="eyebrow">INVENTORY INTELLIGENCE</span>
                    <h2>Stay ahead of stock requirements.</h2>
                    <p>
                      Monitor stock levels and reorder signals when inventory data is available.
                    </p>
                  </section>

                  {!inventory?.has_stock_data ? (
                    <section className="empty-state-card">
                      <div className="empty-state-icon">▤</div>
                      <h3>Stock data is not available yet</h3>
                      <p>
                        Your dataset contains sales information but no actual
                        stock quantity column. Reorder recommendations need
                        stock data to be reliable.
                      </p>
                      {!isReadOnly && (
                        <button
                          className="primary-button"
                          onClick={() => setCurrentTab('datasets')}
                        >
                          Upload inventory dataset →
                        </button>
                      )}
                    </section>
                  ) : (
                    <>
                      <div className="metrics-grid">
                        <MetricCard label="Products monitored" value={number(inventory.items.length)} note="Items with stock information" icon="◇" tone="sage" />
                        <MetricCard label="Lead time" value={`${inventory.lead_time_days} days`} note="Configured supplier lead time" icon="◷" tone="copper" />
                        <MetricCard label="Safety stock" value={`${inventory.safety_stock} units`} note="Minimum buffer quantity" icon="▤" tone="lavender" />
                        <MetricCard label="Attention needed" value={number(inventory.items.filter(i => i.status?.toLowerCase().includes('low') || i.status?.toLowerCase().includes('reorder')).length)} note="Items to review" icon="!" tone="blue" />
                      </div>

                      <section className="panel">
                        <div className="panel-heading">
                          <div>
                            <span className="eyebrow">STOCK MONITORING</span>
                            <h3>Inventory overview</h3>
                          </div>
                        </div>
                        <div className="table-wrap">
                          <table>
                            <thead>
                              <tr>
                                <th>Product</th>
                                <th>Category</th>
                                <th>Available stock</th>
                                <th>Daily demand</th>
                                <th>Reorder point</th>
                                <th>Status</th>
                                <th>Recommended reorder</th>
                              </tr>
                            </thead>
                            <tbody>
                              {inventory.items.map((item, i) => (
                                <tr key={`${item.product_name}-${i}`}>
                                  <td><strong>{item.product_name}</strong></td>
                                  <td>{item.category || '—'}</td>
                                  <td>{number(item.current_stock)}</td>
                                  <td>{number(item.daily_demand)}</td>
                                  <td>{number(item.reorder_point)}</td>
                                  <td><span className="table-status">{item.status}</span></td>
                                  <td>{item.recommended_reorder > 0 ? `+${number(item.recommended_reorder)} units` : 'No reorder needed'}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </section>
                    </>
                  )}
                </div>
              )}

              {currentTab === 'ml_training' && (
                <div className="page-stack">
                  <section className="page-intro">
                    <span className="eyebrow">MACHINE LEARNING</span>
                    <h2>Build models from your business data.</h2>
                    <p>
                      Train product-level forecasting models and review their evaluation metrics.
                    </p>
                  </section>

                  <section className="panel training-banner">
                    <div>
                      <span className="eyebrow">MODEL WORKSPACE</span>
                      <h3>Ready to improve your forecasts?</h3>
                      <p>Training uses the latest uploaded dataset for this business.</p>
                    </div>
                    <button
                      className="primary-button"
                      disabled={loading || isReadOnly || !hasDataset}
                      onClick={handleStartTraining}
                    >
                      {loading ? 'Working…' : '✳ Train models'}
                    </button>
                  </section>

                  {isReadOnly && (
                    <div className="notice notice-info">
                      The public demo is read-only. Sign in and use your own business workspace to train models.
                    </div>
                  )}

                  <section className="panel">
                    <div className="panel-heading">
                      <div>
                        <span className="eyebrow">TRAINED MODELS</span>
                        <h3>Model performance</h3>
                        <p>Models associated with the latest dataset</p>
                      </div>
                      <span className="count-pill">
                        {currentDatasetModels.length} models
                      </span>
                    </div>
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Product / category</th>
                            <th>Algorithm</th>
                            <th>MAE</th>
                            <th>RMSE</th>
                            <th>MAPE</th>
                            <th>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {currentDatasetModels.map(m => (
                            <tr key={m.id}>
                              <td><strong>{m.product_name}</strong></td>
                              <td>{m.model_type}</td>
                              <td>{m.metrics?.mae ?? '—'}</td>
                              <td>{m.metrics?.rmse ?? '—'}</td>
                              <td>{m.metrics?.mape != null ? `${m.metrics.mape}%` : '—'}</td>
                              <td><span className="success-pill">Ready</span></td>
                            </tr>
                          ))}
                          {!currentDatasetModels.length && (
                            <tr><td colSpan={6} className="table-empty">No models trained for the latest dataset yet.</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </section>
                </div>
              )}

              {currentTab === 'forecasting' && (
                <div className="page-stack">
                  <section className="page-intro">
                    <span className="eyebrow">DEMAND PLANNING</span>
                    <h2>Look ahead with demand forecasts.</h2>
                    <p>
                      Use trained models to estimate future product or category demand.
                    </p>
                  </section>

                  {!currentDatasetModels.length ? (
                    <section className="empty-state-card">
                      <div className="empty-state-icon">⌁</div>
                      <h3>No forecasting models available</h3>
                      <p>
                        Upload a dataset and train models first. Forecasts will be based on the latest trained dataset.
                      </p>
                      <button
                        className="primary-button"
                        onClick={() => setCurrentTab(isReadOnly ? 'datasets' : 'ml_training')}
                      >
                        {isReadOnly ? 'View datasets' : 'Go to ML training'} →
                      </button>
                    </section>
                  ) : (
                    <section className="panel">
                      <div className="forecast-controls">
                        <label className="field-label">
                          Product or category
                          <select
                            value={selectedForecastProduct}
                            onChange={e => setSelectedForecastProduct(e.target.value)}
                          >
                            {currentDatasetModels.map(m => (
                              <option key={m.id} value={m.product_name}>
                                {m.product_name}
                              </option>
                            ))}
                          </select>
                        </label>

                        <label className="field-label">
                          Forecast horizon
                          <select
                            value={forecastDays}
                            onChange={e => setForecastDays(Number(e.target.value))}
                          >
                            <option value={7}>7 days</option>
                            <option value={14}>14 days</option>
                            <option value={30}>30 days</option>
                          </select>
                        </label>
                      </div>

                      {forecastData ? (
                        <>
                          <div className="forecast-summary">
                            <div>
                              <span className="eyebrow">SELECTED MODEL</span>
                              <strong>{forecastData.model_type}</strong>
                            </div>
                            <div>
                              <span className="eyebrow">MODEL MAE</span>
                              <strong>{forecastData.metrics?.mae ?? '—'}</strong>
                            </div>
                            <div>
                              <span className="eyebrow">FORECAST PERIOD</span>
                              <strong>{forecastData.forecast.length} days</strong>
                            </div>
                          </div>

                          <div className="table-wrap">
                            <table>
                              <thead>
                                <tr><th>Forecast date</th><th>Predicted demand</th></tr>
                              </thead>
                              <tbody>
                                {forecastData.forecast.map((f, i) => (
                                  <tr key={`${f.date}-${i}`}>
                                    <td>{f.date}</td>
                                    <td><strong>{number(f.quantity)} units</strong></td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </>
                      ) : (
                        <div className="empty-inline">
                          Choose a product to view its forecast.
                        </div>
                      )}
                    </section>
                  )}
                </div>
              )}

              {currentTab === 'assistant' && (
                <div className="page-stack">
                  <section className="page-intro">
                    <span className="eyebrow">YOUR AI COMPANION</span>
                    <h2>Ask better questions about your business.</h2>
                    <p>
                      Get answers grounded in the business data available in this workspace.
                    </p>
                  </section>

                  <section className="assistant-panel">
                    <div className="assistant-header">
                      <div className="assistant-avatar">✧</div>
                      <div>
                        <strong>Orien AI Assistant</strong>
                        <span><i /> Ready to help with your business</span>
                      </div>
                    </div>

                    <div className="chat-messages">
                      {chatMessages.map((msg, i) => (
                        <div
                          key={i}
                          className={`chat-message ${msg.sender}`}
                        >
                          <div className="chat-message-label">
                            {msg.sender === 'assistant' ? 'ORIEN AI' : 'YOU'}
                          </div>
                          <div>{msg.text}</div>
                        </div>
                      ))}

                      {chatLoading && (
                        <div className="chat-message assistant">
                          <div className="chat-message-label">ORIEN AI</div>
                          <div className="typing-dots">
                            <i /><i /><i />
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="suggestion-list">
                      <span className="eyebrow">TRY ASKING</span>
                      {[
                        'Which products are performing best?',
                        'Summarize my revenue performance.',
                        'Which products may run out of stock soon?',
                        'What is the expected demand for the next 7 days?'
                      ].map(q => (
                        <button key={q} onClick={() => handleSendMessage(q)}>
                          {q} <span>↗</span>
                        </button>
                      ))}
                    </div>

                    <form
                      className="chat-composer"
                      onSubmit={e => {
                        e.preventDefault();
                        void handleSendMessage();
                      }}
                    >
                      <input
                        value={chatInput}
                        onChange={e => setChatInput(e.target.value)}
                        placeholder="Ask anything about this business…"
                      />
                      <button
                        type="submit"
                        disabled={chatLoading || !chatInput.trim()}
                      >
                        Send <span>→</span>
                      </button>
                    </form>
                  </section>
                </div>
              )}

              {currentTab === 'datasets' && (
                <div className="page-stack">
                  <section className="page-intro">
                    <span className="eyebrow">YOUR BUSINESS DATA</span>
                    <h2>Everything begins with a dataset.</h2>
                    <p>
                      Upload CSV or Excel files to power your analytics and intelligence workspace.
                    </p>
                  </section>

                  {isReadOnly ? (
                    <div className="notice notice-info">
                      This workspace is public and read-only. Sign in and select your private business to upload datasets.
                    </div>
                  ) : (
                    <section className="upload-panel">
                      <div className="upload-icon">↥</div>
                      <span className="eyebrow">UPLOAD YOUR DATA</span>
                      <h3>Bring your business records</h3>
                      <p>
                        Choose a CSV or Excel file. Your data will be processed to identify supported business metrics.
                      </p>

                      <form onSubmit={handleUpload}>
                        <label className="file-drop">
                          <input
                            type="file"
                            accept=".csv,.xlsx,.xls"
                            onChange={e =>
                              setUploadFile(e.target.files?.[0] || null)
                            }
                          />
                          <span className="file-drop-icon">＋</span>
                          <strong>
                            {uploadFile
                              ? uploadFile.name
                              : 'Choose a file to upload'}
                          </strong>
                          <small>
                            {uploadFile
                              ? 'Ready to process'
                              : 'CSV or Excel · Select a file from your device'}
                          </small>
                        </label>

                        <button
                          className="primary-button"
                          type="submit"
                          disabled={!uploadFile || uploading}
                        >
                          {uploading ? 'Processing dataset…' : 'Upload & analyse →'}
                        </button>
                      </form>

                      {uploadMessage && (
                        <div
                          className={
                            uploadMessage.startsWith('Upload failed')
                              ? 'upload-result error'
                              : 'upload-result'
                          }
                        >
                          {uploadMessage}
                        </div>
                      )}
                    </section>
                  )}

                  <section className="panel">
                    <div className="panel-heading">
                      <div>
                        <span className="eyebrow">DATA HISTORY</span>
                        <h3>Uploaded datasets</h3>
                        <p>
                          {currentBiz?.name || 'Selected business'} · {datasets.length} file(s)
                        </p>
                      </div>
                    </div>

                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>File name</th>
                            <th>Uploaded</th>
                            <th>Rows</th>
                            <th>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {datasets.map(d => (
                            <tr key={d.id}>
                              <td><strong>{d.filename}</strong></td>
                              <td>{new Date(d.uploaded_at).toLocaleString()}</td>
                              <td>{number(d.row_count)}</td>
                              <td><span className="success-pill">Processed</span></td>
                            </tr>
                          ))}
                          {!datasets.length && (
                            <tr><td colSpan={4} className="table-empty">No datasets uploaded yet.</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </section>
                </div>
              )}

              {currentTab === 'settings' && (
                <div className="page-stack">
                  <section className="page-intro">
                    <span className="eyebrow">WORKSPACE DETAILS</span>
                    <h2>Your business, your settings.</h2>
                    <p>
                      Review the details and configuration of the selected workspace.
                    </p>
                  </section>

                  <section className="panel settings-panel">
                    <div className="panel-heading">
                      <div>
                        <span className="eyebrow">BUSINESS PROFILE</span>
                        <h3>Workspace information</h3>
                      </div>
                    </div>

                    <div className="settings-grid">
                      <div className="settings-item">
                        <span>Business name</span>
                        <strong>{currentBiz?.name || '—'}</strong>
                      </div>
                      <div className="settings-item">
                        <span>Business type</span>
                        <strong>{currentBiz?.type || 'General'}</strong>
                      </div>
                      <div className="settings-item">
                        <span>Contact email</span>
                        <strong>{currentBiz?.contact_email || 'Not provided'}</strong>
                      </div>
                      <div className="settings-item">
                        <span>Workspace access</span>
                        <strong>
                          {isDemoBusiness
                            ? 'Public demo · Read only'
                            : user
                              ? 'Private · Owner access'
                              : 'Guest access'}
                        </strong>
                      </div>
                      <div className="settings-item">
                        <span>Datasets</span>
                        <strong>{datasets.length}</strong>
                      </div>
                      <div className="settings-item">
                        <span>Forecast models</span>
                        <strong>{models.length}</strong>
                      </div>
                    </div>
                  </section>

                  <section className="panel">
                    <div className="panel-heading">
                      <div>
                        <span className="eyebrow">ACCOUNT</span>
                        <h3>Account details</h3>
                      </div>
                    </div>

                    <div className="settings-grid">
                      <div className="settings-item">
                        <span>Name</span>
                        <strong>{user?.name || 'Guest visitor'}</strong>
                      </div>
                      <div className="settings-item">
                        <span>Email</span>
                        <strong>{user?.email || 'Not signed in'}</strong>
                      </div>
                    </div>

                    {user && (
                      <button
                        className="secondary-button logout-action"
                        onClick={handleLogout}
                      >
                        Sign out of account ↗
                      </button>
                    )}
                  </section>
                </div>
              )}
            </>
          )}

          <footer className="page-footer">
            <span>ORIEN · BUSINESS INTELLIGENCE</span>
            <span>Clarity for every business decision.</span>
          </footer>
        </div>
      </main>

      {showNewBizModal && (
        <div
          className="modal-backdrop"
          onMouseDown={e => {
            if (e.target === e.currentTarget) {
              setShowNewBizModal(false);
            }
          }}
        >
          <section className="modal-card">
            <button
              className="modal-close"
              onClick={() => setShowNewBizModal(false)}
            >
              ×
            </button>

            <span className="eyebrow">NEW WORKSPACE</span>
            <h2>Bring a business on board.</h2>
            <p>
              Create a private workspace for your business data and insights.
            </p>

            <form onSubmit={handleCreateBusiness}>
              <label className="field-label">
                Business name
                <input
                  value={newBizName}
                  onChange={e => setNewBizName(e.target.value)}
                  placeholder="e.g. Acme Retailers"
                  required
                />
              </label>

              <label className="field-label">
                Business type
                <input
                  value={newBizType}
                  onChange={e => setNewBizType(e.target.value)}
                  placeholder="e.g. Retail, Apparel, Grocery"
                />
              </label>

              <label className="field-label">
                Contact email
                <input
                  type="email"
                  value={newBizEmail}
                  onChange={e => setNewBizEmail(e.target.value)}
                  placeholder="admin@business.com"
                />
              </label>

              <div className="modal-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setShowNewBizModal(false)}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="primary-button"
                  disabled={loading}
                >
                  Create workspace →
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </div>
  );
}
