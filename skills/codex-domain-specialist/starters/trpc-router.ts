/**
 * tRPC Router Starter Template
 * Type-safe API without code generation — end-to-end TypeScript.
 * 
 * Setup: npm install @trpc/server @trpc/client @trpc/react-query zod
 * Adapt: rename procedures, adjust input schemas, customize middleware.
 */

import { initTRPC, TRPCError } from '@trpc/server';
import { z } from 'zod';

// ─── Context ──────────────────────────────────────────────────
// Define what's available in every procedure (user, db, etc.)
interface Context {
  user: { id: string; role: string } | null;
  db: PrismaClient; // or your DB client
}

const createContext = async ({ req }: { req: Request }): Promise<Context> => {
  const token = req.headers.get('authorization')?.replace('Bearer ', '');
  const user = token ? await verifyToken(token) : null;
  return { user, db: prisma };
};

// ─── tRPC Init ────────────────────────────────────────────────
const t = initTRPC.context<Context>().create();

// ─── Middleware ────────────────────────────────────────────────
const isAuthenticated = t.middleware(({ ctx, next }) => {
  if (!ctx.user) {
    throw new TRPCError({ code: 'UNAUTHORIZED', message: 'Not authenticated' });
  }
  return next({ ctx: { ...ctx, user: ctx.user } }); // Narrows type
});

const isAdmin = t.middleware(({ ctx, next }) => {
  if (!ctx.user || ctx.user.role !== 'admin') {
    throw new TRPCError({ code: 'FORBIDDEN', message: 'Admin access required' });
  }
  return next({ ctx: { ...ctx, user: ctx.user } });
});

// ─── Procedure Builders ──────────────────────────────────────
const publicProcedure = t.procedure;
const protectedProcedure = t.procedure.use(isAuthenticated);
const adminProcedure = t.procedure.use(isAdmin);

// ─── Input Schemas (Zod) ─────────────────────────────────────
const createPostInput = z.object({
  title: z.string().min(1).max(200),
  content: z.string().optional(),
  tags: z.array(z.string()).max(10).default([]),
});

const listPostsInput = z.object({
  page: z.number().int().min(1).default(1),
  limit: z.number().int().min(1).max(100).default(20),
  status: z.enum(['DRAFT', 'PUBLISHED', 'ARCHIVED']).optional(),
  search: z.string().optional(),
});

const idInput = z.object({
  id: z.string().cuid(),
});

// ─── Router ────────────────────────────────────────────────────
export const appRouter = t.router({
  // Health check (public)
  health: publicProcedure.query(() => ({
    status: 'ok',
    timestamp: new Date().toISOString(),
  })),

  // ─── Posts ────────────────────────────────────────────────
  posts: t.router({
    // List posts (public)
    list: publicProcedure
      .input(listPostsInput)
      .query(async ({ input, ctx }) => {
        const { page, limit, status, search } = input;
        const where = {
          ...(status && { status }),
          ...(search && {
            OR: [
              { title: { contains: search, mode: 'insensitive' } },
              { content: { contains: search, mode: 'insensitive' } },
            ],
          }),
        };

        const [items, total] = await Promise.all([
          ctx.db.post.findMany({
            where,
            include: { author: { select: { id: true, name: true } }, tags: true },
            orderBy: { createdAt: 'desc' },
            take: limit,
            skip: (page - 1) * limit,
          }),
          ctx.db.post.count({ where }),
        ]);

        return {
          items,
          meta: { page, limit, total, totalPages: Math.ceil(total / limit) },
        };
      }),

    // Get single post (public)
    getById: publicProcedure
      .input(idInput)
      .query(async ({ input, ctx }) => {
        const post = await ctx.db.post.findUnique({
          where: { id: input.id },
          include: { author: true, tags: true },
        });
        if (!post) throw new TRPCError({ code: 'NOT_FOUND', message: 'Post not found' });
        return post;
      }),

    // Create post (authenticated)
    create: protectedProcedure
      .input(createPostInput)
      .mutation(async ({ input, ctx }) => {
        return ctx.db.post.create({
          data: {
            ...input,
            slug: slugify(input.title),
            authorId: ctx.user.id,
            tags: {
              connectOrCreate: input.tags.map((name) => ({
                where: { name },
                create: { name },
              })),
            },
          },
          include: { tags: true },
        });
      }),

    // Delete post (admin only)
    delete: adminProcedure
      .input(idInput)
      .mutation(async ({ input, ctx }) => {
        await ctx.db.post.delete({ where: { id: input.id } });
        return { success: true };
      }),
  }),
});

// ─── Type Export (for client) ─────────────────────────────────
export type AppRouter = typeof appRouter;

// ─── Usage Notes ──────────────────────────────────────────────
//
// Server setup (Express adapter):
//   import { createExpressMiddleware } from '@trpc/server/adapters/express';
//   app.use('/api/trpc', createExpressMiddleware({ router: appRouter, createContext }));
//
// Client setup (React Query):
//   import { createTRPCReact } from '@trpc/react-query';
//   import type { AppRouter } from '../server/router';
//   export const trpc = createTRPCReact<AppRouter>();
//
// Client usage:
//   const { data } = trpc.posts.list.useQuery({ page: 1, limit: 20 });
//   const createPost = trpc.posts.create.useMutation();
//   await createPost.mutateAsync({ title: 'Hello', content: 'World' });
//
// Benefits:
//   - Full type safety from server to client (no codegen)
//   - Input validation at runtime (Zod) + compile time (TypeScript)
//   - React Query integration built-in (caching, optimistic updates)
//   - Middleware composition for auth/logging/rate-limiting
