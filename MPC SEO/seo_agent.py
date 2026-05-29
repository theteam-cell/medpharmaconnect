#!/usr/bin/env python3
"""
MedPharmaConnect SEO Agent
==========================
Maximizes on-site SEO and lead conversion for medpharmaconnect.com.

What it does (idempotent — safe to run repeatedly):
  1. Injects <head> SEO into index.html and every articles/*.html:
       - <link rel="canonical">
       - Open Graph + Twitter card tags
       - JSON-LD structured data:
            index.html  -> Organization + WebSite + FAQPage
            articles/*  -> Article + BreadcrumbList
  2. Injects a branded lead-capture CTA block before the footer of each
     article (drives organic readers to the contact form + DTI calculator).
  3. Generates sitemap.xml and robots.txt at the site root.
  4. Writes a run report to MPC SEO/seo-report-latest.md.

Guards (HTML comment markers) prevent duplicate insertion on re-runs.

Usage:  python3 seo_agent.py [/path/to/practicepath]
"""

import os, re, sys, html, datetime, glob

DOMAIN = "https://medpharmaconnect.com"
LOGO   = f"{DOMAIN}/medpharmaconnect-logo-800.png"

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART_DIR = os.path.join(ROOT, "articles")
SEO_DIR = os.path.join(ROOT, "MPC SEO")

SCHEMA_MARK = "<!-- SEO-AGENT-SCHEMA -->"
CTA_MARK    = "<!-- SEO-AGENT-CTA -->"
RELATED_MARK = "<!-- SEO-AGENT-RELATED -->"

_STOP = set("a an the of to for and or in on at is are with your you how what "
            "when does do as that this it its why who be can not into about "
            "before after they them his her doctors doctor".split())
def _tokens(title):
    return set(w for w in re.findall(r"[a-z0-9]+", title.lower())
               if w not in _STOP and len(w) > 2)
def _jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0

report = []
def log(msg):
    report.append(msg)
    print(msg)

# ---- helpers ---------------------------------------------------------------
def get_title(h):
    m = re.search(r"<title>(.*?)</title>", h, re.S)
    return html.unescape(m.group(1).strip()) if m else "MedPharmaConnect"

def get_desc(h):
    m = re.search(r'<meta\s+name="description"\s+content="(.*?)"', h, re.S)
    return html.unescape(m.group(1).strip()) if m else ""

def headline(title):
    # strip the " | MedPharmaConnect" suffix for OG/schema headline
    return re.sub(r"\s*\|\s*MedPharmaConnect\s*$", "", title).strip()

def file_date(path):
    return datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()

def esc(s):
    return html.escape(s, quote=True)

# ---- FAQ data for homepage FAQPage schema (mirrors index.html FAQ section) --
FAQ = [
    ("I have $300K+ in student loans. Can I really qualify?",
     "Yes. Traditional loans count your full monthly student loan payment against your debt-to-income ratio. Many physician loan programs use a much smaller figure, or exclude deferred loans entirely, making qualification far more realistic for new attendings and residents."),
    ("Is this just for residents and fellows, or can attendings use it too?",
     "Both. Physician loans are available to residents, fellows, and fully practicing attendings. Some programs have income or years-in-practice requirements, so eligibility varies, but this product is not limited to early-career physicians."),
    ("What's the catch? Why don't more people know about this?",
     "There's no hidden catch, but there are tradeoffs. Rates may be slightly higher than conventional loans, and not every lender offers them. Most doctors don't know about these programs because they aren't heavily advertised."),
    ("Do I need perfect credit to qualify?",
     "Not perfect, but strong credit helps. Most programs look for a 700+ credit score, though some lenders work with scores in the mid-600s depending on other factors."),
    ("Can I use this loan to buy a second home or investment property?",
     "Generally no. Physician loans are structured for primary residences only. They're not intended for vacation properties or rental investments."),
    ("How is this different from an FHA loan?",
     "FHA loans are government-backed and often require mortgage insurance for the life of the loan, with lower limits. Physician loans are conventional products with no PMI requirement and much higher limits."),
    ("I'm a pharmacist / dentist — does this apply to me?",
     "Often yes. While the name says 'physician,' many lenders extend these programs to PharmDs, DDSs, DMDs, and other doctoral-level healthcare professionals. Eligibility varies by lender."),
]

# ---- build <head> SEO block ------------------------------------------------
def head_block(url, title, desc, jsonld):
    hl = esc(headline(title))
    d  = esc(desc)
    return f"""  {SCHEMA_MARK}
  <link rel="canonical" href="{url}" />
  <meta property="og:type" content="{ 'website' if url.rstrip('/')==DOMAIN else 'article' }" />
  <meta property="og:title" content="{hl}" />
  <meta property="og:description" content="{d}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:site_name" content="MedPharmaConnect" />
  <meta property="og:image" content="{LOGO}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{hl}" />
  <meta name="twitter:description" content="{d}" />
  <meta name="twitter:image" content="{LOGO}" />
{jsonld}
"""

