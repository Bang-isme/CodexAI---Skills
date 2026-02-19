# Seo Rules

## Scope and Triggers

Use this reference when tasks affect crawlability, metadata, URL structure, structured data, and search performance signals.

Primary triggers:
- requests about indexability, ranking, metadata, or sitemap
- Next.js route updates with dynamic content and canonical concerns
- Core Web Vitals regressions impacting discoverability
- structured data changes for rich results

Secondary triggers:
- internationalization and alternate language route updates
- large content site architecture changes

Out of scope:
- backend-only private endpoints with no crawlable surface

## Core Principles

- Ensure pages meant for search are crawlable and indexable.
- Keep URL structure stable, readable, and canonicalized.
- Use accurate metadata tied to page intent.
- Treat Core Web Vitals as SEO-critical quality gates.
- Prevent duplicate content through canonical policy.
- Keep structured data valid and aligned with visible content.
- Maintain sitemap and robots policy consistency.
- Ensure server-rendered meaningful content for crawlers.
- Track SEO changes with measurable outcome signals.
- Avoid manipulative or misleading optimization patterns.

## Decision Tree

### Decision Tree A: Indexing and Canonical Strategy

- If page should appear in search, allow indexing and add canonical URL.
- If page is duplicate or variant, canonicalize to primary source.
- If page is utility or private, noindex and block unnecessary crawl paths.
- If route is localized, provide alternate hreflang links.
- If content is parameterized, control crawl via canonical and parameter policy.
- If route is deprecated, redirect with proper status and update sitemap.

### Decision Tree B: Metadata and Content Matrix

| Scenario | Preferred Pattern | Avoid |
| --- | --- | --- |
| dynamic product page | server-generated title, description, canonical | static generic metadata |
| paginated content | unique metadata per page + rel strategy | duplicate titles across pages |
| article content | schema.org article markup + author/date | markup inconsistent with visible content |
| migrated URL | 301 redirect + canonical update | soft redirect without canonical correction |
| faceted navigation | controlled index policy for useful facets | indexing infinite low-value combinations |
| preview/staging pages | noindex and protected environment rules | exposing staging pages to indexing |

## Implementation Patterns

- Generate metadata from route-aware server logic.
- Keep title and description specific, concise, and non-duplicative.
- Use canonical tags on all indexable routes.
- Maintain XML sitemap with accurate lastmod and priority strategy.
- Use robots directives for private, duplicate, and low-value paths.
- Implement structured data with schema validation in CI.
- Keep heading hierarchy and semantic markup crawl-friendly.
- Optimize image delivery with alt text and responsive formats.
- Monitor Core Web Vitals and fix regressions quickly.
- Use permanent redirects for canonical URL migrations.
- Validate internal linking paths and anchor relevance.
- Ensure pagination paths expose crawlable navigation context.
- Remove orphan pages or add deliberate internal links.
- Keep locale alternates and hreflang mappings consistent.
- Track SEO incidents after major release events.

## Anti-Patterns

1. ❌ Bad: Duplicating titles and descriptions across many pages.
   ✅ Good: Generate unique title and description metadata from route-specific content fields.

2. ❌ Bad: Allowing both http and https indexed variants.
   ✅ Good: Force HTTPS with permanent redirects and emit canonical URLs using HTTPS only.

3. ❌ Bad: Indexing staging, preview, or internal utility pages.
   ✅ Good: Apply `noindex` and access controls for staging, preview, and internal tools.

4. ❌ Bad: Ignoring canonical tags on filtered or parameterized pages.
   ✅ Good: Set canonical URL to the primary version for all parameterized variants.

5. ❌ Bad: Serving empty shells with delayed content hydration only.
   ✅ Good: Render meaningful server content for crawlers using SSR or SSG where appropriate.

6. ❌ Bad: Using structured data unrelated to visible page content.
   ✅ Good: Emit schema.org markup only for entities visibly present on the page.

7. ❌ Bad: Breaking URLs without redirects and sitemap updates.
   ✅ Good: Add 301 redirects from old URLs and regenerate sitemap in the same release.

