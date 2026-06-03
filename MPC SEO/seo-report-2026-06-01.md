# MedPharmaConnect — Weekly SEO Report

**Date:** 2026-06-01
**Domain:** https://medpharmaconnect.com
**Run type:** Automated weekly SEO agent (scheduled)

---

## 1. Technical SEO sweep (seo_agent.py)

Ran the idempotent maintenance script against `/Users/sbhome/practicepath`. Results:

- **index.html** — Organization + WebSite + FAQPage schema, canonical, Open Graph/Twitter tags all present/refreshed.
- **articles/** — 40 files processed: canonical + OG/Twitter tags and Article + Breadcrumb JSON-LD ensured on every page.
- **Lead CTA** — already present on all 40 articles (0 added, 40 skipped).
- **Related-article internal links** — refreshed on all 40 files.
- **sitemap.xml** — regenerated, 44 URLs.
- **robots.txt** — present with sitemap reference.

**JSON-LD validity:** Independently parsed all structured-data blocks — **83 JSON-LD blocks across 41 pages, 0 invalid.** ✅

---

## 2. Publish gap check (last 14 days: 2026-05-18 → 2026-06-01)

**No real publish gap — all daily articles from the window are live.**

Five markdown files initially flagged as "unpublished" (05-18 through 05-22) turned out to be **already published** under descriptive `article-*.html` filenames; they were simply missing from `content/published-map.json`. Verified by exact title match:

| Markdown | Live HTML | Status |
|---|---|---|
| article-2026-05-18.md | article-pharmacist-playbook-2026.html | ✅ live |
| article-2026-05-19.md | article-rate-buydowns-physician-mortgage.html | ✅ live |
| article-2026-05-20.md | article-credit-score-physician-homebuyer.html | ✅ live |
| article-2026-05-21.md | article-appraisal-physician-mortgage.html | ✅ live |
| article-2026-05-22.md | article-student-loan-shakeup-2026.html | ✅ live |
| article-2026-05-23/24/25.md | — | intentionally skipped (publish-skip.json) |
| article-2026-05-26.md | is-2026-finally-the-right-year-…html | ✅ live |
| article-2026-05-27.md | banks-vs-non-bank-lenders-…html | ✅ live |
| article-2026-05-28.md | — | intentionally skipped (publish-skip.json) |
| article-2026-05-29.md | major-student-loan-changes-…html | ✅ live |
| article-2026-05-30.md | the-visa-holder-physician-s-guide-…html | ✅ live |
| article-2026-05-31.md | buying-a-home-you-ve-never-seen-…html | ✅ live |
| article-2026-06-01.md | the-locum-tenens-physician-s-guide-…html | ✅ live |

**Action taken (safe, reversible):** Added the five verified mappings to `content/published-map.json` so future runs stop raising false "unpublished" alarms. No content was generated or converted.

---

## 3. Keyword & on-page review — 3 newest articles

Reviewed the three most recent publications:

1. `the-locum-tenens-physician-s-guide-…how-1099.html` (06-01)
2. `buying-a-home-you-ve-never-seen-the-relocating-physician-s-playbook-for-2026.html` (05-31)
3. `the-visa-holder-physician-s-guide-…h-1b-j-1-and-the-fha.html` (05-30)

**Passing on all three:** exactly one H1; target keyword present in H1 and title; 6–7 internal links each (well over the 2-link minimum), including the DTI calculator and the `#learn-more` contact form.

**Fixed directly (cheap + safe):** All three meta descriptions were over-length (248 / 283 / 278 chars) and would truncate in search results. Trimmed each to within the 120–158 ideal while preserving the target keyword. Applied consistently across `<meta name="description">`, `og:description`, `twitter:description`, and the JSON-LD `description` field (4 instances per file). New lengths: **151 / 137 / 139 chars.** JSON-LD re-validated OK after edits.

**Flagged as recommendation (not auto-fixed):** Title tags exceed the 60-char ideal (147 / 106 / 135 chars). Shortening risks dropping the long-tail target keywords these descriptive titles are built around, and the `| MedPharmaConnect` suffix is a site-wide branding convention. Recommend leaving as-is unless Steve wants to test shorter SERP-optimized titles on a per-article basis.

---

## 4. Opportunity research — 3 recommended new topics

Current trends (June 2026): physician mortgage rates sit in the ~6.25–7.0% range; ARMs now make up 30–40% of physician originations; the **RAP repayment plan replaces SAVE/most IDR plans on July 1, 2026**; and physician-mortgage eligibility is **expanding to advanced practice clinicians** (CRNAs, NPs, PAs) at a growing share of lenders. Cross-referenced against `content/competitor-research.md` (which calls out "specialize in underserved professions" and "target long-tail, specialty-specific keywords") and the existing 40-article library.

**Recommended new articles (long-tail, low-competition, not yet covered):**

1. **"The CRNA's Physician Mortgage Guide for 2026: Which Lenders Count Nurse Anesthetists — and How Your Student Loans Are Treated."** Target: *CRNA mortgage / nurse anesthetist home loan 2026*. Currently covered by only ~40–60% of lenders, high-income audience, and the site has zero CRNA content. Strong underserved-profession play.

2. **"Nurse Practitioners and Physician Assistants: Do You Qualify for a Physician Mortgage in 2026?"** Target: *nurse practitioner physician mortgage / PA home loan eligibility*. Lenders are actively extending APC eligibility; aligns with the brand's multi-professional positioning and competitor-research recommendation #2.

3. **"How the New RAP Payment Changes Your DTI — and Your Physician Mortgage Approval (Starting July 1, 2026)."** Target: *RAP student loan payment DTI / physician mortgage student loan 2026*. The site covers the RAP/SAVE news broadly but not the specific DTI mechanics. Natural funnel to the DTI calculator — strong lead-gen angle on a high-volume, time-sensitive query.

*(All statistics above are sourced from the linked research below; none invented.)*

---

## 5. Internal linking

- **blog.html** — all three newest articles already linked. ✅
- **Inbound from older articles:** relocating guide (6 inbound) ✅ and visa guide (2 inbound) ✅ were well-linked. The **locum tenens guide had zero inbound links** from older articles.
- **Fix applied:** Added a contextual inline link to the locum guide from `article-variable-income-guide.html` (within its "Locum tenens income" paragraph — topically exact). Chose an in-body prose link rather than editing the script-managed `SEO-AGENT-RELATED` block, so the link survives future script runs.

---

## 6. Leads health

- **index.html:** `#learn-more` contact form anchor present (1), `<form>` present (1). ✅
- **Articles:** 40 of 40 carry the lead-capture CTA linking to `../index.html#learn-more`; 40 of 40 link to the DTI calculator. ✅
- No broken or removed CTAs detected. Lead funnel intact.

---

## 7. Deploy

Changes this run: regenerated sitemap/robots, refreshed schema + tags across 40 articles + index, trimmed 3 meta descriptions, added 1 internal link, updated `published-map.json`. **Not pushed to git** (per policy).

To review and deploy (Netlify auto-deploys from the repo):

```
cd /Users/sbhome/practicepath && git add -A && git commit -m "Weekly SEO update" && git push
```

Tip: run `git diff --stat` first to review the scope before committing.

---

## Addendum — 2026-06-02 (interactive follow-up with Steve)

**Scope decisions from Steve:** CRNA and NP/PA topics are dropped — MedPharmaConnect stays scoped to physicians, dentists, and pharmacists. Two publish-ready HTML articles were written and wired in.

**New articles published (HTML, full template, schema + CTA + internal links):**

1. `articles/article-rap-payment-dti-physician-mortgage.html` — *"RAP and Your Physician-Mortgage DTI: What Changes July 1, 2026."* Title 62 chars, meta 156, single H1, 8 internal links incl. DTI calculator. Funnels to the DTI tool.
2. `articles/article-physician-arm-decision-2026.html` — *"Should a Physician Take an ARM in 2026? A Decision Guide."* Title 56 chars, meta 156, single H1, 9 internal links incl. DTI calculator.

Both pass JSON-LD validation (Article + Breadcrumb, 0 invalid). All facts sourced from the research below — no invented statistics.

**Wiring:** Ran `seo_agent.py` (now 43 articles, 47-URL sitemap, lead CTA + related blocks injected on both). Added both as cards at the top of `blog.html`. Added durable contextual inbound links to both from `article-arm-vs-fixed.html` (the related-block auto-linking already gives RAP 10 inbound and the ARM guide 3 inbound).

**Auto-push investigation (Steve's request):**

- No git / GitHub / Netlify connector exists in the MCP registry, so there is no managed-connector path today.
- However, the repo's git remote (`origin`) already has a GitHub personal-access token embedded in the URL, so a non-interactive `git push` **works from an automated run with no extra auth**. The scheduled SEO task could be updated to run `git add -A && git commit && git push` as a final step.
- **Recommendation:** technically straightforward to enable, but it removes the human review gate before live deploys. Suggest either (a) leave manual, or (b) enable auto-push only for the script's own idempotent changes (sitemap/robots/schema) and keep new-article publishing manual. Happy to wire whichever you choose into the scheduled task.
- ⚠️ **Security flag:** the GitHub token is stored in plaintext in `.git/config`. If this repo is ever shared or the config leaked, the token grants push access. Recommend rotating it and switching to a credential helper or SSH key, or a Netlify build hook, before automating.

**Note:** Steve confirmed he already ran the manual `git push` for the earlier (2026-06-01) batch.

---

### Sources (opportunity research)

- [SAVE vs RAP: Student loan repayment changes in 2026 — Earnest](https://www.earnest.com/blog/save-vs-rap-student-loan-repayment-2026)
- [New repayment options come July 1 — CNBC](https://www.cnbc.com/2026/05/29/student-loan-borrowers-new-repayment-plans.html)
- [How the RAP Plan Changes Repayment and PSLF for Medical Residents — Student Loan Planner](https://www.studentloanplanner.com/medical-residency-rap-payment/)
- [CRNA Mortgage: Up to 100% Financing for Nurse Anesthetists — Student Loan Planner](https://www.studentloanplanner.com/crna-mortgage-loans-nurse-anesthetists/)
- [Professional's Mortgage Loan (eligibility incl. NP/PA/CRNA) — FNBO](https://www.fnbo.com/personal-banking/mortgage-loans/professionals-loan)
- [Physician Mortgage Loans 2026 Guide — SalaryDr](https://www.salarydr.com/blog/physician-mortgage-loans-guide)
- [Doctor Mortgage Loan Complete Guide — White Coat Investor](https://www.whitecoatinvestor.com/personal-finance/the-doctor-mortgage-loan/)