def jsonld_block(objs):
    import json
    out = []
    for o in objs:
        out.append('  <script type="application/ld+json">\n  ' +
                   json.dumps(o, indent=2).replace("\n", "\n  ") + "\n  </script>")
    return "\n".join(out)

def inject_head(path, url, jsonld):
    with open(path, encoding="utf-8") as f:
        h = f.read()
    if SCHEMA_MARK in h:
        # refresh: strip old block then re-inject
        h = re.sub(re.escape(SCHEMA_MARK) + r".*?(?=</head>)", "", h, flags=re.S)
    title, desc = get_title(h), get_desc(h)
    # remove any pre-existing canonical/OG/Twitter tags so we emit one clean set
    head_split = h.split("</head>", 1)
    if len(head_split) == 2:
        head, rest = head_split
        head = re.sub(r'[ \t]*<link[^>]*rel="canonical"[^>]*>\n?', "", head)
        head = re.sub(r'[ \t]*<meta[^>]*property="og:[^>]*>\n?', "", head)
        head = re.sub(r'[ \t]*<meta[^>]*name="twitter:[^>]*>\n?', "", head)
        h = head + "</head>" + rest
    block = head_block(url, title, desc, jsonld)
    h = h.replace("</head>", block + "</head>", 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(h)
    return title, desc

# ---- lead-capture CTA (articles) -------------------------------------------
def cta_html():
    return f"""
  {CTA_MARK}
  <section style="background:#003d5c;padding:56px 0;">
    <div class="container" style="max-width:760px;margin:0 auto;text-align:center;color:#fff;padding:0 20px;">
      <h2 style="font-family:Merriweather,serif;color:#fff;font-size:1.7rem;margin:0 0 .6rem;">Want to know what you'd actually qualify for?</h2>
      <p style="color:rgba(255,255,255,.85);font-size:1.05rem;line-height:1.6;margin:0 0 1.6rem;">
        MedPharmaConnect is a free educational resource. If you're ready to explore your options,
        we can connect you with loan officers who specialize in physician mortgages — no pressure, no spam.
      </p>
      <div style="display:flex;gap:.8rem;justify-content:center;flex-wrap:wrap;">
        <a href="../index.html#learn-more" style="background:#0096a0;color:#fff;font-weight:600;padding:.85rem 1.6rem;border-radius:8px;text-decoration:none;display:inline-block;">Get matched with a lender →</a>
        <a href="../tools/dti-calculator.html" style="background:transparent;border:1.5px solid rgba(255,255,255,.5);color:#fff;font-weight:600;padding:.85rem 1.6rem;border-radius:8px;text-decoration:none;display:inline-block;">Try the DTI Calculator</a>
      </div>
    </div>
  </section>
"""

def inject_cta(path):
    with open(path, encoding="utf-8") as f:
        h = f.read()
    if CTA_MARK in h:
        return False
    # insert immediately before the footer
    m = re.search(r"\n\s*<!-- FOOTER -->", h)
    if not m:
        m = re.search(r"\n\s*<footer", h)
    if not m:
        return False
    idx = m.start()
    h = h[:idx] + "\n" + cta_html() + h[idx:]
    with open(path, "w", encoding="utf-8") as f:
        f.write(h)
    return True

# ---- related articles (internal linking) -----------------------------------
def related_html(items):
    links = "\n".join(
        f'        <li style="margin-bottom:10px;"><a href="{fn}" style="color:#0077b6;text-decoration:none;font-weight:500;">{esc(t)} →</a></li>'
        for fn, t in items)
    return f"""
  {RELATED_MARK}
  <section style="background:#fff;padding:0 0 56px;">
    <div class="container" style="max-width:760px;margin:0 auto;padding:0 20px;">
      <div style="border-top:1px solid #e2e8f0;padding-top:32px;">
        <h2 style="font-family:Merriweather,serif;font-size:1.3rem;color:#003d5c;margin:0 0 16px;">Related reading</h2>
        <ul style="list-style:none;padding:0;margin:0;">
{links}
        </ul>
      </div>
    </div>
  </section>
"""

def inject_related(path, items):
    with open(path, encoding="utf-8") as f:
        h = f.read()
    # strip any prior related block so links stay fresh on re-run
    h = re.sub(r"\n?[ \t]*" + re.escape(RELATED_MARK) + r".*?</section>\n?", "\n", h, flags=re.S)
    if not items:
        with open(path, "w", encoding="utf-8") as f:
            f.write(h)
        return
    block = related_html(items)
    for anchor in ("<!-- CTA -->", CTA_MARK, "<!-- FOOTER -->", "<footer"):
        m = re.search(r"\n\s*" + re.escape(anchor), h)
        if m:
            idx = m.start()
            h = h[:idx] + "\n" + block + h[idx:]
            break
    with open(path, "w", encoding="utf-8") as f:
        f.write(h)

# ---- INDEX -----------------------------------------------------------------
def do_index():
    path = os.path.join(ROOT, "index.html")
    if not os.path.exists(path):
        log("! index.html not found"); return
    org = {
        "@context": "https://schema.org", "@type": "Organization",
        "name": "MedPharmaConnect", "url": DOMAIN, "logo": LOGO,
        "description": "Free educational resource on physician mortgage loans for doctors, dentists, and pharmacists.",
        "sameAs": [
            "https://www.facebook.com/profile.php?id=61588771821558",
            "https://www.linkedin.com/company/115868275",
            "https://x.com/medpharmaconnec",
            "https://www.instagram.com/medpharmaconnect",
            "https://www.youtube.com/@medpharmaconnect",
            "https://www.tiktok.com/@medpharmaconnect",
        ],
    }
    website = {
        "@context": "https://schema.org", "@type": "WebSite",
        "name": "MedPharmaConnect", "url": DOMAIN,
    }
    faq = {
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in FAQ
        ],
    }
    jsonld = jsonld_block([org, website, faq])
    t, _ = inject_head(path, DOMAIN + "/", jsonld)
    log(f"index.html        -> schema(Org+WebSite+FAQ) + canonical/OG")

