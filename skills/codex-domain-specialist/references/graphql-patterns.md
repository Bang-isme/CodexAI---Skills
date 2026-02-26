# GraphQL Patterns

## Scope

Use when building GraphQL APIs. Start with REST unless query flexibility or client-driven selection clearly justifies GraphQL.

## GraphQL vs REST

| Use GraphQL | Use REST |
| --- | --- |
| Multiple clients need different projections | Simple CRUD endpoints |
| Deep nested relationships | File upload/download |
| Strong query flexibility needed | Server-to-server simple contracts |
| Subscriptions required | Webhook endpoints |

## Schema Design

```graphql
type Query {
  user(id: ID!): User
  users(filter: UserFilter, page: PageInput): UserConnection!
}

type Mutation {
  createUser(input: CreateUserInput!): UserPayload!
  updateUser(id: ID!, input: UpdateUserInput!): UserPayload!
  deleteUser(id: ID!): DeletePayload!
}

type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type UserEdge { node: User! cursor: String! }
type PageInfo { hasNextPage: Boolean! endCursor: String }
```

## N+1 Solution with DataLoader

```javascript
import DataLoader from 'dataloader';

const createLoaders = () => ({
  department: new DataLoader(async (ids) => {
    const depts = await Department.find({ _id: { $in: ids } });
    const map = new Map(depts.map((d) => [d._id.toString(), d]));
    return ids.map((id) => map.get(id.toString()) || null);
  }),
});

const resolvers = {
  User: {
    department: (user, _, { loaders }) => loaders.department.load(user.departmentId),
  },
};
```

## Security Rules

- Enforce query depth limits (for example max 5-7).
- Enforce complexity budget per query.
- Disable introspection in production when not needed.
- Apply rate limiting by complexity, not request count only.
- Validate authz in resolvers, not only at root.
