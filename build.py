#!/usr/bin/env python
"""Generate the Santhiago Collection static site from santhiago.json.

Site URL is configurable via the SITE_URL env var, defaulting to localhost
for local development. Set it to the public hostname (e.g. "https://art.example.com")
when generating for a production deploy so canonical URLs and OG tags are correct.
"""
import json, html, os, urllib.parse

# Canonical site origin. Override with SITE_URL env var.
SITE_URL = os.environ.get("SITE_URL", "http://localhost:8080").rstrip("/")

with open("_meta/santhiago.json", "r", encoding="utf-8") as f:
    cat = json.load(f)

CATS = cat["categories"]  # ordered list of dicts
CAT_BY_SLUG = {c["slug"]: c for c in CATS}
PAINTINGS = cat["paintings_by_cat"]
OUT = "public"


def absolute_url(path):
    """Convert a relative path ('foo.html' or '/foo.html') to an absolute URL
    using SITE_URL. Strips any leading slash on the path to avoid double slashes."""
    if not path:
        return SITE_URL
    p = path.lstrip("/")
    return f"{SITE_URL}/{p}" if p else SITE_URL


def fmt_dims(raw):
    """Normalize dimensions for display as 'width × height cm'.
    - Catalog stores dimensions in arbitrary order (e.g. '70/50', '50/70', '92-65').
    - Display is ALWAYS 'width × height cm':
        * For a portrait painting (taller than wide), display is 'short × long cm'
          (e.g. 50 × 70 cm). The 'width' (horizontal) is the shorter side.
        * For a landscape painting (wider than tall), display is 'long × short cm'
          (e.g. 70 × 50 cm). The 'width' (horizontal) is the longer side.
    - Width is ALWAYS the horizontal dimension, height is ALWAYS the vertical.
      This matches how the artist/photographer describes canvas size. """
    if not raw:
        return ""
    # strip any trailing 'cm' so we don't duplicate it
    s = raw.strip()
    if s.lower().endswith("cm"):
        s = s[:-2].strip()
    # normalize separators: both '/' and '-' separate the two numbers
    s = s.replace("-", "/")
    parts = [p.strip() for p in s.split("/") if p.strip()]
    if len(parts) != 2:
        return f"{s} cm"  # fallback
    # ALWAYS display as width × height, where:
    #   width  = horizontal dimension (the shorter side for a portrait,
    #                                     the longer side for a landscape)
    #   height = vertical dimension
    # The source data is already in this convention, so we just render as-is.
    return f"{parts[0]} × {parts[1]} cm"


def picture(asset_path, alt, eager=False, sizes_attr="(max-width: 720px) 50vw, (max-width: 1100px) 33vw, 1100px"):
    """Emit a <picture> element with WebP source + JPEG fallback.
    Uses responsive srcset so phones download the smaller thumbnail variant.

    asset_path is the FULL-size asset path (e.g. 'assets/_MAG9969.jpg').
    Expects sibling files:
      - {basename}.webp         — WebP at full size
      - {basename}-thumb.webp   — WebP thumbnail (max 480px wide)
      - the original JPEG (fallback)
    """
    # derive paths
    base, ext = os.path.splitext(asset_path)
    webp_path  = base + ".webp"
    thumb_path = base + "-thumb.webp"

    # load="lazy" for everything except images that should load immediately
    # (e.g. the hero portrait — first paint, above the fold)
    lazy = "" if eager else ' loading="lazy"'
    async_dec = ' decoding="async"' if not eager else ""

    return f'''<picture>
  <source type="image/webp" media="(max-width: 720px)" srcset="{thumb_path}">
  <source type="image/webp" srcset="{webp_path}">
  <img src="{asset_path}" alt="{html.escape(alt)}"{lazy}{async_dec}>
</picture>'''


# ---------- Shared partials ----------

