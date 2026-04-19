# AI/LLM Integration Patterns

**Load when:** building AI-powered features, integrating OpenAI/Anthropic/Google APIs, implementing RAG pipelines, managing embeddings, or prompt engineering.

## Architecture Decision Table

| Pattern | Use When | Complexity | Example |
| --- | --- | --- | --- |
| Direct API call | Single LLM query, no context | Low | Chatbot, summarizer |
| RAG (Retrieval-Augmented Generation) | LLM needs project/domain knowledge | Medium | Doc Q&A, code assistant |
| Agent loop | Multi-step reasoning with tools | High | Autonomous coding, research |
| Fine-tuning | Domain-specific behavior change | High | Custom classifier, style transfer |
| Embeddings + Vector DB | Semantic search, similarity | Medium | Content recommendation, dedup |

## Prompt Engineering Patterns

### System Prompt Structure

```javascript
const systemPrompt = `You are a [ROLE] that [CORE BEHAVIOR].

## Rules
- [CONSTRAINT 1]
- [CONSTRAINT 2]
- [OUTPUT FORMAT requirement]

## Context
[DOMAIN KNOWLEDGE the model needs]

## Examples
Input: [example input]
Output: [example output]
`;
```

### Anti-Patterns

```javascript
// ❌ BAD: Vague prompt
const prompt = "Help me with this code";

// ✅ GOOD: Structured prompt with constraints
const prompt = `Analyze this TypeScript function for bugs.

Function:
\`\`\`typescript
${code}
\`\`\`

Rules:
- Only report confirmed bugs, not style preferences
- Include line number and severity (critical/warning)
- Suggest a fix for each bug

Output format:
- Bug 1: [line X] [severity] [description] → Fix: [suggestion]
`;

// ❌ BAD: No output format constraint
"Summarize this document";

// ✅ GOOD: Constrained output
"Summarize this document in exactly 3 bullet points, each under 20 words.";
```

### Few-Shot vs Zero-Shot Decision

| Scenario | Strategy | Why |
| --- | --- | --- |
| Well-known task (translation, summary) | Zero-shot | Model already understands |
| Custom format (specific JSON schema) | Few-shot (2-3 examples) | Model needs format reference |
| Domain-specific classification | Few-shot (3-5 examples) | Model needs domain calibration |
| Complex reasoning chain | Chain-of-thought | Model needs step-by-step |

## OpenAI API Integration

```javascript
import OpenAI from 'openai';

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

// Structured output with response_format
const completion = await openai.chat.completions.create({
  model: 'gpt-4o',
  messages: [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: userInput },
  ],
  temperature: 0.3,       // Lower = more deterministic
  max_tokens: 1000,
  response_format: { type: 'json_object' }, // Force JSON output
});

const result = JSON.parse(completion.choices[0].message.content);
```

### Error Handling & Retry

```javascript
import { setTimeout } from 'timers/promises';

const callLLM = async (messages, retries = 3) => {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const response = await openai.chat.completions.create({
        model: 'gpt-4o',
        messages,
        temperature: 0.3,
      });
      return response.choices[0].message.content;
    } catch (error) {
      if (error.status === 429) {
        // Rate limited — exponential backoff
        const delay = Math.min(1000 * Math.pow(2, attempt), 30000);
        console.warn(`Rate limited. Retrying in ${delay}ms (attempt ${attempt}/${retries})`);
        await setTimeout(delay);
        continue;
      }
      if (error.status >= 500) {
        // Server error — retry
        await setTimeout(1000 * attempt);
        continue;
      }
      throw error; // Client error (400, 401) — don't retry
    }
  }
  throw new Error('LLM call failed after retries');
};
```

## RAG (Retrieval-Augmented Generation)

### Pipeline Architecture

```
User Query
    ↓
[1. Embed Query] → Vector DB query (top-K similar chunks)
    ↓
[2. Build Context] → System prompt + retrieved chunks + user query
    ↓
[3. LLM Call] → Generate response grounded in retrieved context
    ↓
[4. Post-process] → Verify citations, format output
```

### Implementation

```javascript
import { OpenAIEmbeddings } from '@langchain/openai';
import { PineconeStore } from '@langchain/pinecone';

// 1. Index documents (one-time or on update)
const embeddings = new OpenAIEmbeddings({ model: 'text-embedding-3-small' });
const vectorStore = await PineconeStore.fromDocuments(documents, embeddings, {
  pineconeIndex,
  namespace: 'project-docs',
});

