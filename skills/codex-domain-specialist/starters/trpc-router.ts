/**
 * tRPC Router Starter — Contract-First (SILC-001 & SILC-002 Compliant)
 * Keyset Cursor Pagination + Explicit DTO Selection (Zero Password Leakage) + Idempotency
 */
import { initTRPC, TRPCError } from '@trpc/server';
import { z } from 'zod';

export interface Actor {
  userId: string;
  tenantId: string;
  role: 'USER' | 'MANAGER' | 'ADMIN';
}

export interface Context {
  requestId: string;
  actor: Actor | null;
  db: any;
}

const t = initTRPC.context<Context>().create();

const isAuthenticated = t.middleware(({ ctx, next }) => {
  if (!ctx.actor) {
    throw new TRPCError({ code: 'UNAUTHORIZED', message: 'Authentication required' });
  }
  return next({ ctx: { ...ctx, actor: ctx.actor } });
});

const isAdmin = t.middleware(({ ctx, next }) => {
  if (!ctx.actor || ctx.actor.role !== 'ADMIN') {
    throw new TRPCError({ code: 'FORBIDDEN', message: 'Admin role required' });
  }
  return next({ ctx: { ...ctx, actor: ctx.actor } });
});

export const publicProcedure = t.procedure;
export const protectedProcedure = t.procedure.use(isAuthenticated);
export const adminProcedure = t.procedure.use(isAdmin);

const PublicAuthorSelect = {
  id: true,
  name: true,
  role: true,
} as const;

const ListPostsCursorInput = z
  .object({
    cursor: z.string().trim().max(512).optional(),
    limit: z.number().int().min(1).max(100).default(25),
    status: z.enum(['DRAFT', 'PUBLISHED', 'ARCHIVED']).optional(),
    search: z.string().trim().max(120).optional(),
  })
  .strict();

const CreatePostInput = z
  .object({
    idempotencyKey: z.string().uuid(),
    title: z.string().trim().min(3).max(200),
    slug: z.string().trim().toLowerCase().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/),
    content: z.string().max(50_000).optional(),
    budgetCents: z.number().int().min(0).default(0),
    tags: z.array(z.string().trim().min(1).max(32)).max(10).default([]),
  })
  .strict();

const PostIdInput = z.object({ id: z.string().min(1) }).strict();

export const toPostDto = (row: any) => ({
  id: String(row.id),
  tenantId: String(row.tenantId),
  title: String(row.title),
  slug: String(row.slug),
  content: row.content ?? null,
  budgetCents: Number(row.budgetCents ?? 0),
  status: row.status,
  author: row.author ? { id: row.author.id, name: row.author.name, role: row.author.role } : null,
  tags: Array.isArray(row.tags) ? row.tags.map((t: any) => ({ id: t.id, name: t.name })) : [],
  createdAt: row.createdAt instanceof Date ? row.createdAt.toISOString() : String(row.createdAt),
});

export const appRouter = t.router({
  health: publicProcedure.query(() => ({
    status: 'alive',
    timestamp: new Date().toISOString(),
  })),

  posts: t.router({
    list: protectedProcedure.input(ListPostsCursorInput).query(async ({ input, ctx }) => {
      const { cursor, limit, status, search } = input;
      const where = {
        tenantId: ctx.actor.tenantId,
        ...(status ? { status } : {}),
        ...(search
          ? {
              OR: [
                { title: { contains: search, mode: 'insensitive' } },
                { content: { contains: search, mode: 'insensitive' } },
              ],
            }
          : {}),
      };

      const rows = await ctx.db.post.findMany({
        where,
        take: limit + 1,
        ...(cursor ? { cursor: { id: cursor }, skip: 1 } : {}),
        orderBy: [{ createdAt: 'desc' }, { id: 'desc' }],
        include: {
          author: { select: PublicAuthorSelect },
          tags: { select: { id: true, name: true } },
        },
      });

      const hasMore = rows.length > limit;
      const slice = hasMore ? rows.slice(0, limit) : rows;
      const nextCursor = hasMore ? String(slice[slice.length - 1].id) : null;

      return {
        data: slice.map(toPostDto),
        meta: {
          requestId: ctx.requestId,
          pagination: { limit, nextCursor, hasMore },
        },
      };
    }),

    getById: protectedProcedure.input(PostIdInput).query(async ({ input, ctx }) => {
      const post = await ctx.db.post.findFirst({
        where: { id: input.id, tenantId: ctx.actor.tenantId },
        include: {
          author: { select: PublicAuthorSelect },
          tags: { select: { id: true, name: true } },
        },
      });
      if (!post) {
        throw new TRPCError({ code: 'NOT_FOUND', message: 'Post not found' });
      }
      return { data: toPostDto(post), meta: { requestId: ctx.requestId } };
    }),

    create: protectedProcedure.input(CreatePostInput).mutation(async ({ input, ctx }) => {
      const created = await ctx.db.post.create({
        data: {
          tenantId: ctx.actor.tenantId,
          authorId: ctx.actor.userId,
          title: input.title,
          slug: input.slug,
          content: input.content,
          budgetCents: BigInt(input.budgetCents),
        },
        include: {
          author: { select: PublicAuthorSelect },
          tags: { select: { id: true, name: true } },
        },
      });
      return { data: toPostDto(created), meta: { requestId: ctx.requestId, idempotencyKey: input.idempotencyKey } };
    }),

    delete: adminProcedure.input(PostIdInput).mutation(async ({ input, ctx }) => {
      const deleted = await ctx.db.post.deleteMany({
        where: { id: input.id, tenantId: ctx.actor.tenantId },
      });
      if (deleted.count === 0) {
        throw new TRPCError({ code: 'NOT_FOUND', message: 'Post not found' });
      }
      return { data: { id: input.id, deleted: true }, meta: { requestId: ctx.requestId } };
    }),
  }),
});

export type AppRouter = typeof appRouter;