CRITICAL_CSS = """
/* critical: theme tokens + above-the-fold layout. Full stylesheet loads in <link> below. */
:root,[data-theme=light]{--bg:#faf8f5;--bg-soft:#f0ebe3;--ink:#1a1612;--ink-soft:#4a4540;--ink-mute:#7d7770;--line:#d8d2c8;--accent:#8b6f47;--shadow:0 2px 20px rgba(50,35,20,.06)}
[data-theme=dark]{--bg:#0e0d0c;--bg-soft:#221f1c;--ink:#ece6dd;--ink-soft:#b8b0a4;--ink-mute:#7d7770;--line:#2e2a26;--accent:#c4a87d}
*{box-sizing:border-box;min-width:0}
html,body{margin:0;padding:0}
html{color-scheme:light dark}
body{font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif;background:var(--bg);color:var(--ink);line-height:1.6;font-size:16px;overflow-x:hidden;transition:background 220ms ease,color 220ms ease}
img{max-width:100%;height:auto;display:block}
.serif{font-family:'Cormorant Garamond','Times New Roman',serif}
h1,h2,h3{font-family:'Cormorant Garamond','Times New Roman',serif;font-weight:500;letter-spacing:-.01em;word-break:break-word}
h1{font-size:clamp(2.2rem,8vw,4.5rem);margin:0 0 .5em;line-height:1.05}
.eyebrow{font-size:.75rem;font-weight:500;letter-spacing:.18em;text-transform:uppercase;color:var(--ink-mute)}
.site-header{position:sticky;top:0;z-index:50;background:color-mix(in srgb,var(--bg) 92%,transparent);backdrop-filter:saturate(180%) blur(16px);-webkit-backdrop-filter:saturate(180%) blur(16px);border-bottom:1px solid var(--line);box-shadow:0 4px 20px rgba(0,0,0,.04)}
.site-header__inner{max-width:1200px;margin:0 auto;padding:1rem 1.25rem;display:flex;align-items:center;justify-content:space-between;gap:.75rem}
.brand__name{font-family:'Cormorant Garamond','Times New Roman',serif;font-size:1.4rem;font-weight:500;letter-spacing:-.005em;white-space:nowrap}
.hero{max-width:1200px;margin:0 auto;padding:4rem 1.25rem 3rem;display:grid;grid-template-columns:repeat(12,1fr);gap:1rem 2rem;align-items:start}
.hero__title{margin:0}
.hero__lede{color:var(--ink-soft);font-size:1.05rem;max-width:36ch;margin:1.25rem 0}
.hero__meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:1rem 1.5rem;margin-top:1.75rem;padding-top:1.75rem;border-top:1px solid var(--line)}
.hero__meta dt{font-size:.7rem;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-mute);margin:0}
.hero__meta dd{margin:.25rem 0 0;font-size:.95rem;color:var(--ink-soft)}
.hero__art{position:relative;min-height:320px;background:var(--bg-soft);border-radius:4px;overflow:hidden;box-shadow:var(--shadow);max-width:100%;display:flex;align-items:center;justify-content:center}
.hero__art img{width:100%;height:auto;display:block}
@media (max-width:800px){.hero{grid-template-columns:1fr;padding:3rem 1.25rem 2rem;gap:1.75rem}.hero__art{order:3}.hero__meta{order:1;grid-area:auto}.hero__lead{order:1}.artist-bio{order:4}}
/* skip link visible on focus */
.skip-link{position:absolute;top:-100px;left:0;background:var(--ink);color:var(--bg);padding:.75rem 1.25rem;font-size:.9rem;font-weight:600;letter-spacing:.04em;z-index:200;text-decoration:none;border-bottom-right-radius:4px;transition:top 200ms ease}
.skip-link:focus,.skip-link:focus-visible{top:0;outline:3px solid var(--accent);outline-offset:2px}
/* focus-visible high contrast outline */
:focus-visible{outline:3px solid var(--accent);outline-offset:2px;border-radius:2px}
/* system theme preference for unstyled load */
@media (prefers-color-scheme:dark){:root:not([data-theme]){--bg:#0e0d0c;--bg-soft:#221f1c;--bg-elev:#1a1815;--ink:#ece6dd;--ink-soft:#b8b0a4;--ink-mute:#7d7770;--line:#2e2a26;--accent:#c4a87d;--accent-soft:#d9c4a0}}
"""

