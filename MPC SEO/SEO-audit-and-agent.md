# MedPharmaConnect — SEO Audit & SEO Agent

_Prepared 2026-05-29_

## What this is

A weekly **SEO Agent** that maximizes organic search performance for medpharmaconnect.com and routes that traffic to your lead form. It plugs into your existing automation (daily content + Buffer social) as a third scheduled task.

The agent and its first full pass are already live. Below is what was wrong, what was fixed today, and what the agent will keep doing every week.

---

## Gaps found (before today)

The site had strong content (34 published articles) but was leaving most of its SEO and lead potential on the table:

- **No `sitemap.xml`** — search engines had no map of the site, slowing indexing of all 34 articles.
- **No `robots.txt`** — no crawl directives, no sitemap pointer.
- **Zero structured data (schema)** on any page — no eligibility for rich results (FAQ rich snippets, Article cards). This is the single biggest "free" ranking lever for a content site.
- **No canonical tags** — duplicate-content risk and diluted ranking signals.
- **No Open Graph / Twitter tags on articles** — links shared on your social channels rendered as plain text with no title, image, or description.
- **No conversion path on articles** — every article ended at the footer. Organic visitors land on *articles*, not the homepage, so they hit a dead end with no link to your email lead form. **This is the SEO-to-leads break.**

---

## Fixed today (live in the files, pending deploy)

| Fix | Scope |
|-----|-------|
| `sitemap.xml` generated | 38 URLs (home, blog, tools, guides, all 34 articles) |
| `robots.txt` created | Allows crawl, blocks build artifacts, points to sitemap |
| Organization + WebSite + FAQPage schema | `index.html` (your 7 FAQs are now eligible for FAQ rich snippets) |
| Article + BreadcrumbList schema | all 34 articles |
| Canonical + Open Graph + Twitter tags | homepage + all 34 articles (71 schema blocks total, all validated) |
| **Lead-capture CTA block** | added before the footer of all 34 articles, linking to the email lead form (`#learn-more`) and the DTI calculator |

All changes are reversible and were made with an idempotent script — re-running never duplicates anything.

---

## The lead funnel, now connected

```
Google search  →  lands on an article (organic)  →  reads  →  CTA block
                                                              ├─ "Get matched with a lender" → index.html #learn-more (your email form)
                                                              └─ "Try the DTI Calculator"     → tools/dti-calculator.html → back to form
```

Before, that funnel stopped at "reads." The email form you already have is now the destination of every article.

---

## The weekly SEO Agent (`medpharma-seo-agent`)

Runs every **Monday ~10am**, after your daily content and Buffer tasks. Each run it:

1. Re-runs the technical SEO script so any **new** articles automatically get schema, canonical/OG tags, a lead CTA, and a sitemap entry.
2. **Publish-gap check** — flags daily markdown articles that were never converted to live HTML pages (see recommendation below).
3. On-page review of the 3 newest articles (title length, meta description, H1, internal links, keyword placement) — fixes the cheap stuff, flags the rest.
4. Researches current keyword/news angles and recommends 3 new long-tail article topics.
5. Strengthens internal linking to the newest articles.
6. Writes a dated report to this folder + appends to `seo-log.md`.
7. Gives you the one-line deploy command (it never pushes on its own).

---

## Article publisher (built)

Your daily-content agent writes articles as **markdown** to `content/articles/`, but they weren't being converted into live HTML pages — so most daily content was invisible to Google. That's fixed:

- **`MPC SEO/publish_articles.py`** converts markdown drafts into HTML pages that match your article template, adds a card to `blog.html`, then runs the SEO agent to inject schema/canonical/OG/lead-CTA and refresh the sitemap.
- **De-duplication** skips any draft whose title closely matches an already-published article (token similarity), preventing keyword cannibalization. It tracks state in `content/published-map.json` so re-runs only publish new drafts.
- **Editorial holds**: `content/publish-skip.json` lists drafts to never publish. Remove an entry to release it.
- **Wired into the daily task** — every new daily article now auto-publishes (unless it's a near-duplicate).

### Backlog processed today

Of the 36 markdown drafts, 31 were already live or near-duplicates. **3 genuinely new articles were published:**

- Is 2026 Finally the Right Year for Physicians to Buy a Home?
- Banks vs. Non-Bank Lenders for Your Physician Mortgage
- Major Student Loan Changes Are Coming July 1 (freshest of the student-loan cluster)

**4 held** (`publish-skip.json`) — they retell the same "July 2026 student-loan changes" story already covered by existing articles. Publishing all of them would split rankings. Release any by editing that file if you'd rather run them.

Site now has **37 live article pages** and a **41-URL sitemap**.

---

## To go live

```
cd /Users/sbhome/practicepath
git add -A
git commit -m "SEO: sitemap, robots, schema, canonical/OG, article lead CTAs"
git push
```

Netlify auto-deploys. After deploy, submit `https://medpharmaconnect.com/sitemap.xml` in Google Search Console to accelerate indexing.
