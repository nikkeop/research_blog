# Rebuild: from research blog to personal website

This file documents how the site was restructured in October 2026: from a research blog into a personal website with three sections (research, projects, and trips), plus the import of the old WordPress travel blog (niksradventures.wordpress.com). It covers what changed, why, and what is still left to do.

The theme is still Hugobricks v2 and its brick system is unchanged. Everything new is built from the theme's own parts: the same bricks, the same card grid, the same palette mechanism. Where something new was needed, it was added as a shortcode or partial in the theme's style.

---

## 1. Site structure

```
content/en/
├── _index.md                  Home: intro, the three sections as cards, latest posts
├── research/                  accent "ocean" (blue)
│   ├── _index.md              intro + all research posts with tag filter   (/research/, alias /blog/)
│   ├── thesis.md              brick page, not listed as a post            (/research/thesis/, alias /thesis/)
│   └── <post>.md              articles
├── projects/                  accent "forest" (green)
│   ├── _index.md              intro + all projects as cards
│   └── <project>.md           brick pages (showcase), from archetypes/projects.md
├── trips/                     accent "sunset" (orange)
│   ├── _index.md              hero image, trip cards, route map         (like the theme's paragliding demo)
│   ├── norway-2024/           imported: 32 posts + 2 drafts
│   │   └── _index.md          hero, posts day by day (oldest first), route map
│   ├── china-2025/            imported: 26 posts
│   │   └── _index.md          hero, posts day by day (oldest first)
│   └── short-trips/           empty for now: one post per short trip, newest first
├── about.md, contact.md, imprint.md, privacy-policy.md, 404.md   accent "slate" (site default)
└── bricks/
    ├── cta.md                 closes research posts (and any section without its own)
    └── cta-trips.md           closes trip posts (new)
```