def head(title, description="", canonical_path="", og_image=None, og_type="website",
          jsonld=None, skip_link_text="Skip to main content"):
    css_ver = "v=2026-09-01-r26"
    js_ver = "v=2026-09-01-r26"
    canonical_url = absolute_url(canonical_path) if canonical_path else ""
    if not og_image:
        og_image = f"{SITE_URL}/assets/Antonia%20Portrait.jpg"
    jsonld_block = (chr(10) + "  <script type=\"application/ld+json\">" + jsonld + "</script>") if jsonld else ""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <title>{html.escape(title)} — Antónia de Távora</title>
  <meta name="description" content="{html.escape(description)}">
  <meta name="author" content="Antónia Camilo de Távora">
  <meta name="robots" content="index, follow">
  <meta name="theme-color" content="#faf8f5" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#0e0d0c" media="(prefers-color-scheme: dark)">
  <link rel="canonical" href="{canonical_url}">
  <link rel="icon" type="image/svg+xml" href="assets/favicon.svg">
  <link rel="apple-touch-icon" href="assets/Antonia Portrait.jpg">
  <meta http-equiv="Content-Language" content="en">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <!-- preload CSS for fonts so it starts downloading immediately -->
  <link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Inter:wght@400;500;600&display=swap">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Inter:wght@400;500;600&display=swap" media="print" onload="this.media='all'">
  <link rel="preload" as="image" href="assets/Antonia Portrait.webp">
  <!-- Open Graph (Facebook, LinkedIn, WhatsApp, iMessage) -->
  <meta property="og:type" content="{html.escape(og_type)}">
  <meta property="og:site_name" content="Antónia de Távora · Santhiago Collection">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(description)}">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:image" content="{og_image}">
  <meta property="og:image:alt" content="Antónia de Távora — Santhiago Collection">
  <meta property="og:locale" content="en_US">
  <!-- Twitter / X Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{html.escape(title)}">
  <meta name="twitter:description" content="{html.escape(description)}">
  <meta name="twitter:image" content="{og_image}">
  <meta name="twitter:image:alt" content="Antónia de Távora — Santhiago Collection">
  <!-- critical CSS inlined so first paint doesn't wait for external stylesheet -->
  <style>{CRITICAL_CSS}</style>
  <!-- full stylesheet loads asynchronously via media=print swap -->
  <link rel="stylesheet" href="assets/style.css?{css_ver}" media="print" onload="this.media='all'">
  <noscript><link rel="stylesheet" href="assets/style.css?{css_ver}"></noscript>
  <script>document.documentElement.setAttribute('data-theme', localStorage.getItem('antonia-theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));</script>{jsonld_block}
</head>
<body>
  <a class="skip-link" href="#main">{html.escape(skip_link_text)}</a>
'''


def theme_toggle():
    return '''<button class="theme-toggle" type="button" aria-label="Toggle theme" aria-pressed="false">
  <svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
  <svg class="sun"  viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>
</button>'''


def nav_toggle():
    return '''<button class="nav-toggle" type="button" aria-label="Open menu" aria-controls="primary-nav" aria-expanded="false">
  <svg class="icon-open" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
  <svg class="icon-close" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
</button>'''


def nav_close():
    """Large, obvious close button rendered INSIDE the mobile overlay."""
    return '''<button class="nav-close" type="button" aria-label="Close menu">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
  <span>Close</span>
</button>'''


def header(active=None, depth=".."):
    nav_items = [("index.html", "Collection", depth + "/index.html")]
    for c in CATS:
        nav_items.append((f"{c['slug']}.html", c["label"], depth + f"/{c['slug']}.html"))
    links = []
    for href, label, path in nav_items:
        cls = ' class="is-active"' if (active and label == active) else ""
        links.append(f'<a href="{path}"{cls}>{html.escape(label)}</a>')
    return f'''<header class="site-header" role="banner">
  <div class="site-header__inner">
    <div class="brand">
      <a href="{depth}/index.html">
        <span class="brand__name">Antónia de Távora</span>
      </a>
    </div>
    {nav_toggle()}
    <nav class="nav" id="primary-nav" role="navigation" aria-label="Main">
      {nav_close()}
      {''.join(links)}
      {theme_toggle()}
    </nav>
  </div>
</header>
'''


def footer(depth=".."):
    # Footer is intentionally minimal — the artist info + collection summary
    # are already shown prominently in the hero on the home page. The footer
    # only carries the contact line (which is the one piece of info that's
    # useful on every page, including detail pages where there's no hero).
    return f'''<footer class="site-footer" role="contentinfo">
  <div>
    <h4>Contact</h4>
    <p>Antónia Camilo de Távora</p>
    <p><a href="mailto:antonia.detavora@gmail.com">antonia.detavora@gmail.com</a></p>
    <p style="margin-top: 1rem; color: var(--ink-mute); font-size: 0.85rem;">Riedhofstrasse 23, 8804 Au, Switzerland</p>
  </div>
  <div>
    <h4>Explore</h4>
    <p><a href="{depth}/portraits.html">Portraits</a></p>
    <p><a href="{depth}/natures-mortes.html">Naturezas Mortas</a></p>
    <p><a href="{depth}/paisagens.html">Paisagens</a></p>
    <p style="margin-top: 1rem;"><a href="{depth}/index.html">← Collection home</a></p>
  </div>
</footer>
<div class="copyright">© Antónia Camilo de Távora. All artworks by the artist.</div>
'''


# ---------- JSON-LD structured data generators ----------

def jsonld_person():
    """Schema.org Person for the artist (used on every page via the home
    page's graph)."""
    return {
        "@context": "https://schema.org",
        "@type": "Person",
        "@id": f"{SITE_URL}/#antonia-de-tavora",
        "name": "Antónia Camilo de Távora",
        "alternateName": "Maria Antónia Camilo de Távora Vasconcelos da Silva",
        "url": SITE_URL,
        "email": "mailto:antonia.detavora@gmail.com",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "Riedhofstrasse 23",
            "addressLocality": "Au",
            "postalCode": "8804",
            "addressCountry": "CH"
        },
        "jobTitle": "Painter",
        "alumniOf": [
            {"@type": "CollegeOrUniversity", "name": "Fine Arts School of Lisbon"},
            {"@type": "CollegeOrUniversity", "name": "University of Neuchâtel"}
        ],
        "knowsAbout": ["Oil painting", "Botany", "Plant physiology", "Biology"],
        "sameAs": []
    }


def jsonld_collection():
    """Schema.org Collection for the Santhiago paintings."""
    items = []
    for cat_slug_inner, items_list in PAINTINGS.items():
        for p in items_list:
            items.append({
                "@type": "ListItem",
                "position": p["num"],
                "name": p["title"],
                "url": absolute_url(f"paintings/{cat_slug_inner}/{p['slug']}.html"),
                "image": absolute_url(p["asset_path"]),
            })
    return {
        "@context": "https://schema.org",
        "@type": "Collection",
        "name": "Santhiago Collection",
        "description": cat["summary"],
        "creator": {"@id": f"{SITE_URL}/#antonia-de-tavora"},
        "hasPart": items,
        "url": absolute_url(""),
    }


def jsonld_visual_artwork(p, cat_slug):
    """Schema.org VisualArtwork for a single painting detail page."""
    dims = p["dimensions"].replace(" cm", "").split("/")
    return {
        "@context": "https://schema.org",
        "@type": "VisualArtwork",
        "name": p["title"],
        "image": absolute_url(p["asset_path"]),
        "creator": {"@id": f"{SITE_URL}/#antonia-de-tavora"},
        "dateCreated": "2000-2004",
        "material": "Oil on canvas",
        "width": (dims[0] + " cm") if len(dims) > 0 else None,
        "height": (dims[1] + " cm") if len(dims) > 1 else None,
        "artform": "Painting",
        "genre": cat_slug.capitalize(),
        "isPartOf": {"@id": f"{SITE_URL}/#collection"},
        "url": absolute_url(f"paintings/{cat_slug}/{p['slug']}.html"),
    }


def jsonld_webpage(title, description, canonical_path):
    """Schema.org WebPage for category and home pages."""
    return {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": description,
        "url": absolute_url(canonical_path),
        "isPartOf": {"@id": f"{SITE_URL}/#collection"},
        "about": {"@id": f"{SITE_URL}/#antonia-de-tavora"},
    }


def serialize_jsonld(*items):
    """Serialize one or more dicts as a single JSON-LD <script> with @graph."""
    return json.dumps({"@context": "https://schema.org", "@graph": list(items)},
                     ensure_ascii=False)


def lightbox():
    return '''<div class="lightbox" role="dialog" aria-hidden="true" aria-label="Image viewer">
  <button class="lightbox__close" type="button" aria-label="Close">×</button>
  <img alt="">
</div>'''


def footer_scripts():
    js_ver = "v=2026-09-01-r24"
    return f'''<script src="assets/app.js?{js_ver}" defer></script>
</body>
</html>'''


# ---------- HOME ----------

# Hero = the portrait
hero_asset = "assets/Antonia Portrait.jpg"
total_paintings = sum(len(v) for v in PAINTINGS.values())

home = head("Santhiago Collection — Antónia de Távora",
            "Oil paintings by Antónia de Távora made in Cascais and Sintra, Portugal, between 2000 and 2004.",
            canonical_path="index.html",
            og_type="website",
            jsonld=serialize_jsonld(jsonld_collection(), jsonld_person())) + \
    header(depth=".") + f'''
<main role="main" id="main" tabindex="-1">
  <section class="hero">
    <div class="hero__lead">
      <div class="eyebrow">The Collection</div>
      <h1 class="hero__title serif">Santhiago</h1>
      <p class="hero__lede">{cat["summary"]}</p>
    </div>
    <div class="hero__art">
      <picture>
        <source type="image/webp" media="(max-width: 720px)" srcset="{os.path.splitext(hero_asset)[0]}-thumb.webp">
        <source type="image/webp" srcset="{os.path.splitext(hero_asset)[0]}.webp">
        <img src="{hero_asset}" alt="Portrait of Antónia Camilo de Távora" decoding="async">
      </picture>
    </div>
    <dl class="hero__meta">
      <div><dt>Artist</dt><dd>Antónia Camilo de Távora</dd></div>
      <div><dt>Period</dt><dd>2000 – 2004</dd></div>
      <div><dt>Medium</dt><dd>Oil on canvas</dd></div>
      <div><dt>Works</dt><dd>{total_paintings} pieces</dd></div>
    </dl>
    <div class="artist-bio">
      <div class="eyebrow" style="margin-bottom: 0.6rem;">The Artist</div>
      <p>Antónia Camilo de Távora (full name: Maria Antónia Camilo de Távora Vasconcelos da Silva) was born in Mozambique in 1960, of Portuguese origins. She attended two years at the Fine Arts School of Lisbon before moving to Switzerland, where she completed a Master’s degree in Biology at the University of Neuchâtel. Her professional path led her through biomedical research and secondary school teaching. In recent years she has dedicated herself to writing and painting, with exhibitions in Nassau, Lisbon and Zurich (2000–2024).</p>
      <blockquote class="artist-quote">
        <p>“Wherever I go, I am always struck by the beauty of the landscape. My background in plant physiology and biology naturally merges with my fascination for still lifes. In my mind, the scientific gaze and the artistic gaze intertwine, shaping the way I observe nature and translate it into painting.”</p>
      </blockquote>
    </div>
  </section>

  <section>
    <div class="section-title">
      <h2 class="serif">By Subject</h2>
    </div>
    <div class="cat-grid">
'''

for c in CATS:
    items = PAINTINGS[c["slug"]]
    cover = items[0]["asset_path"]
    cover_base, cover_ext = os.path.splitext(cover)
    home += f'''      <a class="cat-card" href="{c["slug"]}.html">
        <picture>
          <source type="image/webp" media="(max-width: 720px)" srcset="{cover_base}-thumb.webp">
          <source type="image/webp" srcset="{cover_base}.webp">
          <img src="{cover}" alt="Cover image for {c["label"]}" loading="lazy" decoding="async">
        </picture>
        <div class="cat-card__overlay">
          <div>
            <div class="cat-card__title">{c["label"]}</div>
            <div class="cat-card__count">{len(items)} {"piece" if len(items)==1 else "pieces"}</div>
          </div>
        </div>
      </a>
'''

home += '''    </div>
  </section>
</main>
'''

home += footer(depth=".") + lightbox() + footer_scripts()

with open(f"{OUT}/index.html", "w", encoding="utf-8") as f:
    f.write(home)
print(f"wrote index.html ({len(home)} bytes)")


# ---------- CATEGORY PAGES ----------

def make_category_page(slug):
    c = CAT_BY_SLUG[slug]
    items = PAINTINGS[slug]
    page = head(f"{c['label']} — Santhiago Collection",
                  c["blurb"],
                  canonical_path=f"{c['slug']}.html",
                  og_type="website",
                  jsonld=serialize_jsonld(jsonld_webpage(
                      f"{c['label']} — Santhiago Collection",
                      c["blurb"],
                      f"{c['slug']}.html"))) + \
        header(active=c["label"], depth="..") + f'''
<main role="main" id="main" tabindex="-1">
  <div class="page-intro">
    <div class="eyebrow">{c["label"]}</div>
    <h1 class="serif">{c["label"]}</h1>
    <p>{c["blurb"]}</p>
  </div>

  <div class="gallery">
'''
    for p in items:
        asset = p["asset_path"]
        asset_base, _ = os.path.splitext(asset)
        page += f'''    <a class="tile" href="paintings/{slug}/{p["slug"]}.html" data-lightbox="{asset}" data-lightbox-title="{html.escape(p["title"])}">
      <picture>
        <source type="image/webp" media="(max-width: 720px)" srcset="{asset_base}-thumb.webp">
        <source type="image/webp" srcset="{asset_base}.webp">
        <img src="{asset}" alt="{html.escape(p["title"])}" loading="lazy" decoding="async">
      </picture>
      <div class="tile__cap"><strong>{html.escape(p["title"])}</strong><em>{html.escape(fmt_dims(p["dimensions"]))} · {html.escape(p["medium"])}</em></div>
    </a>
'''
    page += '''  </div>
</main>
'''
    page += footer(depth="..") + lightbox() + footer_scripts()
    return page

for c in CATS:
    page = make_category_page(c["slug"])
    with open(f"{OUT}/{c['slug']}.html", "w", encoding="utf-8") as f:
        f.write(page)
    print(f"wrote {c['slug']}.html ({len(page)} bytes)")


# ---------- DETAIL PAGES ----------

def make_detail_page(slug, idx):
    items = PAINTINGS[slug]
    p = items[idx]
    prev_idx = (idx - 1) % len(items)
    next_idx = (idx + 1) % len(items)
    prev_p = items[prev_idx]
    next_p = items[next_idx]
    same_prev = (prev_p["slug"] == p["slug"])
    same_next = (next_p["slug"] == p["slug"])
    prev_disabled = ' class="disabled"' if same_prev else ''
    next_disabled = ' class="disabled"' if same_next else ''

    c = CAT_BY_SLUG[slug]
    medium_html = (
        f'<p class="detail__medium">{html.escape(p["medium"])} &middot; {html.escape(fmt_dims(p["dimensions"]))}</p>'
    )

    page = head(f"{p['title']} — Santhiago Collection",
                f"{p['title']} by Antónia Camilo de Távora. {p['medium']}, {fmt_dims(p['dimensions'])}.",
                canonical_path=f"paintings/{slug}/{p['slug']}.html",
                og_type="article",
                jsonld=serialize_jsonld(
                    jsonld_visual_artwork(p, slug),
                    jsonld_webpage(
                        f"{p['title']} — Santhiago Collection",
                        f"{p['title']} by Antónia Camilo de Távora. {p['medium']}, {fmt_dims(p['dimensions'])}.",
                        f"paintings/{slug}/{p['slug']}.html"))) + \
        header(active=c["label"], depth="../..") + f'''
<main role="main" id="main" tabindex="-1">
  <div class="detail">
    <div class="detail__img">
      <picture>
        <source type="image/webp" media="(max-width: 720px)" srcset="{os.path.splitext(p["asset_path"])[0]}-thumb.webp">
        <source type="image/webp" srcset="{os.path.splitext(p["asset_path"])[0]}.webp">
        <img src="{p["asset_path"]}" alt="{html.escape(p["title"])}" decoding="async">
      </picture>
    </div>
    <div class="detail__meta">
      <a class="detail__back" href="../../{slug}.html">← {c["label"]}</a>
      <div class="detail__cat">{c["label"]}</div>
      <h1 class="serif">{html.escape(p["title"])}</h1>
      {medium_html}
      <nav class="detail__nav">
        <a href="{prev_p["slug"]}.html"{prev_disabled}>← {html.escape(prev_p["title"])}</a>
        <a href="{next_p["slug"]}.html"{next_disabled}>{html.escape(next_p["title"])} →</a>
      </nav>
    </div>
  </div>
</main>
'''
    page += footer(depth="../..") + lightbox() + footer_scripts()
    return page

import os
count = 0
for c in CATS:
    cat_dir = f"{OUT}/paintings/{c['slug']}"
    os.makedirs(cat_dir, exist_ok=True)
    items = PAINTINGS[c["slug"]]
    for i, p in enumerate(items):
        page = make_detail_page(c["slug"], i)
        with open(f"{cat_dir}/{p['slug']}.html", "w", encoding="utf-8") as f:
            f.write(page)
        count += 1
print(f"wrote {count} detail pages")

# ---------- Sitemap & robots.txt ----------

def build_sitemap():
    """Generate a sitemap.xml covering every page on the site."""
    urls = [
        ("",         "1.0", "weekly"),  # home
        ("portraits.html",       "0.9", "monthly"),
        ("natures-mortes.html",   "0.9", "monthly"),
        ("paisagens.html",        "0.9", "monthly"),
    ]
    for c in CATS:
        urls.append((f"{c['slug']}.html", "0.9", "monthly"))
        for p in PAINTINGS[c["slug"]]:
            urls.append((f"paintings/{c['slug']}/{p['slug']}.html", "0.7", "yearly"))
    lastmod = "2026-09-02"
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, prio, freq in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{absolute_url(path)}</loc>")
        lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append(f"    <changefreq>{freq}</changefreq>")
        lines.append(f"    <priority>{prio}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def build_robots():
    """Generate robots.txt that allows all crawlers and points to sitemap."""
    return f"""User-agent: *
Allow: /

Sitemap: {absolute_url("sitemap.xml")}
"""


# Write sitemap.xml and robots.txt
with open(f"{OUT}/sitemap.xml", "w", encoding="utf-8") as f:
    f.write(build_sitemap())
print(f"wrote sitemap.xml ({len(build_sitemap())} bytes)")

with open(f"{OUT}/robots.txt", "w", encoding="utf-8") as f:
    f.write(build_robots())
print(f"wrote robots.txt")