// 2. Query with RAG
const queryRAG = async (question) => {
  // Retrieve relevant chunks
  const relevantDocs = await vectorStore.similaritySearch(question, 4); // top-4

  // Build context-aware prompt
  const context = relevantDocs.map(d => d.pageContent).join('\n---\n');
  const messages = [
    {
      role: 'system',
      content: `Answer based ONLY on the provided context. If the context doesn't contain the answer, say "I don't have enough information."

Context:
${context}`,
    },
    { role: 'user', content: question },
  ];

  return await callLLM(messages);
};
```

### Chunking Strategy

| Strategy | Chunk Size | Overlap | Best For |
| --- | --- | --- | --- |
| Fixed-size | 500-1000 tokens | 50-100 tokens | General documents |
| Paragraph-based | Natural paragraphs | 1 sentence | Well-structured docs |
| Semantic | By topic/section | Header context | Technical documentation |
| Code-aware | By function/class | Import context | Source code |

## Embeddings & Vector Search

```javascript
// Generate embeddings
const getEmbedding = async (text) => {
  const response = await openai.embeddings.create({
    model: 'text-embedding-3-small', // 1536 dimensions, cheap
    input: text,
  });
  return response.data[0].embedding;
};

// Cosine similarity (for local comparisons)
const cosineSimilarity = (a, b) => {
  const dot = a.reduce((sum, ai, i) => sum + ai * b[i], 0);
  const magA = Math.sqrt(a.reduce((sum, ai) => sum + ai * ai, 0));
  const magB = Math.sqrt(b.reduce((sum, bi) => sum + bi * bi, 0));
  return dot / (magA * magB);
};
```

### Vector DB Selection

| Database | Type | Best For | Pricing Model |
| --- | --- | --- | --- |
| Pinecone | Managed | Production, low-ops | Per-vector + queries |
| Weaviate | Self-hosted / Cloud | Hybrid search | Open source / managed |
| Chroma | Embedded | Prototyping, local dev | Free (open source) |
| pgvector | PostgreSQL extension | Already using Postgres | Free (extension) |
| Qdrant | Self-hosted / Cloud | High performance | Open source / managed |

## Streaming Responses

```javascript
// Server-Sent Events for streaming LLM output
app.get('/api/chat/stream', async (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  const stream = await openai.chat.completions.create({
    model: 'gpt-4o',
    messages: [{ role: 'user', content: req.query.message }],
    stream: true,
  });

  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content || '';
    if (content) {
      res.write(`data: ${JSON.stringify({ content })}\n\n`);
    }
  }
  res.write('data: [DONE]\n\n');
  res.end();
});

// Frontend consumption
const consumeStream = async (message, onChunk) => {
  const response = await fetch(`/api/chat/stream?message=${encodeURIComponent(message)}`);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const text = decoder.decode(value);
    const lines = text.split('\n').filter(l => l.startsWith('data: '));
    for (const line of lines) {
      const data = line.slice(6);
      if (data === '[DONE]') return;
      onChunk(JSON.parse(data).content);
    }
  }
};
```

## Cost Control

| Strategy | Implementation |
| --- | --- |
| Token budgets | Set `max_tokens` to minimum needed |
| Model tiering | Use GPT-4o-mini for simple tasks, GPT-4o for complex |
| Caching | Cache identical queries (hash prompt → response) |
| Batch processing | Group multiple items in one prompt |
| Rate limiting | Limit user requests per minute |
| Usage tracking | Log tokens per user/feature for billing |

```javascript
// Token usage tracking middleware
const trackUsage = (userId, model, usage) => {
  const cost = calculateCost(model, usage.prompt_tokens, usage.completion_tokens);
  db.usageLogs.create({
    userId,
    model,
    promptTokens: usage.prompt_tokens,
    completionTokens: usage.completion_tokens,
    totalTokens: usage.total_tokens,
    estimatedCost: cost,
    timestamp: new Date(),
  });
};
```

## Security Rules

1. **Never expose API keys to frontend.** Proxy through your backend.
2. **Sanitize LLM output** before rendering as HTML (prevent XSS from model output).
3. **Validate structured output** — model may return invalid JSON despite `response_format`.
4. **Rate limit per user** — prevent abuse / cost explosion.
5. **PII filtering** — strip sensitive data before sending to external LLM APIs.
6. **Prompt injection defense** — separate system instructions from user input clearly.

```javascript
// ❌ BAD: User input in system prompt
const prompt = `You are helpful. ${userInput}. Now summarize.`;

// ✅ GOOD: Clear separation
const messages = [
  { role: 'system', content: 'You are a helpful summarizer. Only summarize the user text.' },
  { role: 'user', content: userInput },
];
```

## Anti-Patterns

| Anti-Pattern | Fix |
| --- | --- |
| API key in frontend code | Backend proxy with auth |
| No retry on rate limit | Exponential backoff |
| Trusting LLM output as code | Validate/sandbox before execution |
| Giant context window stuffing | RAG with relevant chunks only |
| No cost monitoring | Track tokens per user/feature |
| Prompt in hardcoded string | Template with variables, version control prompts |
| No streaming for long responses | SSE/WebSocket for real-time UX |