8. ❌ Bad: Blocking key assets in robots that render page meaning.
   ✅ Good: Allow crawl access to essential CSS/JS assets required for content rendering.

9. ❌ Bad: Over-optimizing keywords at expense of clarity.
   ✅ Good: Write clear user-intent copy and use keywords naturally within meaningful content.

10. ❌ Bad: Ignoring Core Web Vitals regressions on important pages.
   ✅ Good: Track LCP, CLS, and INP on key landing pages and block regressions above budget.

11. ❌ Bad: Shipping metadata templates without route-specific context.
   ✅ Good: Compose metadata per route from page data instead of one generic template.

12. ❌ Bad: Creating infinite crawl spaces through uncontrolled parameters.
   ✅ Good: Constrain crawlable parameters with canonicalization and robots parameter rules.

13. ❌ Bad: Forgetting hreflang consistency for multilingual routes.
   ✅ Good: Ensure hreflang links are reciprocal and map to valid localized URLs.

14. ❌ Bad: Treating sitemap as static and never updating it.
   ✅ Good: Automate sitemap generation on publish, update, and delete content events.

## Code Review Checklist

- [ ] Yes/No: Does this change stay within the scope and triggers defined in this reference?
- [ ] Yes/No: Is each major decision traceable to an explicit if/then or matrix condition in the Decision Tree section?
- [ ] Yes/No: Are ownership boundaries and dependencies explicit?
- [ ] Yes/No: Are high-risk failure paths guarded by validations, limits, or fallbacks?
- [ ] Yes/No: Is there a documented rollback or containment path if production behavior regresses?
- [ ] Yes/No: Are titles, descriptions, and canonical tags unique and route-specific?
- [ ] Yes/No: Are indexing rules correct for staging, preview, and internal pages?
- [ ] Yes/No: Are redirects and URL normalization rules defined for changed routes?
- [ ] Yes/No: Does structured data reflect content that is actually visible on the page?
- [ ] Yes/No: Are Core Web Vitals impacts evaluated on high-value landing pages?

## Testing and Verification Checklist

- [ ] Yes/No: Is there at least one positive-path test that verifies intended behavior?
- [ ] Yes/No: Is there at least one negative-path test that verifies rejection/failure handling?
- [ ] Yes/No: Is a regression test added for the highest-risk scenario touched?
- [ ] Yes/No: Do tests cover boundary inputs and edge conditions relevant to this change?
- [ ] Yes/No: Are integration boundaries verified where this change crosses module/service/UI layers?
- [ ] Yes/No: Do SEO snapshots verify metadata, canonical, and robots directives on changed pages?
- [ ] Yes/No: Are sitemap and robots outputs validated after routing or content updates?
- [ ] Yes/No: Do redirect tests cover old-to-new URL mappings for renamed routes?
- [ ] Yes/No: Are Core Web Vitals measured post-change on key traffic pages?
- [ ] Yes/No: Are hreflang links validated as reciprocal and pointing to valid localized URLs?

## Cross-References

- `nextjs-patterns.md` for route-level rendering and metadata generation.
- `frontend-rules.md` for semantic and structured UI foundations.
- `performance-rules.md` for Core Web Vitals optimization workflow.
- `accessibility-rules.md` for semantic markup and user-facing clarity.
- `testing-rules.md` for SEO regression and smoke test strategy.

### Scenario Walkthroughs

- Scenario: Category pages generate duplicate content via query parameters.
  - Action: Set canonical tags to primary category URLs and restrict crawl parameters.
  - Action: Add tests that parse rendered head tags across parameterized variants.
- Scenario: Site migration changes URL paths for product pages.
  - Action: Publish 301 redirect map and regenerate sitemap in the same deployment.
  - Action: Run crawl verification to confirm no orphaned legacy URLs remain indexed.
- Scenario: Next.js landing page drops CWV scores after hero redesign.
  - Action: Optimize image delivery and layout stability to recover LCP and CLS budgets.
  - Action: Add performance regression checks on top landing pages before release approval.

### Delivery Notes

- Keep this reference aligned with project conventions and postmortems.
- Update checklists when recurring defects reveal missing guardrails.
- Prefer incremental adoption over large risky rewrites.
