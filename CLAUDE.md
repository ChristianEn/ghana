# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ghana Travel Slideshow Generator — a Python script that reads media files (JPG/MOV) from the current directory, extracts dates, sorts chronologically, assigns to chapters, and outputs a single self-contained bilingual (EN/DE) HTML slideshow.

## Commands

```bash
# Generate the slideshow
python3 generate_slideshow.py

# View in Safari
open -a Safari slideshow.html

# Alternative: local server (needed if browser blocks local file access for videos)
python3 -m http.server 8000
```

**Dependency**: Pillow (`pip3 install Pillow`). macOS-only due to `mdls` usage for MOV metadata.

## Architecture

**Single generator script** (`generate_slideshow.py`) → **Single output file** (`slideshow.html`)

### Data flow
1. `collect_media_files()` — finds all .jpg/.jpeg/.mov, filters `EXCLUDED_IMAGES`
2. `get_media_date()` — date extraction chain: EXIF (JPG) → `mdls` (MOV) → file birthtime
3. `assign_chapters()` — maps files to 4 chapters using `CHAPTER_BOUNDARIES` dict (start-of-day comparison)
4. `generate_html()` — builds slides list, renders HTML with embedded CSS+JS

### Key configuration (top of file)
- `CHAPTER_BOUNDARIES` — image prefix → chapter start (uses start-of-day of that image's date)
- `CHAPTER_NAMES` — chapter display names
- `EXCLUDED_IMAGES` — image stems to skip

### Slide types in generation order
`lang-select` → `title` → for each chapter: `chapter` + media slides + `content` → `end`

### Bilingual system
- CSS classes `.lang-en` / `.lang-de` on `<div>` and `<span>` elements
- Body class `show-en` or `show-de` toggles visibility
- All text slides (title, chapter, content, end, TOC) have both language variants
- Language chosen on slide 0 (lang-select), stored in JS `lang` variable

### Generated HTML structure
- All CSS and JS inline (no external files)
- Lazy loading: images beyond slide 2 use `data-src`, loaded when within 2 slides
- Videos: auto-play muted on entry, pause on exit, nav overlays on left/right edges
- Navigation: arrow keys, click zones (30%/70%), progress bar seek, TOC overlay (`t` key), fullscreen (`f` key)
- Slide 0 (lang-select) is navigation-locked — must click a button to proceed
