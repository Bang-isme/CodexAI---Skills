// ============================================
// REACT TESTING LIBRARY + MSW v2 STARTER (SILC-001 Contract & 6-State Coverage)
// ============================================
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import ItemsPage from './react-crud-page.jsx';

const sampleItems = [
  {
    id: 'itm_1',
    name: 'Enterprise Seat',
    amountCents: 4900,
    createdAt: '2026-10-23T08:00:00.000Z',
  },
  {
    id: 'itm_2',
    name: 'Audit Log Add-on',
    amountCents: 1900,
    createdAt: '2026-10-23T09:00:00.000Z',
  },
];

const handlers = [
  http.get('/api/v1/items', ({ request }) => {
    const url = new URL(request.url);
    const search = (url.searchParams.get('search') || '').toLowerCase();
    const filtered = search
      ? sampleItems.filter((item) => item.name.toLowerCase().includes(search))
      : sampleItems;
    return HttpResponse.json({
      data: filtered,
      meta: {
        requestId: 'req_test_1',
        pagination: { limit: 25, nextCursor: null, hasMore: false },
      },
    });
  }),

  http.post('/api/v1/items', async ({ request }) => {
    const idempotencyKey = request.headers.get('Idempotency-Key');
    if (!idempotencyKey) {
      return HttpResponse.json(
        {
          error: {
            code: 'IDEMPOTENCY_KEY_REQUIRED',
            title: 'Idempotency-Key header is required',
            status: 400,
            requestId: 'req_test_err',
            fieldErrors: [],
          },
        },
        { status: 400 }
      );
    }

    const body = await request.json();
    if (!body.name || body.name.trim().length < 2) {
      return HttpResponse.json(
        {
          error: {
            code: 'VALIDATION_FAILED',
            title: 'Request validation failed',
            status: 422,
            requestId: 'req_test_422',
            fieldErrors: [
              { field: 'name', code: 'TOO_SMALL', message: 'Name must be at least 2 characters' },
            ],
          },
        },
        { status: 422 }
      );
    }

    return HttpResponse.json(
      {
        data: {
          id: 'itm_3',
          name: body.name,
          amountCents: body.amountCents,
          createdAt: '2026-10-23T10:00:00.000Z',
        },
        meta: { requestId: 'req_test_create', idempotentReplay: false },
      },
      { status: 201 }
    );
  }),

  http.delete('/api/v1/items/:id', () => new HttpResponse(null, { status: 204 })),
];

const server = setupServer(...handlers);

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('ItemsPage (6-State Matrix & SILC-001 Contract)', () => {
  it('renders loading skeleton with aria-busy and then displays tabular items', async () => {
    render(<ItemsPage />);
    expect(screen.getByLabelText(/loading items/i)).toHaveAttribute('aria-busy', 'true');

    await waitFor(() => {
      expect(screen.getByText('Enterprise Seat')).toBeInTheDocument();
      expect(screen.getByText('$49.00')).toBeInTheDocument();
    });
  });

  it('renders guided empty state with primary activation CTA when no items exist', async () => {
    server.use(
      http.get('/api/v1/items', () =>
        HttpResponse.json({
          data: [],
          meta: { requestId: 'req_empty', pagination: { limit: 25, nextCursor: null, hasMore: false } },
        })
      )
    );

    render(<ItemsPage />);
    await waitFor(() => {
      expect(screen.getByText(/no items recorded yet/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /create first item/i })).toBeInTheDocument();
    });
  });

  it('surfaces server 422 fieldErrors inline on the form and preserves user input', async () => {
    const user = userEvent.setup();
    render(<ItemsPage />);
    await waitFor(() => expect(screen.getByText('Enterprise Seat')).toBeInTheDocument());

    await user.click(screen.getByRole('button', { name: /create item/i }));
    const dialog = screen.getByRole('dialog');
    const nameInput = within(dialog).getByLabelText(/item name/i);

    await user.type(nameInput, 'A');
    await user.click(within(dialog).getByRole('button', { name: /create item/i }));

    await waitFor(() => {
      expect(within(dialog).getByRole('alert')).toHaveTextContent(/at least 2 characters/i);
      expect(nameInput).toHaveAttribute('aria-invalid', 'true');
      expect(nameInput).toHaveValue('A');
    });
  });

  it('requires explicit confirmation before executing a destructive delete', async () => {
    const user = userEvent.setup();
    render(<ItemsPage />);
    await waitFor(() => expect(screen.getByText('Enterprise Seat')).toBeInTheDocument());

    const deleteButtons = screen.getAllByRole('button', { name: /^delete$/i });
    await user.click(deleteButtons[0]);

    expect(screen.getByRole('button', { name: /confirm delete/i })).toBeInTheDocument();
  });
});
