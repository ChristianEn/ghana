#!/usr/bin/env python3
"""
Ghana Travel Slideshow Generator
Reads media files, extracts EXIF dates, sorts chronologically,
assigns chapters, and generates a single-file HTML slideshow.
"""

import os
import subprocess
import glob
import re
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS

MEDIA_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(MEDIA_DIR, "slideshow.html")

# Images to exclude from the slideshow
EXCLUDED_IMAGES = {"IMG_4003"}

# Chapter boundary images (chapter starts at this image's date)
CHAPTER_BOUNDARIES = {
    2: "IMG_2730",
    3: "IMG_2893",
    4: "IMG_3129",
}

CHAPTER_NAMES = {
    1: "Accra",
    2: "Elmina",
    3: "Cape Three Points",
    4: "Cape Coast / Return Journey",
}


def get_exif_date_jpg(filepath):
    """Extract DateTimeOriginal from EXIF data of JPG/JPEG files."""
    try:
        img = Image.open(filepath)
        exif_data = img._getexif()
        if exif_data:
            # Tag 36867 = DateTimeOriginal
            date_str = exif_data.get(36867)
            if date_str:
                return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
    except Exception as e:
        print(f"  EXIF error for {os.path.basename(filepath)}: {e}")
    return None


def get_date_mov(filepath):
    """Extract content creation date from MOV using macOS mdls."""
    try:
        result = subprocess.run(
            ["mdls", "-name", "kMDItemContentCreationDate", filepath],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout.strip()
        # Format: kMDItemContentCreationDate = 2026-03-01 12:34:56 +0000
        match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", output)
        if match:
            return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"  mdls error for {os.path.basename(filepath)}: {e}")
    return None


def get_birthtime(filepath):
    """Fallback: use file creation time (macOS st_birthtime)."""
    try:
        stat = os.stat(filepath)
        return datetime.fromtimestamp(stat.st_birthtime)
    except Exception:
        return datetime.fromtimestamp(os.path.getmtime(filepath))


