// ============================================
// REACT CRUD PAGE STARTER
// ============================================
import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api-client';
import './crud-page.css'; // uses design-system.css tokens

export default function ItemsPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [meta, setMeta] = useState({ total: 0, pages: 0 });
  const [modalOpen, setModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  const limit = 20;

  const fetchItems = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get('/items', { page, limit, search });
      setItems(res.data);
      setMeta(res.meta);
    } catch (err) {
      setError(err.message || 'Failed to load items');
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  const handleDelete = async (id) => {
    if (!confirm('Delete this item?')) {
      return;
    }

    try {
      await api.delete(`/items/${id}`);
      fetchItems();
    } catch (err) {
      setError(err.message);
    }
  };

  const openCreate = () => {
    setEditingItem(null);
    setModalOpen(true);
  };

  const openEdit = (item) => {
    setEditingItem(item);
    setModalOpen(true);
  };

  return (
    <div className="page">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Items</h1>
          <p className="page-subtitle">{meta.total} items total</p>
        </div>
        <button className="btn btn-primary btn-md" onClick={openCreate}>
          + Add Item
        </button>
      </div>

      {/* Search Bar */}
      <div className="card" style={{ marginBottom: 'var(--space-5)' }}>
        <input
          className="input"
          placeholder="Search items..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <div className="flex items-center justify-center" style={{ padding: 'var(--space-10)' }}>
            <div className="spinner" />
          </div>
        ) : error ? (
          <div style={{ padding: 'var(--space-6)', color: 'var(--error)', textAlign: 'center' }}>
            {error}{' '}
            <button className="btn btn-ghost btn-sm" onClick={fetchItems}>
              Retry
            </button>
          </div>
        ) : items.length === 0 ? (
          <div style={{ padding: 'var(--space-10)', textAlign: 'center', color: 'var(--text-secondary)' }}>
            No items found.{" "}
            <button className="btn btn-ghost btn-sm" onClick={openCreate}>
              Create one
            </button>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item._id}>
                  <td>{item.name}</td>
                  <td>
                    <span className={`badge badge-${item.status === 'active' ? 'success' : 'neutral'}`}>
                      {item.status}
                    </span>
                  </td>
                  <td>{new Date(item.createdAt).toLocaleDateString()}</td>
                  <td className="flex gap-2">
                    <button className="btn btn-ghost btn-sm" onClick={() => openEdit(item)}>
                      Edit
                    </button>
                    <button
                      className="btn btn-ghost btn-sm"
                      style={{ color: 'var(--error)' }}
                      onClick={() => handleDelete(item._id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {meta.pages > 1 && (
        <div className="flex items-center justify-between" style={{ marginTop: 'var(--space-4)' }}>
          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>
            Page {page} of {meta.pages}
          </span>
          <div className="flex gap-2">
            <button className="btn btn-secondary btn-sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Previous
            </button>
            <button
              className="btn btn-secondary btn-sm"
              disabled={page >= meta.pages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Modal */}
      {modalOpen && (
        <div className="modal-backdrop" onClick={() => setModalOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 style={{ fontSize: 'var(--text-xl)', fontWeight: 'var(--font-semibold)' }}>
                {editingItem ? 'Edit Item' : 'New Item'}
              </h2>
              <button className="btn btn-ghost btn-sm" onClick={() => setModalOpen(false)}>
                x
              </button>
            </div>
            <div className="modal-body">
              {/* Form fields here */}
              <label style={{ display: 'block', marginBottom: 'var(--space-4)' }}>
                <span
                  style={{
                    fontSize: 'var(--text-sm)',
                    fontWeight: 'var(--font-medium)',
                    marginBottom: 'var(--space-1)',
                    display: 'block',
                  }}
                >
                  Name
                </span>
                <input className="input" defaultValue={editingItem?.name || ''} />
              </label>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary btn-md" onClick={() => setModalOpen(false)}>
                Cancel
              </button>
              <button className="btn btn-primary btn-md">{editingItem ? 'Save' : 'Create'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
