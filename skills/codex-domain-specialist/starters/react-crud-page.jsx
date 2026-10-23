// ============================================
// REACT CRUD PAGE STARTER — 6-State Matrix + Cursor Pagination + SILC-001 FieldErrors
// ============================================
import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api-client';

export default function ItemsPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});
  const [search, setSearch] = useState('');
  const [cursor, setCursor] = useState(undefined);
  const [cursorStack, setCursorStack] = useState([]);
  const [pagination, setPagination] = useState({ limit: 25, nextCursor: null, hasMore: false });
  const [modalOpen, setModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);
  const [formName, setFormName] = useState('');
  const [formAmountCents, setFormAmountCents] = useState('0');

  const fetchItems = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get('/items', { cursor, limit: 25, search: search.trim() || undefined });
      setItems(res.data || []);
      setPagination(res.meta?.pagination || { limit: 25, nextCursor: null, hasMore: false });
    } catch (err) {
      setError(err.message || 'Failed to load items');
    } finally {
      setLoading(false);
    }
  }, [cursor, search]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  const openCreate = () => {
    setEditingItem(null);
    setFormName('');
    setFormAmountCents('0');
    setFieldErrors({});
    setModalOpen(true);
  };

  const openEdit = (item) => {
    setEditingItem(item);
    setFormName(item.name || '');
    setFormAmountCents(String(item.amountCents ?? 0));
    setFieldErrors({});
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setFieldErrors({});
    setError(null);
    try {
      const payload = { name: formName.trim(), amountCents: Number(formAmountCents) };
      if (editingItem) {
        await api.patch(`/items/${editingItem.id}`, payload);
      } else {
        await api.post('/items', payload);
      }
      setModalOpen(false);
      await fetchItems();
    } catch (err) {
      if (err.fieldMap && Object.keys(err.fieldMap).length > 0) {
        setFieldErrors(err.fieldMap);
      } else {
        setError(err.message || 'Unable to save item');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleConfirmDelete = async (id) => {
    setSubmitting(true);
    try {
      await api.delete(`/items/${id}`);
      setConfirmDeleteId(null);
      await fetchItems();
    } catch (err) {
      setError(err.message || 'Unable to delete item');
    } finally {
      setSubmitting(false);
    }
  };

  const handleNextPage = () => {
    if (!pagination.nextCursor) return;
    setCursorStack((prev) => [...prev, cursor]);
    setCursor(pagination.nextCursor);
  };

  const handlePrevPage = () => {
    if (cursorStack.length === 0) return;
    const nextStack = [...cursorStack];
    const previousCursor = nextStack.pop();
    setCursorStack(nextStack);
    setCursor(previousCursor);
  };

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <h1 className="page-title">Items</h1>
          <p className="page-subtitle">Manage workspace inventory and pricing units</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={openCreate}>
          Create Item
        </button>
      </header>

      <section aria-label="Filter items" style={{ marginBottom: 'var(--space-4)' }}>
        <label htmlFor="item-search" className="sr-only">
          Search items
        </label>
        <input
          id="item-search"
          type="search"
          className="input"
          placeholder="Filter items by name…"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setCursor(undefined);
            setCursorStack([]);
          }}
        />
      </section>

      {loading ? (
        <section aria-busy="true" aria-label="Loading items" className="card">
          <div className="skeleton-row" />
          <div className="skeleton-row" />
          <div className="skeleton-row" />
        </section>
      ) : error ? (
        <section role="alert" className="card">
          <p>{error}</p>
          <button type="button" className="btn btn-secondary" onClick={fetchItems}>
            Retry request
          </button>
        </section>
      ) : items.length === 0 ? (
        <section className="card">
          <h2>No items recorded yet</h2>
          <p>Create your first item to start tracking inventory and unit pricing.</p>
          <button type="button" className="btn btn-primary" onClick={openCreate}>
            Create first item
          </button>
        </section>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <table className="table">
            <thead>
              <tr>
                <th scope="col">Name</th>
                <th scope="col" style={{ textAlign: 'right' }}>Amount</th>
                <th scope="col">Created</th>
                <th scope="col">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{item.name}</td>
                  <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                    ${((item.amountCents || 0) / 100).toFixed(2)}
                  </td>
                  <td style={{ fontVariantNumeric: 'tabular-nums' }}>
                    {new Date(item.createdAt).toLocaleDateString()}
                  </td>
                  <td>
                    <button type="button" className="btn btn-ghost" onClick={() => openEdit(item)}>
                      Edit
                    </button>
                    {confirmDeleteId === item.id ? (
                      <>
                        <button
                          type="button"
                          className="btn btn-danger"
                          disabled={submitting}
                          aria-busy={submitting}
                          onClick={() => handleConfirmDelete(item.id)}
                        >
                          Confirm Delete
                        </button>
                        <button type="button" className="btn btn-ghost" onClick={() => setConfirmDeleteId(null)}>
                          Cancel
                        </button>
                      </>
                    ) : (
                      <button type="button" className="btn btn-ghost" onClick={() => setConfirmDeleteId(item.id)}>
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <nav aria-label="Pagination" className="flex items-center justify-between" style={{ marginTop: 'var(--space-4)' }}>
        <button
          type="button"
          className="btn btn-secondary"
          disabled={cursorStack.length === 0 || loading}
          onClick={handlePrevPage}
        >
          Previous
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          disabled={!pagination.hasMore || loading}
          onClick={handleNextPage}
        >
          Next
        </button>
      </nav>

      {modalOpen && (
        <div className="modal-backdrop" onClick={() => setModalOpen(false)}>
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="item-dialog-title"
            className="modal"
            onClick={(e) => e.stopPropagation()}
          >
            <form onSubmit={handleSubmit}>
              <div className="modal-header">
                <h2 id="item-dialog-title">{editingItem ? 'Edit Item' : 'Create Item'}</h2>
                <button type="button" aria-label="Close dialog" className="btn btn-ghost" onClick={() => setModalOpen(false)}>
                  ×
                </button>
              </div>
              <div className="modal-body">
                <div>
                  <label htmlFor="item-name">Item Name</label>
                  <input
                    id="item-name"
                    className="input"
                    value={formName}
                    aria-invalid={Boolean(fieldErrors.name)}
                    aria-describedby={fieldErrors.name ? 'item-name-error' : undefined}
                    onChange={(e) => setFormName(e.target.value)}
                    required
                  />
                  {fieldErrors.name && (
                    <p id="item-name-error" role="alert" className="field-error">
                      {fieldErrors.name}
                    </p>
                  )}
                </div>
                <div>
                  <label htmlFor="item-amount">Amount (cents)</label>
                  <input
                    id="item-amount"
                    type="number"
                    className="input"
                    value={formAmountCents}
                    aria-invalid={Boolean(fieldErrors.amountCents)}
                    aria-describedby={fieldErrors.amountCents ? 'item-amount-error' : undefined}
                    onChange={(e) => setFormAmountCents(e.target.value)}
                    required
                  />
                  {fieldErrors.amountCents && (
                    <p id="item-amount-error" role="alert" className="field-error">
                      {fieldErrors.amountCents}
                    </p>
                  )}
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting} aria-busy={submitting}>
                  {submitting ? 'Saving…' : editingItem ? 'Save Changes' : 'Create Item'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