def get_media_date(filepath):
    """Get the best available date for a media file."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in (".jpg", ".jpeg"):
        date = get_exif_date_jpg(filepath)
        if date:
            return date
    elif ext == ".mov":
        date = get_date_mov(filepath)
        if date:
            return date
    # Fallback
    return get_birthtime(filepath)


def collect_media_files():
    """Find all media files in the directory."""
    extensions = (".jpg", ".jpeg", ".mov")
    files = []
    for f in os.listdir(MEDIA_DIR):
        if os.path.splitext(f)[1].lower() in extensions:
            stem = os.path.splitext(f)[0]
            if stem not in EXCLUDED_IMAGES:
                files.append(f)
    return files


def assign_chapters(sorted_media, boundary_dates):
    """Assign each media item to a chapter based on its date."""
    chapters = {1: [], 2: [], 3: [], 4: []}
    for filename, date in sorted_media:
        if date >= boundary_dates[4]:
            chapters[4].append((filename, date))
        elif date >= boundary_dates[3]:
            chapters[3].append((filename, date))
        elif date >= boundary_dates[2]:
            chapters[2].append((filename, date))
        else:
            chapters[1].append((filename, date))
    return chapters


def is_video(filename):
    return os.path.splitext(filename)[1].lower() == ".mov"


def get_mov_rotation(filepath):
    """Read rotation from MOV track header matrix (tkhd atom)."""
    import struct, math
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        pos = 0
        while pos < len(data) - 8:
            idx = data.find(b'tkhd', pos)
            if idx == -1:
                break
            version = data[idx + 4]
            if version == 0:
                matrix_offset = idx + 4 + 1 + 3 + 4 + 4 + 4 + 4 + 4 + 8 + 2 + 2 + 2 + 2
            else:
                matrix_offset = idx + 4 + 1 + 3 + 8 + 8 + 4 + 4 + 8 + 8 + 2 + 2 + 2 + 2
            a = struct.unpack('>i', data[matrix_offset:matrix_offset + 4])[0] / 65536.0
            b = struct.unpack('>i', data[matrix_offset + 4:matrix_offset + 8])[0] / 65536.0
            rotation = round(math.degrees(math.atan2(b, a)))
            if rotation != 0:
                return rotation
            pos = idx + 4
    except Exception as e:
        print(f"  Rotation detection error for {os.path.basename(filepath)}: {e}")
    return 0


def generate_html(chapters):
    """Generate the complete HTML slideshow."""

    # Build slides list
    slides = []

    # --- Language selection slide (slide 0) ---
    slides.append({"type": "lang-select"})

    # --- Title slide ---
    slides.append({"type": "title"})

    # --- Chapter 1: Accra ---
    slides.append({"type": "chapter", "chapter": 1, "name": CHAPTER_NAMES[1]})
    for filename, date in chapters[1]:
        if is_video(filename):
            rotation = get_mov_rotation(os.path.join(MEDIA_DIR, filename))
            slides.append({"type": "video", "src": filename, "date": date, "rotation": rotation})
        else:
            slides.append({"type": "image", "src": filename, "date": date})

    # --- Content: Ghana at a Glance ---
    slides.append({"type": "content", "id": "ghana-glance"})

    # --- Content: Life in Ghana ---
    slides.append({"type": "content", "id": "life-ghana"})

    # --- Chapter 2: Elmina ---
    slides.append({"type": "chapter", "chapter": 2, "name": CHAPTER_NAMES[2]})
    for filename, date in chapters[2]:
        if is_video(filename):
            rotation = get_mov_rotation(os.path.join(MEDIA_DIR, filename))
            slides.append({"type": "video", "src": filename, "date": date, "rotation": rotation})
        else:
            slides.append({"type": "image", "src": filename, "date": date})

    # --- Content: The Slave Forts ---
    slides.append({"type": "content", "id": "slave-forts"})

    # --- Chapter 3: Cape Three Points ---
    slides.append({"type": "chapter", "chapter": 3, "name": CHAPTER_NAMES[3]})
    for filename, date in chapters[3]:
        if is_video(filename):
            rotation = get_mov_rotation(os.path.join(MEDIA_DIR, filename))
            slides.append({"type": "video", "src": filename, "date": date, "rotation": rotation})
        else:
            slides.append({"type": "image", "src": filename, "date": date})

    # --- Content: Volunteering in Ghana ---
    slides.append({"type": "content", "id": "volunteering"})

    # --- Chapter 4: Cape Coast / Return ---
    slides.append({"type": "chapter", "chapter": 4, "name": CHAPTER_NAMES[4]})
    for filename, date in chapters[4]:
        if is_video(filename):
            rotation = get_mov_rotation(os.path.join(MEDIA_DIR, filename))
            slides.append({"type": "video", "src": filename, "date": date, "rotation": rotation})
        else:
            slides.append({"type": "image", "src": filename, "date": date})

    # --- End slide ---
    slides.append({"type": "end"})

    # Track chapter start indices and content slide indices for TOC and progress bar
    chapter_indices = {}
    content_indices = {}
    title_index = 0
    for i, s in enumerate(slides):
        if s["type"] == "chapter":
            chapter_indices[s["chapter"]] = i
        elif s["type"] == "content":
            content_indices[s["id"]] = i
        elif s["type"] == "title":
            title_index = i

    total_slides = len(slides)
    print(f"\nTotal slides: {total_slides}")
    for ch in range(1, 5):
        count = len(chapters[ch])
        print(f"  Chapter {ch} ({CHAPTER_NAMES[ch]}): {count} media files")

    # Chapter name translations
    chapter_names_de = {
        1: "Accra",
        2: "Elmina",
        3: "Cape Three Points",
        4: "Cape Coast / Rückreise",
    }

    # --- Build HTML slide elements ---
    slide_html_parts = []
    for i, s in enumerate(slides):
        lazy = 'loading="lazy"' if i > 2 else 'loading="eager"'
        if s["type"] == "lang-select":
            slide_html_parts.append(f'''
    <div class="slide slide-lang-select active" data-index="{i}">
      <div class="lang-select-content">
        <div class="ghana-flag">
          <div class="flag-stripe flag-red"></div>
          <div class="flag-stripe flag-gold">
            <div class="flag-star">&#9733;</div>
          </div>
          <div class="flag-stripe flag-green"></div>
        </div>
        <h2>Choose your language</h2>
        <p class="lang-select-sub">Sprache wählen</p>
        <div class="lang-buttons">
          <button class="lang-btn" data-lang="en">English</button>
          <button class="lang-btn" data-lang="de">Deutsch</button>
        </div>
        <p class="nav-hint">Navigate with &#8592; &#8594; arrow keys</p>
        <p class="nav-hint">Navigation mit den Pfeiltasten &#8592; &#8594;</p>
      </div>
    </div>''')

        elif s["type"] == "title":
            slide_html_parts.append(f'''
    <div class="slide slide-title" data-index="{i}">
      <div class="title-content">
        <div class="ghana-flag">
          <div class="flag-stripe flag-red"></div>
          <div class="flag-stripe flag-gold">
            <div class="flag-star">&#9733;</div>
          </div>
          <div class="flag-stripe flag-green"></div>
        </div>
        <div class="lang-en">
          <h1>Along the West African Gold Coast</h1>
          <p class="subtitle-de">Entlang der westafrikanischen Goldküste</p>
          <p class="dates">27 February – 13 March 2026</p>
        </div>
        <div class="lang-de">
          <h1>Entlang der westafrikanischen Goldküste</h1>
          <p class="subtitle-de">Along the West African Gold Coast</p>
          <p class="dates">27. Februar – 13. März 2026</p>
        </div>
      </div>
    </div>''')

        elif s["type"] == "chapter":
            ch_num = s['chapter']
            ch_name_de = chapter_names_de[ch_num]
            slide_html_parts.append(f'''
    <div class="slide slide-chapter" data-index="{i}" data-chapter="{ch_num}">
      <div class="chapter-content">
        <div class="lang-en">
          <span class="chapter-label">Chapter {ch_num}</span>
          <h2>{s['name']}</h2>
        </div>
        <div class="lang-de">
          <span class="chapter-label">Kapitel {ch_num}</span>
          <h2>{ch_name_de}</h2>
        </div>
      </div>
    </div>''')

        elif s["type"] == "image":
            src_attr = f'src="{s["src"]}"' if i <= 2 else f'src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" data-src="{s["src"]}"'
            slide_html_parts.append(f'''
    <div class="slide slide-media" data-index="{i}">
      <img {src_attr} alt="" {lazy} draggable="false">
    </div>''')

        elif s["type"] == "video":
            rot_attr = f' data-rotation="{s["rotation"]}"' if s.get("rotation") else ''
            slide_html_parts.append(f'''
    <div class="slide slide-media slide-video" data-index="{i}">
      <video preload="none" controls playsinline{rot_attr}>
        <source src="{s['src']}">
      </video>
      <div class="video-nav video-nav-prev" data-dir="prev">&#9664;</div>
      <div class="video-nav video-nav-next" data-dir="next">&#9654;</div>
    </div>''')

        elif s["type"] == "content" and s["id"] == "ghana-glance":
            slide_html_parts.append(f'''
    <div class="slide slide-content" data-index="{i}">
      <div class="content-card">
        <div class="lang-en">
        <h2>Ghana at a Glance</h2>
        <div class="fact-grid">
          <div class="fact">
            <div class="fact-value">34M</div>
            <div class="fact-label">Population</div>
          </div>
          <div class="fact">
            <div class="fact-value">$2,350</div>
            <div class="fact-label">GDP per Capita</div>
          </div>
          <div class="fact">
            <div class="fact-value">~23%</div>
            <div class="fact-label">Inflation Rate</div>
          </div>
          <div class="fact">
            <div class="fact-value">87%</div>
            <div class="fact-label">Electricity Access</div>
          </div>
          <div class="fact">
            <div class="fact-value">40%</div>
            <div class="fact-label">Clean Water Access (rural)</div>
          </div>
          <div class="fact">
            <div class="fact-value">2022</div>
            <div class="fact-label">Sovereign Debt Restructuring</div>
          </div>
        </div>
        <p class="content-note">Ghana's economy has been under severe strain since 2022, when the country defaulted on most of its external debt. An IMF programme and debt restructuring are ongoing. Inflation peaked above 50% in late 2022 and remains elevated.</p>
        </div>
        <div class="lang-de">
        <h2>Ghana auf einen Blick</h2>
        <div class="fact-grid">
          <div class="fact">
            <div class="fact-value">34 Mio.</div>
            <div class="fact-label">Bevölkerung</div>
          </div>
          <div class="fact">
            <div class="fact-value">$2.350</div>
            <div class="fact-label">BIP pro Kopf</div>
          </div>
          <div class="fact">
            <div class="fact-value">~23%</div>
            <div class="fact-label">Inflationsrate</div>
          </div>
          <div class="fact">
            <div class="fact-value">87%</div>
            <div class="fact-label">Stromversorgung</div>
          </div>
          <div class="fact">
            <div class="fact-value">40%</div>
            <div class="fact-label">Trinkwasser (ländlich)</div>
          </div>
          <div class="fact">
            <div class="fact-value">2022</div>
            <div class="fact-label">Schuldenrestrukturierung</div>
          </div>
        </div>
        <p class="content-note">Ghanas Wirtschaft steht seit 2022 unter schwerem Druck, als das Land den Großteil seiner Auslandsschulden nicht mehr bedienen konnte. Ein IWF-Programm und die Umschuldung laufen. Die Inflation erreichte Ende 2022 über 50% und bleibt hoch.</p>
        </div>
      </div>
    </div>''')

        elif s["type"] == "content" and s["id"] == "life-ghana":
            slide_html_parts.append(f'''
    <div class="slide slide-content" data-index="{i}">
      <div class="content-card">
        <div class="lang-en">
        <h2>Life in Ghana</h2>
        <div class="info-grid">
          <div class="info-card">
            <div class="info-icon">&#127793;</div>
            <div class="info-title">Nutrition & Development</div>
            <div class="info-text">Chronic malnutrition and limited access to quality education have measurable effects on cognitive development, particularly in rural areas.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#127858;</div>
            <div class="info-title">Food Culture</div>
            <div class="info-text">Meals are built around starches (fufu, banku, rice) with stews. The emphasis is on caloric sustenance over variety. Western-style restaurants are rare outside Accra.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#127962;</div>
            <div class="info-title">Service & Tourism</div>
            <div class="info-text">There is no established hospitality culture. Tourist-facing services can feel improvised, and accommodation prices often approach European levels without matching the quality.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#9889;</div>
            <div class="info-title">Infrastructure</div>
            <div class="info-text">Roads deteriorate quickly outside cities. Power outages (&ldquo;dumsor&rdquo;) and unreliable water supply are everyday realities.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#9878;&#65039;</div>
            <div class="info-title">Corruption</div>
            <div class="info-text">Pervasive and systemic: from roadside police stops to government procurement. Widely acknowledged by Ghanaians themselves.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#128499;&#65039;</div>
            <div class="info-title">Democracy</div>
            <div class="info-text">A genuine bright spot. Ghana has had peaceful transfers of power since 1992, a free press, and an engaged electorate. The 2024 election saw a smooth opposition victory.</div>
          </div>
        </div>
        </div>
        <div class="lang-de">
        <h2>Leben in Ghana</h2>
        <div class="info-grid">
          <div class="info-card">
            <div class="info-icon">&#127793;</div>
            <div class="info-title">Ernährung & Entwicklung</div>
            <div class="info-text">Chronische Unterernährung und eingeschränkter Zugang zu guter Bildung wirken sich messbar auf die kognitive Entwicklung aus, besonders in ländlichen Gebieten.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#127858;</div>
            <div class="info-title">Esskultur</div>
            <div class="info-text">Mahlzeiten basieren auf Stärkebeilagen (Fufu, Banku, Reis) mit Eintöpfen. Der Fokus liegt auf Sättigung, nicht auf Vielfalt. Restaurants westlichen Stils sind außerhalb Accras selten.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#127962;</div>
            <div class="info-title">Service & Tourismus</div>
            <div class="info-text">Es gibt keine gewachsene Gastgeberkultur. Touristische Angebote wirken oft improvisiert, und die Unterkunftspreise erreichen europäisches Niveau, ohne die Qualität zu bieten.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#9889;</div>
            <div class="info-title">Infrastruktur</div>
            <div class="info-text">Straßen verschlechtern sich schnell außerhalb der Städte. Stromausfälle (&bdquo;Dumsor&ldquo;) und unzuverlässige Wasserversorgung gehören zum Alltag.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#9878;&#65039;</div>
            <div class="info-title">Korruption</div>
            <div class="info-text">Allgegenwärtig und systemisch: von Polizeikontrollen am Straßenrand bis zur Auftragsvergabe der Regierung. Wird von den Ghanaern selbst offen eingeräumt.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#128499;&#65039;</div>
            <div class="info-title">Demokratie</div>
            <div class="info-text">Ein echter Lichtblick. Ghana hat seit 1992 friedliche Machtwechsel erlebt, eine freie Presse und eine engagierte Wählerschaft. Die Wahl 2024 brachte einen reibungslosen Oppositionssieg.</div>
          </div>
        </div>
        </div>
      </div>
    </div>''')

        elif s["type"] == "content" and s["id"] == "slave-forts":
            slide_html_parts.append(f'''
    <div class="slide slide-content" data-index="{i}">
      <div class="content-card">
        <div class="lang-en">
        <h2>The Slave Forts</h2>
        <div class="info-grid">
          <div class="info-card">
            <div class="info-icon">&#9875;</div>
            <div class="info-title">Scale</div>
            <div class="info-text">An estimated 12.5 million Africans were shipped across the Atlantic over roughly 400 years. Millions more died in capture and transit.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#127984;</div>
            <div class="info-title">Elmina Castle</div>
            <div class="info-text">Built by the Portuguese in 1482, it is the oldest European structure in sub-Saharan Africa. Later seized by the Dutch and used as a major slave-trading hub.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#128274;</div>
            <div class="info-title">Cape Coast Castle</div>
            <div class="info-text">The British headquarters of the Gold Coast slave trade. Its underground dungeons held up to 1,000 captives at a time in total darkness.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#9876;&#65039;</div>
            <div class="info-title">The Garrisons</div>
            <div class="info-text">Remarkably small European garrisons &mdash; often fewer than 100 men &mdash; controlled these massive operations, relying heavily on local intermediaries.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#129309;</div>
            <div class="info-title">African Collaboration</div>
            <div class="info-text">Powerful states like the Ashanti Empire and Fante chiefs actively supplied war captives and kidnapped people to European traders. The trade reshaped regional power dynamics.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#128337;</div>
            <div class="info-title">Legacy</div>
            <div class="info-text">Centuries of depopulation, broken family and social structures, and economic extraction left lasting damage across West Africa that continues to shape the region today.</div>
          </div>
        </div>
        </div>
        <div class="lang-de">
        <h2>Die Sklavenfestungen</h2>
        <div class="info-grid">
          <div class="info-card">
            <div class="info-icon">&#9875;</div>
            <div class="info-title">Ausma&szlig;</div>
            <div class="info-text">Sch&auml;tzungsweise 12,5 Millionen Afrikaner wurden &uuml;ber rund 400 Jahre &uuml;ber den Atlantik verschleppt. Millionen weitere starben bei Gefangennahme und Transport.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#127984;</div>
            <div class="info-title">Elmina Castle</div>
            <div class="info-text">1482 von den Portugiesen erbaut, ist es das &auml;lteste europ&auml;ische Bauwerk in Subsahara-Afrika. Sp&auml;ter von den Niederl&auml;ndern &uuml;bernommen und als bedeutendes Zentrum des Sklavenhandels genutzt.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#128274;</div>
            <div class="info-title">Cape Coast Castle</div>
            <div class="info-text">Das britische Hauptquartier des Sklavenhandels an der Goldk&uuml;ste. In seinen unterirdischen Kerkern wurden bis zu 1.000 Gefangene gleichzeitig in v&ouml;lliger Dunkelheit festgehalten.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#9876;&#65039;</div>
            <div class="info-title">Die Garnisonen</div>
            <div class="info-text">Bemerkenswert kleine europ&auml;ische Garnisonen &mdash; oft weniger als 100 Mann &mdash; kontrollierten diese massiven Operationen und st&uuml;tzten sich stark auf einheimische Mittelsm&auml;nner.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#129309;</div>
            <div class="info-title">Afrikanische Beteiligung</div>
            <div class="info-text">M&auml;chtige Staaten wie das Ashanti-Reich und Fante-H&auml;uptlinge lieferten aktiv Kriegsgefangene und entf&uuml;hrte Menschen an europ&auml;ische H&auml;ndler. Der Handel ver&auml;nderte die regionalen Machtverh&auml;ltnisse grundlegend.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#128337;</div>
            <div class="info-title">Verm&auml;chtnis</div>
            <div class="info-text">Jahrhunderte der Entv&ouml;lkerung, zerst&ouml;rte Familien- und Sozialstrukturen sowie wirtschaftliche Ausbeutung hinterlie&szlig;en bleibende Sch&auml;den in Westafrika, die die Region bis heute pr&auml;gen.</div>
          </div>
        </div>
        </div>
      </div>
    </div>''')

        elif s["type"] == "content" and s["id"] == "volunteering":
            slide_html_parts.append(f'''
    <div class="slide slide-content" data-index="{i}">
      <div class="content-card">
        <div class="lang-en">
        <h2>Volunteering in Ghana</h2>
        <div class="info-grid">
          <div class="info-card">
            <div class="info-icon">&#128176;</div>
            <div class="info-title">The Model</div>
            <div class="info-text">&ldquo;Voluntourism&rdquo; is big business: participants pay NGOs or agencies for a placement, covering their own costs plus a fee. The NGO places them in schools, orphanages, or community projects.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#10067;</div>
            <div class="info-title">Questionable Impact</div>
            <div class="info-text">Many placements provide unskilled labour that displaces local workers. Short stays (1&ndash;4 weeks) rarely produce lasting benefit. Some orphanages have been found to recruit children specifically to attract volunteers and donations.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#11088;</div>
            <div class="info-title">The Case for Meritocracy</div>
            <div class="info-text">The most powerful long-term contribution may not be hands-on work, but demonstrating meritocratic principles: the idea that effort, talent, and integrity should determine outcomes &mdash; not family connections, bribes, or tribal affiliations.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#128279;</div>
            <div class="info-title">Structural Dependency</div>
            <div class="info-text">A steady flow of well-meaning foreigners can inadvertently reinforce dependency rather than building local capacity. The best programmes focus on training local people to lead.</div>
          </div>
        </div>
        </div>
        <div class="lang-de">
        <h2>Freiwilligenarbeit in Ghana</h2>
        <div class="info-grid">
          <div class="info-card">
            <div class="info-icon">&#128176;</div>
            <div class="info-title">Das Modell</div>
            <div class="info-text">&bdquo;Voluntourismus&ldquo; ist ein gro&szlig;es Gesch&auml;ft: Teilnehmer zahlen NGOs oder Agenturen f&uuml;r einen Einsatzplatz und tragen ihre eigenen Kosten plus eine Geb&uuml;hr. Die NGO vermittelt sie an Schulen, Waisenh&auml;user oder Gemeindeprojekte.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#10067;</div>
            <div class="info-title">Fraglicher Nutzen</div>
            <div class="info-text">Viele Eins&auml;tze bieten ungelernte Arbeit, die lokale Arbeitskr&auml;fte verdr&auml;ngt. Kurze Aufenthalte (1&ndash;4 Wochen) bringen selten nachhaltigen Nutzen. Manche Waisenh&auml;user werben gezielt Kinder an, um Freiwillige und Spenden anzuziehen.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#11088;</div>
            <div class="info-title">Leistungsprinzip</div>
            <div class="info-text">Der wirkungsvollste langfristige Beitrag ist m&ouml;glicherweise nicht die praktische Arbeit, sondern das Vorleben meritokratischer Prinzipien: dass Leistung, Talent und Integrit&auml;t &uuml;ber Ergebnisse entscheiden sollten &mdash; nicht Beziehungen, Bestechung oder Stammeszugeh&ouml;rigkeit.</div>
          </div>
          <div class="info-card">
            <div class="info-icon">&#128279;</div>
            <div class="info-title">Strukturelle Abh&auml;ngigkeit</div>
            <div class="info-text">Ein stetiger Strom gutmeinender Ausl&auml;nder kann unbeabsichtigt Abh&auml;ngigkeit verst&auml;rken, statt lokale Kapazit&auml;ten aufzubauen. Die besten Programme setzen darauf, Einheimische zu F&uuml;hrungskr&auml;ften auszubilden.</div>
          </div>
        </div>
        </div>
      </div>
    </div>''')

        elif s["type"] == "end":
            slide_html_parts.append(f'''
    <div class="slide slide-end" data-index="{i}">
      <div class="end-content">
        <div class="ghana-flag flag-small">
          <div class="flag-stripe flag-red"></div>
          <div class="flag-stripe flag-gold">
            <div class="flag-star">&#9733;</div>
          </div>
          <div class="flag-stripe flag-green"></div>
        </div>
        <h2>Medaase</h2>
        <div class="lang-en">
          <p class="end-subtitle">Thank you — Danke</p>
          <p class="end-meta">Ghana, February–March 2026</p>
        </div>
        <div class="lang-de">
          <p class="end-subtitle">Danke — Thank you</p>
          <p class="end-meta">Ghana, Februar–März 2026</p>
        </div>
      </div>
    </div>''')

    slides_html = "\n".join(slide_html_parts)

    # Content slide labels (EN/DE)
    content_labels = {
        "ghana-glance": ("Ghana at a Glance", "Ghana auf einen Blick"),
        "life-ghana": ("Life in Ghana", "Leben in Ghana"),
        "slave-forts": ("The Slave Forts", "Die Sklavenfestungen"),
        "volunteering": ("Volunteering in Ghana", "Freiwilligenarbeit in Ghana"),
    }

    # TOC entries
    toc_entries = []
    toc_entries.append(f'<div class="toc-entry" data-goto="{title_index}"><span class="lang-en">Title</span><span class="lang-de">Titel</span></div>')

    for ch in range(1, 5):
        idx = chapter_indices.get(ch, 0)
        toc_entries.append(f'<div class="toc-entry" data-goto="{idx}"><span class="lang-en">Chapter {ch}: {CHAPTER_NAMES[ch]}</span><span class="lang-de">Kapitel {ch}: {chapter_names_de[ch]}</span></div>')

    # Add content slide entries to TOC
    for cid in ["ghana-glance", "life-ghana", "slave-forts", "volunteering"]:
        if cid in content_indices:
            en_label, de_label = content_labels[cid]
            idx = content_indices[cid]
            toc_entries.append(f'<div class="toc-entry toc-content-entry" data-goto="{idx}"><span class="lang-en">{en_label}</span><span class="lang-de">{de_label}</span></div>')

    toc_entries.append(f'<div class="toc-entry" data-goto="{total_slides - 1}"><span class="lang-en">End</span><span class="lang-de">Ende</span></div>')
    toc_html = "\n        ".join(toc_entries)

    # Chapter marker positions for progress bar (as percentages)
    chapter_markers_js = "["
    for ch in sorted(chapter_indices.keys()):
        pct = (chapter_indices[ch] / (total_slides - 1)) * 100
        chapter_markers_js += f'{{"chapter":{ch},"pct":{pct:.1f},"name":"{CHAPTER_NAMES[ch]}"}},'
    chapter_markers_js += "]"

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ghana — Along the West African Gold Coast</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 100%; height: 100%; overflow: hidden; background: #000; color: #fff;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased; cursor: none; }}

/* --- Slides --- */
.slide {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  display: none; align-items: center; justify-content: center; }}
.slide.active {{ display: flex; }}

/* Media slides */
.slide-media img, .slide-media video {{
  width: 100%; height: 100%; object-fit: contain; background: #000; display: block; }}

/* Video navigation overlays */
.video-nav {{ position: absolute; top: 0; width: 12%; height: 100%; display: flex;
  align-items: center; justify-content: center; cursor: pointer; z-index: 10;
  font-size: 3vw; color: rgba(255,255,255,0); transition: color 0.2s; }}
.video-nav:hover {{ color: rgba(255,255,255,0.7); }}
.video-nav-prev {{ left: 0; }}
.video-nav-next {{ right: 0; }}

/* Title slide */
.slide-title {{ background: #000; }}
.title-content {{ text-align: center; }}
.ghana-flag {{ width: 20vw; height: 13.3vw; margin: 0 auto 3vh; position: relative;
  border-radius: 0.4vw; overflow: hidden; box-shadow: 0 0.5vw 2vw rgba(0,0,0,0.5); }}
.flag-small {{ width: 12vw; height: 8vw; margin: 0 auto 2vh; }}
.flag-stripe {{ width: 100%; height: 33.333%; }}
.flag-red {{ background: #CE1126; }}
.flag-gold {{ background: #FCD116; position: relative; }}
.flag-green {{ background: #006B3F; }}
.flag-star {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  font-size: 4.5vw; color: #000; line-height: 1; }}
.flag-small .flag-star {{ font-size: 2.7vw; }}
.title-content h1 {{ font-size: 4.5vw; font-weight: 700; letter-spacing: -0.05vw;
  margin-bottom: 1vh; line-height: 1.1; }}
.subtitle-de {{ font-size: 2vw; font-style: italic; color: #ccc; margin-bottom: 3vh; }}
.dates {{ font-size: 1.8vw; color: #FCD116; font-weight: 500; }}

/* Chapter title slides */
.slide-chapter {{ background: linear-gradient(135deg, #006B3F 0%, #004d2e 100%); }}
.chapter-content {{ text-align: center; }}
.chapter-label {{ font-size: 1.5vw; text-transform: uppercase; letter-spacing: 0.5vw;
  color: #FCD116; display: block; margin-bottom: 1.5vh; }}
.chapter-content h2 {{ font-size: 6vw; font-weight: 700; line-height: 1.1; }}

/* Content slides */
.slide-content {{ background: #111; padding: 4vh 5vw; }}
.content-card {{ max-width: 85vw; width: 100%; }}
.content-card h2 {{ font-size: 3.5vw; font-weight: 700; margin-bottom: 3vh;
  color: #FCD116; border-bottom: 0.15vw solid #333; padding-bottom: 1.5vh; }}
.fact-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 2.5vw; margin-bottom: 3vh; }}
.fact {{ background: #1a1a1a; border-radius: 0.8vw; padding: 2.5vh 1.5vw; text-align: center;
  border: 1px solid #333; }}
.fact-value {{ font-size: 3.5vw; font-weight: 700; color: #FCD116; margin-bottom: 0.5vh; }}
.fact-label {{ font-size: 1.3vw; color: #aaa; }}
.content-note {{ font-size: 1.4vw; color: #999; line-height: 1.6; margin-top: 1vh; }}
.content-list {{ list-style: none; padding: 0; }}
.content-list li {{ font-size: 1.6vw; line-height: 1.5; margin-bottom: 2vh;
  padding-left: 2vw; position: relative; color: #ddd; }}
.content-list li::before {{ content: ""; position: absolute; left: 0; top: 0.6vw;
  width: 0.6vw; height: 0.6vw; background: #FCD116; border-radius: 50%; }}
.content-list li strong {{ color: #fff; }}

/* Info card grid */
.info-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.8vw; }}
.info-card {{ background: #1a1a1a; border-radius: 0.8vw; padding: 2vh 1.5vw;
  border: 1px solid #333; border-left: 3px solid #FCD116; }}
.info-icon {{ font-size: 2.2vw; margin-bottom: 0.8vh; line-height: 1; }}
.info-title {{ font-size: 1.4vw; font-weight: 700; color: #fff; margin-bottom: 0.6vh; }}
.info-text {{ font-size: 1.15vw; color: #aaa; line-height: 1.5; }}

/* End slide */
.slide-end {{ background: #000; }}
.end-content {{ text-align: center; }}
.end-content h2 {{ font-size: 5vw; font-weight: 700; margin-bottom: 1vh; }}
.end-subtitle {{ font-size: 2vw; color: #ccc; margin-bottom: 2vh; }}
.end-meta {{ font-size: 1.4vw; color: #666; }}

/* --- Progress bar --- */
#progress-bar {{ position: fixed; bottom: 0; left: 0; width: 100%; height: 0.4vh;
  background: #222; z-index: 100; opacity: 0; transition: opacity 0.3s; cursor: pointer; }}
#progress-bar:hover, body:hover #progress-bar {{ opacity: 1; }}
#progress-fill {{ height: 100%; background: #FCD116; transition: width 0.15s ease; width: 0%; }}
.chapter-marker {{ position: absolute; top: -2.5vh; width: 2px; height: 2.5vh;
  background: #FCD116; opacity: 0; transition: opacity 0.3s; pointer-events: none; }}
#progress-bar:hover .chapter-marker {{ opacity: 0.6; }}
.chapter-marker-label {{ position: absolute; bottom: 3vh; left: 50%; transform: translateX(-50%);
  white-space: nowrap; font-size: 1vw; color: #FCD116; opacity: 0; transition: opacity 0.3s;
  pointer-events: none; }}
#progress-bar:hover .chapter-marker-label {{ opacity: 1; }}

/* --- TOC overlay --- */
#toc-overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.92); z-index: 200; display: none;
  align-items: center; justify-content: center; }}
#toc-overlay.visible {{ display: flex; }}
#toc-box {{ text-align: center; }}
#toc-box h3 {{ font-size: 2.5vw; margin-bottom: 3vh; color: #FCD116; }}
.toc-entry {{ font-size: 1.8vw; padding: 1.2vh 3vw; cursor: pointer; border-radius: 0.5vw;
  transition: background 0.15s; }}
.toc-entry:hover {{ background: rgba(252, 209, 22, 0.15); }}

/* --- Slide counter --- */
#slide-counter {{ position: fixed; bottom: 1.5vh; right: 1.5vw; font-size: 1vw;
  color: #555; z-index: 50; opacity: 0; transition: opacity 0.3s; pointer-events: none; }}
body:hover #slide-counter {{ opacity: 1; }}

/* Language selector slide */
.slide-lang-select {{ background: #000; }}
.lang-select-content {{ text-align: center; }}
.lang-select-content h2 {{ font-size: 3vw; font-weight: 700; margin-bottom: 0.5vh; }}
.lang-select-sub {{ font-size: 1.8vw; color: #999; font-style: italic; margin-bottom: 5vh; }}
.lang-buttons {{ display: flex; gap: 3vw; justify-content: center; }}
.lang-btn {{ font-size: 2.2vw; padding: 2.5vh 4vw; border: 2px solid #FCD116; background: transparent;
  color: #FCD116; border-radius: 1vw; cursor: pointer; font-family: inherit; font-weight: 600;
  transition: background 0.2s, color 0.2s; }}
.lang-btn:hover {{ background: #FCD116; color: #000; }}
.nav-hint {{ font-size: 1.2vw; color: #555; margin-top: 2vh; }}

/* Language visibility */
.lang-en, .lang-de {{ display: none; }}
body.show-en .lang-en {{ display: block; }}
body.show-de .lang-de {{ display: block; }}
span.lang-en, span.lang-de {{ display: none; }}
body.show-en span.lang-en {{ display: inline; }}
body.show-de span.lang-de {{ display: inline; }}

/* TOC content entries */
.toc-content-entry {{ font-size: 1.4vw; color: #aaa; padding-left: 5vw; }}

/* Cursor visibility */
body {{ cursor: none; }}
body:hover {{ cursor: default; }}
</style>
</head>
<body>

  <div id="slideshow">
    {slides_html}
  </div>

  <div id="progress-bar">
    <div id="progress-fill"></div>
  </div>

  <div id="toc-overlay">
    <div id="toc-box">
      <h3><span class="lang-en">Table of Contents</span><span class="lang-de">Inhaltsverzeichnis</span></h3>
      {toc_html}
    </div>
  </div>

  <div id="slide-counter"></div>

<script>
(function() {{
  const totalSlides = {total_slides};
  const chapterMarkers = {chapter_markers_js};
  let current = 0;
  let lang = 'en';

  const slides = document.querySelectorAll('.slide');
  const progressFill = document.getElementById('progress-fill');
  const progressBar = document.getElementById('progress-bar');
  const tocOverlay = document.getElementById('toc-overlay');
  const slideCounter = document.getElementById('slide-counter');

  // Fix video rotation for browsers that ignore MOV rotation metadata (e.g. Tizen)
  document.querySelectorAll('video[data-rotation]').forEach(video => {{
    video.addEventListener('loadedmetadata', () => {{
      const rot = parseInt(video.dataset.rotation);
      if (!rot) return;
      // If rotation is 90 or 270, a compliant browser reports swapped dimensions
      // (videoWidth < videoHeight for portrait). If not swapped, browser ignored rotation.
      const isPortraitRotation = (rot === 90 || rot === -90 || rot === 270 || rot === -270);
      if (isPortraitRotation && video.videoWidth > video.videoHeight) {{
        video.style.transform = 'rotate(' + rot + 'deg)';
        // Scale to fit container after rotation (swap width/height)
        const scale = Math.min(
          video.parentElement.clientWidth / video.videoHeight,
          video.parentElement.clientHeight / video.videoWidth
        );
        video.style.transform = 'rotate(' + rot + 'deg) scale(' + scale + ')';
        video.style.objectFit = 'initial';
        video.style.width = video.videoWidth + 'px';
        video.style.height = video.videoHeight + 'px';
        video.style.position = 'absolute';
        video.style.top = '50%';
        video.style.left = '50%';
        video.style.transform = 'translate(-50%, -50%) rotate(' + rot + 'deg) scale(' + scale + ')';
      }}
    }}, {{once: true}});
  }});

  // Language selection
  function setLanguage(chosen) {{
    lang = chosen;
    document.body.classList.remove('show-en', 'show-de');
    document.body.classList.add('show-' + chosen);
  }}

  document.querySelectorAll('.lang-btn').forEach(btn => {{
    btn.addEventListener('click', (e) => {{
      e.stopPropagation();
      setLanguage(btn.dataset.lang);
      showSlide(1); // advance to title slide
    }});
  }});

  // Default to English
  setLanguage('en');

  // Add chapter markers to progress bar
  chapterMarkers.forEach(m => {{
    const marker = document.createElement('div');
    marker.className = 'chapter-marker';
    marker.style.left = m.pct + '%';
    const label = document.createElement('div');
    label.className = 'chapter-marker-label';
    label.textContent = m.name;
    marker.appendChild(label);
    progressBar.appendChild(marker);
  }});

  function showSlide(index) {{
    if (index < 0 || index >= totalSlides) return;

    // Pause any playing video on current slide
    const currentSlide = slides[current];
    const currentVideo = currentSlide.querySelector('video');
    if (currentVideo) {{
      currentVideo.pause();
    }}

    // Hide current, show new
    slides[current].classList.remove('active');
    current = index;
    slides[current].classList.add('active');

    // Lazy load current and next 2 images
    for (let i = current; i < Math.min(current + 3, totalSlides); i++) {{
      const img = slides[i].querySelector('img[data-src]');
      if (img) {{
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
      }}
    }}

    // Auto-play video if navigated to a video slide
    const newVideo = slides[current].querySelector('video');
    if (newVideo) {{
      newVideo.currentTime = 0;
      newVideo.muted = false;
      newVideo.play().catch(() => {{
        // Autoplay with sound blocked — retry muted
        newVideo.muted = true;
        newVideo.play().catch(() => {{}});
      }});
    }}

    // Update progress
    const pct = totalSlides > 1 ? (current / (totalSlides - 1)) * 100 : 0;
    progressFill.style.width = pct + '%';
    slideCounter.textContent = (current + 1) + ' / ' + totalSlides;
  }}

  function next() {{ if (current === 0) return; showSlide(current + 1); }}
  function prev() {{ if (current <= 1) return; showSlide(current - 1); }}

  // Keyboard navigation
  document.addEventListener('keydown', (e) => {{
    if (tocOverlay.classList.contains('visible')) {{
      if (e.key === 'Escape' || e.key === 't' || e.key === 'T') {{
        tocOverlay.classList.remove('visible');
      }}
      return;
    }}
    switch(e.key) {{
      case 'ArrowRight': case ' ': case 'PageDown':
        e.preventDefault(); next(); break;
      case 'ArrowLeft': case 'Backspace': case 'PageUp':
        e.preventDefault(); prev(); break;
      case 'Home': e.preventDefault(); showSlide(1); break;
      case 'End': e.preventDefault(); showSlide(totalSlides - 1); break;
      case 't': case 'T':
        tocOverlay.classList.toggle('visible'); break;
      case 'f': case 'F':
        if (!document.fullscreenElement) {{
          document.documentElement.requestFullscreen().catch(() => {{}});
        }} else {{
          document.exitFullscreen();
        }}
        break;
      case 'Escape':
        if (document.fullscreenElement) document.exitFullscreen();
        break;
    }}
  }});

  // Video overlay navigation
  document.querySelectorAll('.video-nav').forEach(btn => {{
    btn.addEventListener('click', (e) => {{
      e.stopPropagation();
      if (btn.dataset.dir === 'prev') prev(); else next();
    }});
  }});

  // Click navigation (left 30% = back, right 70% = forward)
  document.addEventListener('click', (e) => {{
    if (tocOverlay.classList.contains('visible')) return;
    if (e.target.closest('#progress-bar') || e.target.closest('#toc-overlay') || e.target.closest('video') || e.target.closest('.lang-btn') || e.target.closest('.video-nav')) return;
    // Don't navigate away from lang-select via click — must use buttons
    if (current === 0) return;
    const x = e.clientX / window.innerWidth;
    if (x < 0.3) prev(); else next();
  }});

  // Progress bar click-to-seek
  progressBar.addEventListener('click', (e) => {{
    const pct = e.clientX / window.innerWidth;
    const targetSlide = Math.round(pct * (totalSlides - 1));
    showSlide(targetSlide);
  }});

  // TOC entry clicks
  document.querySelectorAll('.toc-entry').forEach(entry => {{
    entry.addEventListener('click', () => {{
      showSlide(parseInt(entry.dataset.goto));
      tocOverlay.classList.remove('visible');
    }});
  }});

  // Initialize first slide
  showSlide(0);
}})();
</script>
</body>
</html>'''

    return html


def main():
    print("Ghana Slideshow Generator")
    print("=" * 40)

    # Collect and date all media files
    media_files = collect_media_files()
    print(f"\nFound {len(media_files)} media files")

    print("\nExtracting dates...")
    dated_media = []
    for f in sorted(media_files):
        filepath = os.path.join(MEDIA_DIR, f)
        date = get_media_date(filepath)
        dated_media.append((f, date))
        # Print date source info for verification
        ext = os.path.splitext(f)[1].lower()
        print(f"  {f}: {date.strftime('%Y-%m-%d %H:%M:%S')}")

    # Sort by date
    dated_media.sort(key=lambda x: x[1])

    # Get chapter boundary dates from the boundary images
    boundary_dates = {}
    date_lookup = {f: d for f, d in dated_media}
    for ch, img_prefix in CHAPTER_BOUNDARIES.items():
        # Find the actual filename (could be .JPG or .jpg)
        found = None
        for f, d in dated_media:
            if f.startswith(img_prefix):
                found = (f, d)
                break
        if found:
            boundary_dates[ch] = found[1].replace(hour=0, minute=0, second=0)
            print(f"\nChapter {ch} boundary: {found[0]} = {found[1]} (using start-of-day: {boundary_dates[ch]})")
        else:
            print(f"\nWARNING: Chapter {ch} boundary image {img_prefix} not found!")
            return

    # Assign chapters
    chapters = assign_chapters(dated_media, boundary_dates)

    # Generate HTML
    print("\nGenerating HTML...")
    html = generate_html(chapters)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\nDone! Slideshow written to: {OUTPUT_FILE}")
    print(f"Open in Safari: open -a Safari '{OUTPUT_FILE}'")
    print(f"Or serve: python3 -m http.server 8000  (then open http://localhost:8000/slideshow.html)")


if __name__ == "__main__":
    main()