# ---- ARTICLES --------------------------------------------------------------
def do_articles():
    files = sorted(glob.glob(os.path.join(ART_DIR, "*.html")))
    # precompute titles/tokens for related-article linking
    meta = {}
    for p in files:
        t = get_title(open(p, encoding="utf-8").read())
        meta[os.path.basename(p)] = (headline(t), _tokens(t))
    cta_added = 0
    for path in files:
        fn = os.path.basename(path)
        url = f"{DOMAIN}/articles/{fn}"
        with open(path, encoding="utf-8") as f:
            h = f.read()
        title, desc = get_title(h), get_desc(h)
        date = file_date(path)
        article = {
            "@context": "https://schema.org", "@type": "Article",
            "headline": headline(title),
            "description": desc,
            "image": LOGO,
            "datePublished": date, "dateModified": date,
            "author": {"@type": "Organization", "name": "MedPharmaConnect"},
            "publisher": {"@type": "Organization", "name": "MedPharmaConnect",
                          "logo": {"@type": "ImageObject", "url": LOGO}},
            "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        }
        breadcrumb = {
            "@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": DOMAIN + "/"},
                {"@type": "ListItem", "position": 2, "name": "Articles", "item": DOMAIN + "/blog.html"},
                {"@type": "ListItem", "position": 3, "name": headline(title), "item": url},
            ],
        }
        inject_head(path, url, jsonld_block([article, breadcrumb]))
        if inject_cta(path):
            cta_added += 1
        # internal links: top-3 most similar sibling articles
        my_t = meta[fn][1]
        ranked = sorted(((b, _jaccard(my_t, mt)) for b, (_, mt) in meta.items() if b != fn),
                        key=lambda x: x[1], reverse=True)
        rel = [(b, meta[b][0]) for b, s in ranked if s > 0][:3]
        inject_related(path, rel)
    log(f"articles/         -> {len(files)} files: canonical/OG + Article+Breadcrumb schema")
    log(f"articles/         -> lead CTA added to {cta_added} (skipped {len(files)-cta_added} already had it)")
    log(f"articles/         -> related-article internal links refreshed on {len(files)} files")
    return files

# ---- SITEMAP + ROBOTS ------------------------------------------------------
def do_sitemap(article_files):
    urls = []
    def add(rel, path):
        if os.path.exists(path):
            urls.append((f"{DOMAIN}/{rel}".rstrip("/") if rel else DOMAIN + "/",
                         file_date(path)))
    add("", os.path.join(ROOT, "index.html"))
    add("blog.html", os.path.join(ROOT, "blog.html"))
    add("tools/dti-calculator.html", os.path.join(ROOT, "tools", "dti-calculator.html"))
    add("guides/lender-comparison.html", os.path.join(ROOT, "guides", "lender-comparison.html"))
    for p in article_files:
        urls.append((f"{DOMAIN}/articles/{os.path.basename(p)}", file_date(p)))

    body = "\n".join(
        f'  <url>\n    <loc>{u}</loc>\n    <lastmod>{d}</lastmod>\n  </url>'
        for u, d in urls)
    sm = ('<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + body + "\n</urlset>\n")
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sm)
    robots = ("User-agent: *\n"
              "Allow: /\n\n"
              "# Block deploy/build artifacts\n"
              "Disallow: /netlify-deploy.html\n"
              "Disallow: /.netlify/\n\n"
              f"Sitemap: {DOMAIN}/sitemap.xml\n")
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots)
    log(f"sitemap.xml       -> {len(urls)} URLs")
    log("robots.txt        -> created with sitemap reference")

# ---- MAIN ------------------------------------------------------------------
def main():
    log(f"# MedPharmaConnect SEO Agent run — {datetime.datetime.now():%Y-%m-%d %H:%M}")
    log(f"Root: {ROOT}\n")
    do_index()
    files = do_articles()
    do_sitemap(files)
    os.makedirs(SEO_DIR, exist_ok=True)
    with open(os.path.join(SEO_DIR, "seo-report-latest.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")
    log("\nDone. Review changes with `git diff`, then deploy.")

if __name__ == "__main__":
    main()
