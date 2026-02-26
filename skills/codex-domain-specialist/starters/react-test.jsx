// ============================================
// REACT TESTING LIBRARY STARTER
// ============================================
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { rest } from 'msw';
import { setupServer } from 'msw/node';

// Replace with your component path
import UsersPage from '../src/pages/UsersPage.jsx';

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 }, mutations: { retry: false } },
  });

const AllProviders = ({ children }) => (
  <QueryClientProvider client={createTestQueryClient()}>
    <BrowserRouter>{children}</BrowserRouter>
  </QueryClientProvider>
);

const renderWithProviders = (ui, options = {}) =>
  render(ui, { wrapper: AllProviders, ...options });

const handlers = [
  rest.get('/api/v1/users', (req, res, ctx) => {
    const page = parseInt(req.url.searchParams.get('page') || '1', 10);
    return res(
      ctx.json({
        success: true,
        data: [
          { _id: '1', firstName: 'John', lastName: 'Doe', email: 'john@test.com', status: 'active' },
          { _id: '2', firstName: 'Jane', lastName: 'Smith', email: 'jane@test.com', status: 'active' },
        ],
        meta: { page, limit: 20, total: 2, pages: 1 },
      })
    );
  }),
  rest.post('/api/v1/users', async (req, res, ctx) => {
    const body = await req.json();
    return res(ctx.status(201), ctx.json({ success: true, data: { _id: '3', ...body } }));
  }),
  rest.delete('/api/v1/users/:id', (req, res, ctx) => res(ctx.json({ success: true }))),
];

const server = setupServer(...handlers);

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('UsersPage', () => {
  it('should show loading spinner initially', () => {
    renderWithProviders(<UsersPage />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('should display users after loading', async () => {
    renderWithProviders(<UsersPage />);
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });
  });

  it('should filter users when searching', async () => {
    const user = userEvent.setup();
    renderWithProviders(<UsersPage />);
    await waitFor(() => expect(screen.getByText('John Doe')).toBeInTheDocument());

    const searchInput = screen.getByPlaceholderText(/search/i);
    await user.type(searchInput, 'John');

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });
  });

  it('should show error message on API failure', async () => {
    server.use(rest.get('/api/v1/users', (req, res, ctx) => res(ctx.status(500))));
    renderWithProviders(<UsersPage />);

    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });
  });

  it('should open create modal and submit form', async () => {
    const user = userEvent.setup();
    renderWithProviders(<UsersPage />);
    await waitFor(() => expect(screen.getByText('John Doe')).toBeInTheDocument());

    await user.click(screen.getByRole('button', { name: /add/i }));

    const modal = screen.getByRole('dialog');
    expect(within(modal).getByText(/new user/i)).toBeInTheDocument();

    await user.type(within(modal).getByLabelText(/name/i), 'New User');
    await user.click(within(modal).getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  it('should show empty state when no users', async () => {
    server.use(
      rest.get('/api/v1/users', (req, res, ctx) =>
        res(ctx.json({ success: true, data: [], meta: { total: 0, pages: 0 } }))
      )
    );

    renderWithProviders(<UsersPage />);
    await waitFor(() => {
      expect(screen.getByText(/no.*found/i)).toBeInTheDocument();
    });
  });
});

/*
Query priority:
1. getByRole
2. getByLabelText
3. getByPlaceholderText
4. getByText
5. getByTestId
Avoid: querySelector/class selectors.
*/
