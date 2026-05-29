#!/usr/bin/env python3
"""
MedPharmaConnect Article Publisher
==================================
Converts daily markdown drafts in content/articles/*.md into live, SEO-ready
HTML pages in articles/, adds a card to blog.html, and (via seo_agent.py)
injects schema/canonical/OG/lead-CTA and regenerates the sitemap.

Key safety feature — DE-DUPLICATION:
  Many daily drafts overlap with already-published articles or with each other
  (e.g. several "July 2026 student loan change" pieces). Publishing near-dupes
  causes keyword cannibalization and hurts SEO. This script skips any draft
  whose title is too similar (token Jaccard >= THRESHOLD) to an already-
  published article OR to another draft already published in this run.

State is tracked in content/published-map.json so re-runs only publish new,
unique drafts (safe to run daily/weekly).

Usage:
  python3 publish_articles.py [/path/to/practicepath] [--dry-run]
"""

import os, re, sys, json, glob, html, datetime, subprocess

ROOT = next((a for a in sys.argv[1:] if not a.startswith("-")),
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DRY = "--dry-run" in sys.argv

ART_DIR   = os.path.join(ROOT, "articles")
MD_DIR    = os.path.join(ROOT, "content", "articles")
BLOG      = os.path.join(ROOT, "blog.html")
MAP_FILE  = os.path.join(ROOT, "content", "published-map.json")
SKIP_FILE = os.path.join(ROOT, "content", "publish-skip.json")  # md basenames to never publish (editorial holds)
SEO_AGENT = os.path.join(ROOT, "MPC SEO", "seo_agent.py")

THRESHOLD = 0.45  # title similarity above which a draft is treated as a duplicate
STOP = set("a an the of to for and or in on at is are with your you how what "
           "when does do as that this it its when why who whom be can not "
           "into about before after their they them his her doctors doctor".split())

# ---------- markdown parsing ----------
def parse_md(path):
    raw = open(path, encoding="utf-8").read()
    fm, body = {}, raw
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip('"')
        body = m.group(2)
    return fm, body.strip()

def norm_tokens(title):
    words = re.findall(r"[a-z0-9]+", title.lower())
    return set(w for w in words if w not in STOP and len(w) > 2)

def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

# ---------- inline + block markdown -> HTML ----------
def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return t

def md_to_html(body):
    lines = body.split("\n")
    out, para, list_buf, list_type = [], [], [], None
    first_h1_skipped = False

    def flush_para():
        if para:
            out.append("<p>" + inline(" ".join(para).strip()) + "</p>")
            para.clear()
    def flush_list():
        nonlocal list_type
        if list_buf:
            tag = list_type
            out.append(f"<{tag}>")
            out.extend(f"  <li>{inline(li)}</li>" for li in list_buf)
            out.append(f"</{tag}>")
            list_buf.clear(); list_type = None

    for ln in lines:
        s = ln.rstrip()
        if not s.strip():
            flush_para(); flush_list(); continue
        h = re.match(r"^(#{1,6})\s+(.*)$", s)
        if h:
            flush_para(); flush_list()
            level = len(h.group(1)); text = h.group(2).strip()
            if level == 1 and not first_h1_skipped:
                first_h1_skipped = True; continue  # hero already shows the title
            tag = "h2" if level <= 2 else "h3"
            out.append(f"<{tag}>{inline(text)}</{tag}>")
            continue
        ol = re.match(r"^\d+\.\s+(.*)$", s)
        ul = re.match(r"^[-*]\s+(.*)$", s)
        if ol or ul:
            flush_para()
            want = "ol" if ol else "ul"
            if list_type and list_type != want:
                flush_list()
            list_type = want
            list_buf.append((ol or ul).group(1).strip())
            continue
        flush_list()
        para.append(s.strip())
    flush_para(); flush_list()
    return "\n".join(out)

# ---------- helpers ----------
def slugify(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if len(s) > 80:
        s = s[:80].rsplit("-", 1)[0]
    return s

def category_meta(cat):
    c = (cat or "").lower()
    if "checklist" in c: return "checklist", "Checklist"
    if "q&a" in c or "faq" in c or "q and a" in c: return "q&a", "Q&A"
    if "explain" in c: return "explainer", "Explainer"
    return "guide", "Guide"

def pretty_date(d):
    try:
        return datetime.date.fromisoformat(d).strftime("%B %Y")
    except Exception:
        return ""

# ---------- HTML templates ----------
NAV = '''  <!-- NAV -->
  <header class="nav">
    <div class="container nav-inner">
      <a href="../index.html" style="display:inline-block;line-height:0;">
        <svg width="240" height="48" viewBox="0 0 290 52" fill="none" xmlns="http://www.w3.org/2000/svg">
          <polygon points="26,6 6,24 46,24" fill="#0077b6"/>
          <rect x="10" y="24" width="32" height="22" fill="#0096a0"/>
          <rect x="19" y="34" width="8" height="12" rx="1" fill="white" opacity="0.9"/>
          <rect x="23" y="11" width="6" height="2" rx="1" fill="white"/>
          <rect x="25" y="9" width="2" height="6" rx="1" fill="white"/>
          <text x="58" y="24" font-family="Merriweather, serif" font-weight="700" font-size="18" fill="#003d5c">MedPharma</text>
          <text x="58" y="44" font-family="Merriweather, serif" font-weight="700" font-size="18" fill="#0096a0">Connect</text>
        </svg>
      </a>
      <button class="hamburger" id="hamburger" aria-label="Open menu"><span></span><span></span><span></span></button>
      <nav id="main-nav">
        <a href="../index.html">Home</a>
        <a href="../blog.html">Articles</a>
        <a href="../index.html#who-qualifies">Who Qualifies</a>
        <a href="../index.html#benefits">Benefits</a>
        <a href="../index.html#faq">FAQ</a>
        <a href="../index.html#learn-more" class="btn btn-outline">Learn More</a>
      </nav>
    </div>
  </header>'''

FOOTER = '''  <!-- FOOTER -->
  <footer class="footer">
    <div class="container footer-inner">
      <p class="footer-copy">&copy; 2026 MedPharmaConnect. All rights reserved.</p>
      <nav class="footer-nav">
        <a href="../index.html">Home</a>
        <a href="../blog.html">Articles</a>
        <a href="../index.html#faq">FAQ</a>
      </nav>
    </div>
  </footer>

  <script>
    const hamburger = document.getElementById('hamburger');
    const nav = document.getElementById('main-nav');
    if (hamburger) hamburger.addEventListener('click', () => {
      nav.classList.toggle('open'); hamburger.classList.toggle('open');
    });
  </script>'''

STYLE = '''  <style>
    .article-hero { background: var(--navy); padding: 80px 0 60px; position: relative; overflow: hidden; }
    .article-hero-bg { position: absolute; inset: 0; background: radial-gradient(ellipse at 30% 50%, rgba(26,86,160,0.35) 0%, transparent 60%); pointer-events: none; }
    .article-hero-inner { position: relative; z-index: 1; max-width: 800px; }
    .article-hero .eyebrow { color: rgba(255,255,255,0.6); }
    .article-hero h1 { font-size: clamp(1.8rem, 3vw, 2.6rem); color: var(--white); margin-bottom: 24px; line-height: 1.3; }
    .article-hero p { color: rgba(255,255,255,0.75); font-size: 1.05rem; }
    .article-meta-bar { display: flex; gap: 24px; align-items: center; margin-top: 24px; padding-top: 24px; border-top: 1px solid rgba(255,255,255,0.1); flex-wrap: wrap; }
    .meta-item { display: flex; align-items: center; gap: 8px; font-size: 14px; color: rgba(255,255,255,0.7); }
    .article-body { background: var(--white); padding: 80px 0; }
    .article-content { max-width: 760px; margin: 0 auto; }
    .article-content h2 { font-family: 'Merriweather', serif; font-size: 1.6rem; color: var(--navy); margin-top: 48px; margin-bottom: 20px; line-height: 1.3; }
    .article-content h2:first-child { margin-top: 0; }
    .article-content h3 { font-family: 'Inter', sans-serif; font-size: 1.1rem; color: var(--navy); font-weight: 600; margin-top: 32px; margin-bottom: 16px; }
    .article-content p { color: var(--text); font-size: 16px; line-height: 1.8; margin-bottom: 20px; }
    .article-content ul, .article-content ol { color: var(--text); margin: 20px 0 20px 24px; line-height: 1.8; }
    .article-content li { margin-bottom: 12px; font-size: 16px; }
    .article-cta { background: var(--light); padding: 60px 0; text-align: center; margin-top: 80px; }
    .article-cta h3 { font-family: 'Merriweather', serif; font-size: 1.6rem; color: var(--navy); margin-bottom: 16px; }
    .article-cta p { color: var(--muted); margin-bottom: 32px; max-width: 600px; margin-left: auto; margin-right: auto; }
    .disclaimer-inline { font-size: 13px; color: var(--muted); margin-top: 40px; padding-top: 24px; border-top: 1px solid var(--border); }
    @media (max-width: 600px) {
      .article-hero { padding: 60px 0 40px; } .article-hero h1 { font-size: 1.5rem; }
      .article-body { padding: 60px 0; } .article-meta-bar { flex-direction: column; align-items: flex-start; gap: 12px; }
      .article-content h2 { font-size: 1.3rem; }
    }
  </style>'''

def build_page(fm, body_html):
    title = fm.get("title", "MedPharmaConnect")
    desc  = fm.get("description", "")
    eyebrow = fm.get("category", "Physician Mortgages")
    read = fm.get("readTime", "5 min read")
    when = pretty_date(fm.get("date", ""))
    e = lambda s: html.escape(s, quote=True)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{e(title)} | MedPharmaConnect</title>
  <meta name="description" content="{e(desc)}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Merriweather:wght@400;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../styles.css" />
{STYLE}
</head>
<body>

{NAV}

  <!-- ARTICLE HERO -->
  <section class="article-hero">
    <div class="article-hero-bg"></div>
    <div class="container article-hero-inner">
      <span class="eyebrow">{e(eyebrow)}</span>
      <h1>{e(title)}</h1>
      <p>{e(desc)}</p>
      <div class="article-meta-bar">
        <span class="meta-item">{e(read)}</span>
        <span class="meta-item">{e(when)}</span>
      </div>
    </div>
  </section>

  <!-- ARTICLE BODY -->
  <section class="article-body">
    <div class="container article-content">

{body_html}

<p class="disclaimer-inline"><em>MedPharmaConnect is an educational resource, not a lender. Always verify program details, current rates, and eligibility with licensed mortgage professionals.</em></p>

    </div>
  </section>

  <!-- CTA -->
  <section class="article-cta">
    <div class="container">
      <h3>Ready to Explore Your Options?</h3>
      <p>MedPharmaConnect is your free, unbiased educational resource for physician mortgage loans. No lenders pay to be featured here.</p>
      <a href="../index.html#learn-more" class="btn btn-primary">Explore the Guide</a>
    </div>
  </section>

{FOOTER}

</body>
</html>
'''

def blog_card(fn, fm):
    dcat, label = category_meta(fm.get("category"))
    e = lambda s: html.escape(s, quote=True)
    return f'''      <!-- auto-published -->
      <a href="articles/{fn}" class="article-card" data-category="{dcat}">
        <span class="article-tag">{label}</span>
        <h3 class="article-title">{e(fm.get("title",""))}</h3>
        <p class="article-desc">{e(fm.get("description",""))}</p>
        <div class="article-meta">
          <span>{e(fm.get("readTime","5 min read"))}</span>
          <span>{e(pretty_date(fm.get("date","")))}</span>
        </div>
        <span class="article-read-link">Read Article →</span>
      </a>

'''

# ---------- main ----------
def main():
    published_titles = []
    for f in glob.glob(os.path.join(ART_DIR, "*.html")):
        m = re.search(r"<title>(.*?)</title>", open(f, encoding="utf-8").read(), re.S)
        if m:
            published_titles.append(norm_tokens(html.unescape(m.group(1))))

    pub_map = {}
    if os.path.exists(MAP_FILE):
        pub_map = json.load(open(MAP_FILE))
    skip_list = set()
    if os.path.exists(SKIP_FILE):
        skip_list = set(json.load(open(SKIP_FILE)))

    new_cards, published, skipped = [], [], []
    for md in sorted(glob.glob(os.path.join(MD_DIR, "*.md"))):
        base = os.path.basename(md)
        fm, body = parse_md(md)
        title = fm.get("title", "")
        if not title:
            continue
        toks = norm_tokens(title)

        # editorial hold — never publish (reversible: edit content/publish-skip.json)
        if base in skip_list:
            skipped.append((base, title, 0, "editorial hold (publish-skip.json)"))
            continue

        # already published by this script before?
        if base in pub_map and os.path.exists(os.path.join(ART_DIR, pub_map[base])):
            continue

        # duplicate of an existing live article (hand-built or prior run)?
        sim = max((jaccard(toks, t) for t in published_titles), default=0)
        if sim >= THRESHOLD:
            skipped.append((base, title, round(sim, 2), "matches existing article"))
            continue

        fn = slugify(title) + ".html"
        if os.path.exists(os.path.join(ART_DIR, fn)):
            skipped.append((base, title, 1.0, "slug already exists"))
            continue

        if not DRY:
            with open(os.path.join(ART_DIR, fn), "w", encoding="utf-8") as f:
                f.write(build_page(fm, md_to_html(body)))
            pub_map[base] = fn
        new_cards.append(blog_card(fn, fm))
        published.append((base, fn, title))
        published_titles.append(toks)   # prevent within-run near-dupes

    # insert new cards at top of the blog grid
    if new_cards and not DRY:
        h = open(BLOG, encoding="utf-8").read()
        anchor = '<div class="article-grid" id="article-grid">'
        if anchor in h:
            h = h.replace(anchor, anchor + "\n" + "".join(new_cards), 1)
            open(BLOG, "w", encoding="utf-8").write(h)
        if not DRY:
            json.dump(pub_map, open(MAP_FILE, "w"), indent=2)

    # report
    print(f"{'DRY RUN — ' if DRY else ''}Publisher results")
    print(f"  Published: {len(published)}")
    for b, fn, t in published:
        print(f"    + {b}  ->  articles/{fn}")
    print(f"  Skipped as duplicate/near-duplicate: {len(skipped)}")
    for b, t, s, why in skipped:
        print(f"    - {b}  (sim={s}, {why})  {t[:70]}")

    # enrich + sitemap (schema, canonical, OG, lead CTA) via the SEO agent
    if published and not DRY and os.path.exists(SEO_AGENT):
        print("\nRunning SEO enrichment + sitemap...")
        subprocess.run([sys.executable, SEO_AGENT, ROOT], check=False)

if __name__ == "__main__":
    main()
