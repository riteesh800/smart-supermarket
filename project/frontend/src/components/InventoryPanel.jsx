import React, { useEffect, useState, useCallback } from 'react';
import { api } from '../services/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';

const COLORS = ['#00d4ff', '#7c3aed', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#6366f1', '#14b8a6',
                '#06b6d4', '#a855f7', '#22c55e', '#eab308', '#f43f5e', '#d946ef', '#8b5cf6'];

export default function InventoryPanel() {
  const [inventory, setInventory] = useState({ items: [], total: 0, page: 1, pages: 1 });
  const [lowStock, setLowStock] = useState([]);
  const [expiring, setExpiring] = useState([]);
  const [byCategory, setByCategory] = useState([]);
  const [categories, setCategories] = useState([]);
  const [search, setSearch] = useState('');
  const [catFilter, setCatFilter] = useState('');
  const [page, setPage] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const [restocking, setRestocking] = useState(null);
  const [form, setForm] = useState({
    name: '', category: 'Dairy', price: '', cost: '',
    supplier: '', shelf_life_days: 30, unit: 'piece',
    initial_stock: 50, max_stock: 200, reorder_point: 20
  });
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [inv, low, exp, cat, cats] = await Promise.all([
        api.getInventory(page, 50, search, catFilter),
        api.getLowStock(),
        api.getExpiringSoon(),
        api.getInventoryByCategory(),
        api.getCategories()
      ]);
      setInventory(inv);
      setLowStock(low);
      setExpiring(exp);
      setByCategory(cat);
      setCategories(cats);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, [page, search, catFilter]);

  useEffect(() => { loadData(); }, [loadData]);

  // Debounced search
  const [searchInput, setSearchInput] = useState('');
  useEffect(() => {
    const timer = setTimeout(() => { setSearch(searchInput); setPage(1); }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  async function handleAddProduct(e) {
    e.preventDefault();
    try {
      await api.addProduct({
        ...form,
        price: parseFloat(form.price),
        cost: form.cost ? parseFloat(form.cost) : null,
        shelf_life_days: parseInt(form.shelf_life_days),
        initial_stock: parseInt(form.initial_stock),
        max_stock: parseInt(form.max_stock),
        reorder_point: parseInt(form.reorder_point),
      });
      setShowModal(false);
      setForm({ name: '', category: 'Dairy', price: '', cost: '', supplier: '', shelf_life_days: 30, unit: 'piece', initial_stock: 50, max_stock: 200, reorder_point: 20 });
      loadData();
    } catch (e) { alert('Error adding product'); }
  }

  async function handleRestock(productId) {
    setRestocking(productId);
    try {
      await api.restockProduct(productId, 50);
      loadData();
    } catch (e) { alert('Error restocking'); }
    setRestocking(null);
  }

  function stockPercent(current, max) {
    return Math.min(100, Math.round((current / (max || 1)) * 100));
  }

  function stockColor(current, reorder) {
    if (current <= reorder) return '#ef4444';
    if (current <= reorder * 1.5) return '#f59e0b';
    return '#10b981';
  }

  return (
    <div>
      <div className="page-header">
        <h2>📦 Inventory Management</h2>
        <p>Track stock levels, manage products, and monitor alerts — {inventory.total} products</p>
      </div>

      {/* KPI Row */}
      <div className="kpi-grid">
        <div className="kpi-card blue">
          <div className="kpi-icon">📦</div>
          <div className="kpi-label">Total Products</div>
          <div className="kpi-value">{inventory.total}</div>
        </div>
        <div className="kpi-card red">
          <div className="kpi-icon">🚨</div>
          <div className="kpi-label">Low Stock</div>
          <div className="kpi-value">{lowStock.length}</div>
        </div>
        <div className="kpi-card orange">
          <div className="kpi-icon">⏰</div>
          <div className="kpi-label">Expiring Soon</div>
          <div className="kpi-value">{expiring.length}</div>
        </div>
        <div className="kpi-card green">
          <div className="kpi-icon">📊</div>
          <div className="kpi-label">Categories</div>
          <div className="kpi-value">{byCategory.length}</div>
        </div>
        <div className="kpi-card purple">
          <div className="kpi-icon">➕</div>
          <div className="kpi-label">Add Product</div>
          <div>
            <button className="btn btn-primary" onClick={() => setShowModal(true)} style={{marginTop: 8}}>
              + New Product
            </button>
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Stock by Category */}
        <div className="card">
          <div className="card-title">Stock by Category</div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byCategory}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="category" tick={{ fill: '#9898b8', fontSize: 10 }} angle={-25} textAnchor="end" height={60} />
                <YAxis tick={{ fill: '#9898b8', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(100,100,255,0.2)', borderRadius: 10, color: '#e8e8f0' }} />
                <Bar dataKey="total_stock" fill="#00d4ff" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Distribution Pie */}
        <div className="card">
          <div className="card-title">Product Distribution</div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={byCategory} dataKey="product_count" nameKey="category" cx="50%" cy="50%"
                  outerRadius={100} innerRadius={55} paddingAngle={2}
                  label={({ category, product_count }) => `${category}: ${product_count}`}
                  labelLine={{ stroke: '#6868a0' }}
                >
                  {byCategory.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(100,100,255,0.2)', borderRadius: 10, color: '#e8e8f0' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Expiring Soon */}
      {expiring.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-title">⏰ Expiring Soon ({expiring.length})</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 8 }}>
            {expiring.slice(0, 8).map(item => (
              <div key={item.product_id} className="alert-row" style={{ borderColor: 'rgba(245, 158, 11, 0.15)', background: 'rgba(245, 158, 11, 0.05)' }}>
                <div className="alert-icon">⏰</div>
                <div className="alert-info">
                  <div className="alert-name">{item.name}</div>
                  <div className="alert-detail">{Math.round(item.days_remaining)}d remaining • Stock: {item.current_stock}</div>
                </div>
                <span className="badge orange">{Math.round(item.days_remaining)}d</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Low Stock Alerts */}
      {lowStock.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-title">⚠️ Low Stock Alerts ({lowStock.length})</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 8 }}>
            {lowStock.slice(0, 8).map(item => (
              <div className="alert-row" key={item.product_id}>
                <div className="alert-icon">🔴</div>
                <div className="alert-info">
                  <div className="alert-name">{item.name}</div>
                  <div className="alert-detail">{item.category} • Stock: {item.current_stock} / Reorder: {item.reorder_point}</div>
                </div>
                <button className="btn btn-primary" style={{ padding: '6px 12px', fontSize: 12 }}
                  onClick={() => handleRestock(item.product_id)}
                  disabled={restocking === item.product_id}>
                  {restocking === item.product_id ? '...' : '🔄 Restock'}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search & Filter Bar */}
      <div className="card">
        <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
          <div className="card-title" style={{ marginBottom: 0, flex: 1 }}>All Products</div>
          <input className="search-input" placeholder="🔍 Search products..."
            value={searchInput} onChange={e => setSearchInput(e.target.value)} />
          <select className="filter-select" value={catFilter}
            onChange={e => { setCatFilter(e.target.value); setPage(1); }}>
            <option value="">All Categories</option>
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>ID</th><th>Product</th><th>Category</th><th>Price</th>
                <th>Stock</th><th>Status</th><th>Location</th><th>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="8" style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>Loading...</td></tr>
              ) : (inventory.items || []).map(item => (
                <tr key={item.product_id}>
                  <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{item.product_id}</td>
                  <td style={{ fontWeight: 600 }}>{item.name}</td>
                  <td><span className="badge blue">{item.category}</span></td>
                  <td>₹{item.price?.toFixed(2)}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span>{item.current_stock}</span>
                      <div className="stock-bar">
                        <div className="stock-bar-fill" style={{
                          width: `${stockPercent(item.current_stock, item.max_stock)}%`,
                          background: stockColor(item.current_stock, item.reorder_point)
                        }} />
                      </div>
                    </div>
                  </td>
                  <td>
                    {item.current_stock <= item.reorder_point
                      ? <span className="badge red">Low</span>
                      : <span className="badge green">OK</span>}
                  </td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{item.warehouse_location}</td>
                  <td>
                    {item.current_stock <= item.reorder_point && (
                      <button className="btn btn-primary" style={{ padding: '4px 10px', fontSize: 11 }}
                        onClick={() => handleRestock(item.product_id)}
                        disabled={restocking === item.product_id}>
                        {restocking === item.product_id ? '...' : 'Restock'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {inventory.pages > 1 && (
          <div className="pagination">
            <button className="btn btn-secondary" disabled={page <= 1}
              onClick={() => setPage(p => Math.max(1, p - 1))}>← Prev</button>
            <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              Page {inventory.page} of {inventory.pages} ({inventory.total} products)
            </span>
            <button className="btn btn-secondary" disabled={page >= inventory.pages}
              onClick={() => setPage(p => Math.min(inventory.pages, p + 1))}>Next →</button>
          </div>
        )}
      </div>

      {/* Add Product Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3>➕ Add New Product</h3>
            <form onSubmit={handleAddProduct}>
              <div className="form-group">
                <label>Product Name</label>
                <input required value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="e.g. Organic Oat Milk 1L" />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Category</label>
                  <select value={form.category} onChange={e => setForm({...form, category: e.target.value})}>
                    {categories.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>Unit</label>
                  <select value={form.unit} onChange={e => setForm({...form, unit: e.target.value})}>
                    {['piece','pack','kg','liter'].map(u => <option key={u} value={u}>{u}</option>)}
                  </select>
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Price (₹)</label>
                  <input required type="number" step="0.01" min="0" value={form.price} onChange={e => setForm({...form, price: e.target.value})} />
                </div>
                <div className="form-group">
                  <label>Cost (₹)</label>
                  <input type="number" step="0.01" min="0" value={form.cost} onChange={e => setForm({...form, cost: e.target.value})} />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Supplier</label>
                  <input value={form.supplier} onChange={e => setForm({...form, supplier: e.target.value})} placeholder="Optional" />
                </div>
                <div className="form-group">
                  <label>Shelf Life (days)</label>
                  <input type="number" min="1" value={form.shelf_life_days} onChange={e => setForm({...form, shelf_life_days: e.target.value})} />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Initial Stock</label>
                  <input type="number" min="0" value={form.initial_stock} onChange={e => setForm({...form, initial_stock: e.target.value})} />
                </div>
                <div className="form-group">
                  <label>Reorder Point</label>
                  <input type="number" min="0" value={form.reorder_point} onChange={e => setForm({...form, reorder_point: e.target.value})} />
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Add Product</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