**Menu** (`data/en/header.yaml`): Research ▾ (All posts, Master's thesis) · Projects · Trips ▾ (Norway 2024, China 2025, Short trips) · About · Contact. A new trip needs a line under `Trips → items`.

**Old URLs:** `/blog/` redirects to `/research/` and `/thesis/` redirects to `/research/thesis/` (Hugo `aliases`). The single post that existed was a draft, so no post URLs changed.

### How a page becomes an article or a brick page

- A section's `_index.md` **cascades** settings to everything below it:
  ```yaml
  cascade:
    - color_name: ocean          # the accent, for every page in the section
    - target: { kind: page }
      type: article              # every regular page renders as an article
  ```
- `type: article` makes Hugo use **`layouts/article/page.html`**, the former `layouts/posts/page.html`. It renders the post brick (title, date, tags, featured image, body), then **previous/next links**, then the section's call-to-action brick.
- A page that should be built from bricks instead sets `type: page` in its own front matter (the thesis does).
- Projects do *not* cascade `type: article`: a project is a showcase page made of bricks (hero, image bricks, facts, gallery), like the theme's demo pages.
- `build: { list: never }` keeps a page out of every list (the thesis is in `research/` but isn't a post).

---

## 2. Section colours

The theme already supported `color_name` (sets `data-color` on `<html>`, which swaps `--accent`). That mechanism is reused; only the palettes and their scope are new.

| Palette | Accent | Used by |
|---|---|---|
| `slate`  | `#455a64` | home, about, contact, legal pages (site default, `data/settings.yaml`) |
| `ocean`  | `#1e78c8` | research |
| `forest` | `#3d8b2f` | projects |
| `sunset` | `#e0640b` | trips |

The palettes are defined in `static/css/variables.css`. They are a shade deeper than the theme's own (`red`/`blue`/`green`/`yellow`, still available) so white button text stays legible. To change a colour, edit the hex values there. To give a section a different palette, change `color_name` in its `_index.md` (twice: on the page itself and in `cascade`).

Where the accent shows, so the sections stay recognisable with the same layout:

- a **4px band** along the top of the banner (new, `static/css/media.css`)
- each **top-level menu item underlines in its target section's colour** (the menu reads `color_name` from the linked page, `layouts/_partials/site/menu.html`)
- buttons, breadcrumbs, icons, and link focus rings (theme default)
- **cards carry their own page's palette.** The palette selectors are no longer limited to `:root`, so on the home page each "latest post" card is drawn in its section's colour and labelled with a section badge.

---

## 3. New and changed templates

### New

| File | What it does |
|---|---|
| `layouts/_partials/media.html` | Resolves an image reference: `/uploads/…` → local file, processed to webp as before; `trips/…` (no slash, no scheme) → **media bucket** key, prefixed with `params.media.base`, plus `.w800` thumbnail and `srcset`; `https://…` → passed through. |
| `layouts/_shortcodes/photo.html` | `{{< photo src="trips/…/x.jpg" caption="…" alt="…" >}}`: a figure with caption that opens in the lightbox. |
| `layouts/_shortcodes/photos.html` | `{{< photos [cols="2"] >}} …photo shortcodes… {{< /photos >}}`: a grid the lightbox pages through as one gallery. `cols="1"` stacks full-width photos. |
| `layouts/_shortcodes/routemap.html` | `{{< routemap src="https://www.google.com/maps/d/embed?mid=…" >}}`: Google My Maps, **click-to-load** (no Google request or cookie until the visitor clicks). Without JS the button links to the map on Google. |
| `layouts/_shortcodes/subsections.html` | Cards for the sections below the page (the trips on `/trips/`), with "Mar 2025 – Apr 2025 · 26 posts" counted from the posts. `paths="/a,/b"` picks pages explicitly (home page). `list_last: true` in a section's front matter sorts it last (Short trips). |
| `layouts/_partials/site/postnav.html` | Previous/next post links under every article, in date order within the same section (day 3 → day 4). |
| `static/css/media.css` | Styles for all of the above: accent band, menu underline, card badge, photos, route map, prev/next. |
| `archetypes/{research,trips,projects,default}.md` | Starting points for `hugo new content …`. The projects archetype is a full brick-page template (hero → problem → how it works → facts → gallery → CTA). |
| `content/en/bricks/cta-trips.md` | "More trips" call to action under every trip post. |

### Changed

| File | Change |
|---|---|
| `layouts/posts/page.html` → `layouts/article/page.html` | Picks `bricks/cta-<section>.md` before `bricks/cta.md`; adds prev/next. |
| `layouts/_shortcodes/blog.html` | Generalised: lists the posts below the current page by default, or `section="research,trips"`; new params `order`, `pagesize`, `limit`, `filter`, `dates`, `badges`; shows "Nothing here yet" when empty. |
| `layouts/_partials/teaser_list.html` | Images via `media.html` (lazy-loaded); `summary` front matter overrides the first-paragraph summary; `data-color` per card; optional section badge; date range and post count for section cards. |
| `layouts/_partials/sections/post.html` | Tag links go to the post's own section (`/research/?tag=…`) instead of `/blog/`; featured image via `media.html`; `content_language` → `lang` on title and article. |
| `layouts/_markup/render-image.html` | Goes through `media.html`, so Markdown images can use bucket keys too: `![](trips/import/…jpg){:.background}`. |
| `layouts/_partials/site/menu.html` | `data-color` per top-level item, taken from the linked section. |
| `layouts/_partials/site/styles.html` | Adds `css/media.css` to the bundle. |
| `static/css/variables.css` | Palettes no longer limited to `:root`; four new palettes. |
| `static/js/site.js` | Click-to-load for the route map. |
| `static/js/lightbox.js` | Keeps a link's existing `title` as the caption (previously overwritten with the link text, empty for photos); escapes captions before inserting them as HTML. |
| `hugo.yaml` | `params.media` (bucket base URL, thumbnails switch); routing rules sending `div.routemap` and `ul.photos` sections to the `wide` brick. |
| `data/settings.yaml` | `color_name: slate`; webmanifest name without "— Research". |
| `data/en/header.yaml`, `data/en/general.yaml` | New menu, subtitle "Research, projects & trips", site description. |
| `i18n/en.yaml`, `i18n/de.yaml` | Strings for prev/next, empty lists, route map notice, post counts. |
| `content/en/_index.md`, `about.md`, `research/*` | New home page; about text points to the three sections; links from `/blog/` → `/research/`. |
| `README.md` | Updated "Writing a post". |

### Using the bricks in practice (design ideas)

These patterns come from the theme's demo pages (hugobricks2.preview.usecue.com):

- **Hero with photo** (paragliding demo): `# Title`, a paragraph, a button and `![](key){:.background}` in the first section, with `transparent_header: true` in the front matter. Used on `/trips/` and each trip page. Good for a project page too.
- **Zig-zag image bricks** (hiking demo): sections of `## Heading`, text and `![](key){:.float}` alternate left/right with a tinted band automatically. The projects archetype uses them.
- **Facts list**: a section that is a list with `**bold**` labels becomes the `blocks` brick, which works well for "Status / Built with / Time" on projects or "Distance / Days / Elevation" on trips.
- **Quote**: a section starting with `> "…"` and an optional `{:.background}` image becomes a full-bleed quote, e.g. a favourite line from a trip.
- **Features** (`{{< features >}}` from `data/en/features.yaml`): could become "skills" on the about page or key numbers on `/trips/` (km cycled, countries, nights in the tent).

---

## 4. The WordPress import

### What was in the export (`~/Wordpress/`)

- `niklasontour.WordPress.2026-08-10.xml`: 60 posts (34 in category "Norway 2024", 26 in "China 2025"), 4 pages, 776 attachments, 14 comments.
- `media-export-233299362-from-0-to-1276.tar`: the 776 images (1 GB), as `YYYY/MM/file.jpg`.

### How it was imported

```sh
# 1. Web-sized copies of all images (max 2000 px + 800 px thumbnail, EXIF/GPS stripped)
python3 tools/media/optimize.py ~/Wordpress/media-export-233299362-from-0-to-1276.tar \
        ~/Wordpress/r2-upload --prefix trips/import

# 2. Posts → Markdown
python3 tools/wp-import/wp2hugo.py ~/Wordpress/niklasontour.WordPress.2026-08-10.xml content/en/trips
```

Both scripts are in the repository, so the import can be repeated. **Re-running `wp2hugo.py` overwrites the imported posts**, so edit them only once you're happy with the import.

How the importer maps WordPress to this site:

| WordPress | Here |
|---|---|
| category `norway-2024` / `china-2025` | folder `trips/norway-2024/` / `trips/china-2025/` (anything else would go to `short-trips/`) |
| post slug | file name (emoji and special characters removed, e.g. `tag-30-…-goodbye-schweden`) |
| publish date (GMT) | `date` |
| featured image | `image: trips/import/YYYY/MM/file.jpg` |
| private posts ("Day -3", "Day -2") | imported with `draft: true` (test posts, not published) |
| image block | `{{< photo >}}` with caption |
| gallery / Jetpack slideshow / tiled gallery | `{{< photos >}}` (keeps the column count when one was set) |
| table | Markdown table |
| `[googlemaps …]` | `{{< routemap >}}` (click-to-load) |
| links between old posts | rewritten to the new paths |
| comments, tags, contact forms, subscribe buttons | not imported |
| the original URL | kept as `wordpress_url` in the front matter, for reference |

Every imported post has `content_language: de`. The site and its menus stay English, but the title and body of the post are marked `lang="de"` for screen readers and search engines.

The trip overview pages (`trips/norway-2024/_index.md`, `trips/china-2025/_index.md`) were written by hand. Their German text comes from the old WordPress trip pages, and their card images are the featured images of those pages.

### Media: what to upload

`~/Wordpress/r2-upload/` (450 MB, 1,552 files) mirrors the bucket layout exactly:

```
trips/import/2024/06/img_6239-1.jpg        2000 px, for the lightbox and hero images
trips/import/2024/06/img_6239-1.w800.jpg    800 px, for cards and in-text photos
```

**Upload it to the bucket root now**, before publishing: until then, every imported photo is a broken image. All 760 images referenced by the posts were checked to exist in that folder. With [rclone](https://rclone.org/s3/#cloudflare-r2) set up for R2 (remote name `r2`, your bucket name in place of `BUCKET`):

```sh
rclone copy ~/Wordpress/r2-upload r2:BUCKET --progress \
       --header-upload "Cache-Control: public, max-age=31536000, immutable"
```

The original tar stays your full-resolution backup; it does not need to go into the bucket.

**For new photos** (any section): put them in a folder, run
`python3 tools/media/optimize.py <folder> <out> --prefix trips/<trip>` (or `research/<post>`, `projects/<project>`), upload `<out>` the same way, and use the keys in the content. Every image in the bucket should go through the script, because the site expects the `.w800` sibling. If you ever upload images without it, set `params.media.thumbnails: false` in `hugo.yaml`.

---

## 5. Moving from science.oppernik.de to oppernik.de

Little has to change:

1. `baseURL` in `hugo.yaml` → `https://oppernik.de`. (The GitHub Actions build overrides it with the Pages URL anyway.)
2. In the repository's GitHub Pages settings, set the custom domain to `oppernik.de` and update the DNS records.
3. On Cloudflare, add a redirect rule `science.oppernik.de/*` → `https://oppernik.de/${1}` (301) so old links keep working.

Nothing in the content uses the domain: internal links are root-relative, and media keys are resolved against `params.media.base`, which stays `site-media.oppernik.de`.

---

## 6. Still to do

- [ ] **Upload `~/Wordpress/r2-upload/` to R2** (see above).
- [ ] **Look at the site in a browser** (`hugo server -D`). I couldn't take screenshots here (no browser in this WSL environment), so the layout was checked only through the generated HTML and a clean build. Worth checking in particular: the accent band and menu underlines, the photo grids, the route map placeholder, and the hero pages with the transparent banner.
- [ ] Fill in the `TODO`s: home intro, projects intro, trips intro and route-map text, short-trips intro, the projects card summary on the home page.
- [ ] **Route map of all trips:** the map on `/trips/` is the Norway 2024 map from the old blog. In Google My Maps, create a map with one layer per trip (import the GPX/KML tracks), then replace the `mid=` in `content/en/trips/_index.md`. A China map could go on `trips/china-2025/_index.md` the same way.
- [ ] **Privacy policy:** it currently says the site uses no cookies and loads nothing from third parties. Two things are new: images are served from Cloudflare R2 (`site-media.oppernik.de`, which processes visitors' IP addresses), and the route map loads Google Maps *after the visitor clicks*. Both should be mentioned.
- [ ] Optional: a notice on the old WordPress blog pointing to `oppernik.de/trips/` (wordpress.com only redirects whole sites with a paid upgrade).
- [ ] Optional: replace the SVG illustrations on the research/projects cards and intros with your own photos.
- [ ] Delete the two imported test drafts (`trips/norway-2024/day-2-…`, `day-3-…`) if you don't want them.
