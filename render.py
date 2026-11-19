#!/usr/bin/env python3
"""Paint the news-image-20261119 v3 front page (fresh build, this session).

One newspaper front page for Thursday 19 November 2026: 26 stories from
seven regions. Three lead stories, ten more illustrated stories (one of
them Scotland's World Cup qualification, promoted from the briefs), and
thirteen more as a numbered list beside a world map.

What is different from the earlier v2 page, and why:
- thirteen illustrations instead of twelve, all newly generated for this
  build as three painterly strips (leads, smalls-A, smalls-B);
- taller hero pictures and a denser grid, so the page reads at thumbnail
  size;
- the map is fixed: the GTA pin sits on New Zealand, the two Washington
  stories get offset badges with leader lines instead of one pile, the
  Europe and Gulf clusters are spread the same way, and the two stories
  that have no place on land (a world survey, a deep-space probe) are
  shown as badges in the oceans, not as pins on the wrong continent;
- the region strip counts regions honestly (seven groups, Oceania and
  World included) instead of claiming six continents;
- every number is used the same way everywhere ($115.8bn, 120-130 km/h).

The program runs on system python3 + PIL only. Deterministic: fixed
crop boxes measured from the generated strips, no timestamps, no
network. It writes entry.png next to this file.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"

W = H = 1024
MARGIN = 14
CW = W - 2 * MARGIN  # 996 content width

# --- newsprint palette: warm cream paper, slate ink, restrained accents ---
PAPER = (247, 241, 227)
INK = (32, 34, 38)
SLATE = (36, 50, 66)
RED = (178, 44, 32)
BLUE = (58, 106, 143)
SKY = (198, 220, 230)
SKY_LIGHT = (216, 232, 238)
SEA = (174, 205, 219)
SAND = (233, 220, 192)
LAND_LINE = (190, 175, 140)
GREEN = (74, 128, 84)
OCHRE = (216, 162, 74)
PURPLE = (128, 74, 140)
TEAL = (46, 130, 126)
GREY = (120, 122, 118)
LIGHT_GREY = (226, 224, 216)
WHITE = (252, 250, 244)

REGION_COLORS = {
    "Europe": BLUE,
    "Middle East": OCHRE,
    "Asia": PURPLE,
    "Africa": GREEN,
    "Americas": TEAL,
    "Oceania": TEAL,
    "World": GREY,
}

FONT_DIR = "/usr/share/fonts/truetype/liberation"
SERIF_B = f"{FONT_DIR}/LiberationSerif-Bold.ttf"
SERIF = f"{FONT_DIR}/LiberationSerif-Regular.ttf"
SANS_B = f"{FONT_DIR}/LiberationSans-Bold.ttf"
SANS = f"{FONT_DIR}/LiberationSans-Regular.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, width):
    """Greedy word wrap; returns a list of lines."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=fnt) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_text_block(draw, x, y, text, fnt, fill, width, leading, max_lines=None):
    lines = wrap(draw, text, fnt, width)
    if max_lines is not None:
        lines = lines[:max_lines]
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += leading
    return y


# --- illustration strips generated fresh for this build -------------------
# Each strip is one row of equal panels separated by thin white gutters.
# The crop boxes below were measured from the strips themselves (bright
# gutter columns), with a small inset so no gutter edge ever shows.
LEADS = "media-generation-grid-leads-0-c546f31d-de82-40aa-a55c-480a2fe593f0.png"
SMALLS_A = "media-generation-grid-smalls-a-0-c2a6709a-3e99-42eb-9859-441b5ef5e554.png"
SMALLS_B = "media-generation-grid-smalls-b-0-e0ca0db4-45a0-41fc-92a0-730ba0c4b623.png"

# (strip file, x0, x1, y0, y1) per panel, in strip pixels.
LEAD_BOXES = [
    (LEADS, 18, 896, 4, 908),
    (LEADS, 926, 1811, 4, 908),
    (LEADS, 1841, 2718, 4, 908),
]
SMALL_A_BOXES = [
    (SMALLS_A, 18, 671, 4, 700),
    (SMALLS_A, 699, 1371, 4, 700),
    (SMALLS_A, 1399, 2074, 4, 700),
    (SMALLS_A, 2102, 2788, 4, 700),
    (SMALLS_A, 2816, 3504, 4, 700),
]
SMALL_B_BOXES = [
    (SMALLS_B, 15, 692, 4, 700),
    (SMALLS_B, 716, 1393, 4, 700),
    (SMALLS_B, 1416, 2105, 4, 700),
    (SMALLS_B, 2129, 2810, 4, 700),
    (SMALLS_B, 2834, 3505, 4, 700),
]

_PANEL_CACHE = {}


def panel_for(number):
    """Return the generated illustration for story `number` (1-13)."""
    if number in _PANEL_CACHE:
        return _PANEL_CACHE[number]
    if number <= 3:
        fname, x0, x1, y0, y1 = LEAD_BOXES[number - 1]
    elif number <= 8:
        fname, x0, x1, y0, y1 = SMALL_A_BOXES[number - 4]
    else:
        fname, x0, x1, y0, y1 = SMALL_B_BOXES[number - 9]
    strip = Image.open(ASSETS / fname).convert("RGB")
    panel = strip.crop((x0, y0, x1, y1))
    _PANEL_CACHE[number] = panel
    return panel


def fit_panel(number, w, h, centering=(0.5, 0.5)):
    """Crop the story's illustration to the panel box.

    centering picks which band survives a wide crop: the hero pictures
    keep their subjects low in the frame (a car, a motorcade), so the
    heroes are cropped bottom-biased at (0.5, 0.8); the mediums are
    centre-cropped.
    """
    return ImageOps.fit(panel_for(number), (w, h), Image.LANCZOS,
                        centering=centering)


def caption_bar(draw, x, y, w, text, bar_h=20, size=11):
    """Dark caption bar across the foot of an illustration."""
    draw.rectangle([x, y, x + w, y + bar_h], fill=SLATE)
    draw.text((x + 6, y + 3), text, font=font(SANS_B, size), fill=WHITE)


def story_block(img, draw, x, y, w, img_h, story, sizes):
    """One illustrated story: picture, caption bar, kicker, headline, deck.

    sizes: (ty_gap, kicker_size, head_size, head_dy, head_leading,
            deck_size, deck_dy, deck_leading, cap_h, cap_size)
    """
    (num, region, kicker, headline, deck, caption) = story
    (ty_gap, kicker_size, head_size, head_dy, head_leading,
     deck_size, deck_dy, deck_leading, cap_h, cap_size) = sizes
    # Heroes are wide and short: crop bottom-biased so the low subjects
    # survive. Story 1's red car sits at the very bottom of its panel,
    # so it takes the full bottom band; stories 2-3 sit at 0.8.
    # Mediums are centre-cropped.
    if img_h >= 120:
        centering = (0.5, 1.0) if num == 1 else (0.5, 0.8)
    else:
        centering = (0.5, 0.5)
    pic = fit_panel(num, w, img_h, centering=centering)
    img.paste(pic, (x, y))
    caption_bar(draw, x, y + img_h - cap_h, w, caption,
                bar_h=cap_h, size=cap_size)
    ty = y + img_h + ty_gap
    draw.text((x, ty), kicker, font=font(SANS_B, kicker_size),
              fill=REGION_COLORS[region])
    draw_text_block(draw, x, ty + head_dy, headline, font(SERIF_B, head_size),
                    INK, w, head_leading, max_lines=2)
    draw_text_block(draw, x, ty + deck_dy, deck, font(SANS, deck_size),
                    INK, w, deck_leading, max_lines=2)

# --- stories: (number, region, kicker, headline, deck, caption) -----------
HEROES = [
    (1, "Oceania", "1 \u00b7 CULTURE \u00b7 VIDEO GAMES",
     "GTA VI rolls out around the world",
     "Rockstar's game unlocks at midnight local time, starting in New "
     "Zealand; after 13 years, Metacritic 99.",
     "NEW ZEALAND \u2014 THE ROLLOUT BEGINS"),
    (2, "Asia", "2 \u00b7 ASIA \u00b7 DIPLOMACY",
     "Trump, Xi, Putin due to meet in Shenzhen today",
     "First trilateral of the three sitting presidents, on the APEC "
     "sidelines in Shenzhen; no outcome yet.",
     "SHENZHEN \u2014 DUE TODAY"),
    (3, "Middle East", "3 \u00b7 MIDDLE EAST \u00b7 IRAN WAR",
     "Iran fires on US bases in Kuwait and Bahrain",
     "Tehran says it hit US drone and missile sites; Bahrain and Kuwait "
     "say the attacks were intercepted.",
     "GULF \u2014 INTERCEPTORS UP"),
]

MEDIUMS_ROW1 = [
    (4, "Europe", "4 \u00b7 EUROPE \u00b7 UKRAINE",
     "EU proposes \u20ac45bn loan for Ukraine",
     "\u20ac20bn budget aid, \u20ac25bn military; repaid only once Russia pays "
     "reparations.",
     "BRUSSELS \u2014 \u20ac45BN PLAN"),
    (5, "Americas", "5 \u00b7 US \u00b7 BUSINESS",
     "Nvidia rules out Huang return; sales double",
     "Board will not reinstate the founder, who quit amid security "
     "concerns.",
     "SANTA CLARA \u2014 $115.8BN QUARTER"),
    (6, "Americas", "6 \u00b7 US \u00b7 POLITICS",
     "Democrats nominate Jeffries for Speaker, 251\u201311",
     "He would be the first Black Speaker if the full House elects him "
     "on 3 Jan.",
     "WASHINGTON \u2014 251\u201311"),
    (7, "World", "7 \u00b7 WORLD \u00b7 RELIGION",
     "Pew: Islam to pass Christianity by 2035",
     "Pew projects 2.57bn Muslims vs 2.52bn Christians by 2035; both "
     "still growing.",
     "WORLD \u2014 2.57BN BY 2035"),
    (8, "World", "8 \u00b7 SPACE \u00b7 SCIENCE",
     "Voyager 1 reaches one light-day from Earth",
     "NASA says the probe crossed about 16.1bn miles on 18 Nov; "
     "briefing today.",
     "DEEP SPACE \u2014 16.1BN MILES"),
]

MEDIUMS_ROW2 = [
    (9, "Asia", "9 \u00b7 ASIA \u00b7 WEATHER",
     "Cyclone Akvan bears down on India's east coast",
     "Very severe storm forecast to cross Andhra Pradesh on Friday; "
     "winds 120\u2013130 km/h.",
     "BAY OF BENGAL \u2014 LANDFALL FRIDAY"),
    (10, "Middle East", "10 \u00b7 MIDDLE EAST \u00b7 GAZA",
     "Gaza's winter shelters fail in the rain",
     "UN says tens of thousands of shelters were damaged by the first "
     "winter rains.",
     "GAZA \u2014 46,000 HOMES FLOODED"),
    (11, "Middle East", "11 \u00b7 MIDDLE EAST \u00b7 YEMEN",
     "Houthis close on Aden as army pulls back",
     "Sources say fighters are about 60 km from the city after "
     "government forces left.",
     "BAB EL-MANDEB \u2014 60 KM FROM ADEN"),
    (12, "Americas", "12 \u00b7 US \u00b7 ECONOMY",
     "Fed minutes point to more rate rises",
     "Most officials expect further hikes if inflation and jobs stay "
     "hot, minutes show.",
     "WASHINGTON \u2014 RATES STILL RISING"),
    (13, "Europe", "13 \u00b7 EUROPE \u00b7 SPORT",
     "Scotland beat Denmark 4\u20132 to reach World Cup",
     "The 4\u20132 win at Hampden ends a 28-year wait for the World Cup "
     "finals.",
     "HAMPDEN \u2014 4\u20132, WORLD CUP SEALED"),
]

ALSO_ON = [
    (14, "Zelensky urges the US to lift Starshield limits, saying they hinder drone defence."),
    (15, "Canada adjusts China ties; Carney seeks the right deal with the US."),
    (16, "US senators warn AI cyber threats are outpacing defences."),
    (17, "France: justice minister says M\u00e9lenchon could win the presidency."),
    (18, "Saudi Arabia says the danger has passed in three southern cities."),
    (19, "Libya seizes cocaine and millions of pills in the east, officials say."),
    (20, "Amazon pledges $7bn for renewables in India by 2030."),
    (21, "India and Japan to review defence ties in 2+2 talks."),
    (22, "Modi meets the Prince and Princess of Wales, talks UK\u2013India ties."),
    (23, "Kyiv: Russia hit the capital's Dnipro bridges; Ukraine claims a new Crimea bridge strike."),
    (24, "Tankers hit in the Strait of Hormuz, reports say; Iran claims mine strikes."),
    (25, "Board of Peace warns the Gaza truce could collapse without steps."),
    (26, "Somalia accuses the UAE of secretly building bases on its soil."),
]

DATA_STRIP = [
    ("16m", "GTA VI copies pre-sold"),
    ("\u20ac45bn", "EU loan for Ukraine, 2027"),
    ("251\u201311", "Jeffries nomination vote"),
    ("$115.8bn", "Nvidia quarterly sales"),
    ("16.1bn", "Voyager 1 miles from Earth"),
    ("120\u2013130", "Akvan landfall winds km/h"),
]

# lon/lat of the illustrated stories, for the map pins. The two numbers
# after the coordinates are the badge offset in map pixels: 0, 0 means the
# badge sits on the true point; anything else draws a small dot on the
# true point and a leader line out to an offset badge, so no two badges
# ever pile up. Stories 7 (a world survey) and 8 (a deep-space probe)
# have no land position at all: their badges sit in empty ocean.
PINS = {
    1: (174, -41, -14, -6),   # Auckland: badge pulled left off the edge
    2: (114, 22, 0, 0),      # Shenzhen
    3: (51, 27, 14, -12),    # Gulf: badge up-right, clear of Riyadh's dot
    4: (4, 51, -12, 14),     # Brussels: badge down-left, clear of London
    5: (-122, 37, 0, 0),     # Santa Clara
    6: (-77, 39, -18, -14),  # Washington (Jeffries): badge up-left
    7: (-150, -35, 0, 0),    # World survey: South Pacific, ocean badge
    8: (155, 68, 0, 0),      # Deep space: Arctic Ocean, star badge
    9: (88, 16, 0, 0),       # Bay of Bengal
    10: (34, 32, -16, -10),  # Gaza: badge up-left, clear of the Gulf
    11: (44, 11, 0, 0),      # Bab el-Mandeb
    12: (-79, 36, 18, 14),   # Washington (Fed): badge down-right
    13: (-4, 56, 2, -16),    # Scotland: badge straight up
}

PIN_REGION = {1: "Oceania", 2: "Asia", 3: "Middle East", 4: "Europe",
              5: "Americas", 6: "Americas", 7: "World", 8: "World",
              9: "Asia", 10: "Middle East", 11: "Middle East",
              12: "Americas", 13: "Europe"}

# Small grey dots for the also-on stories (lon/lat).
DOTS = {
    14: (30, 50), 15: (-75, 45), 16: (-77, 39), 17: (2, 49),
    18: (47, 25), 19: (20, 32), 20: (77, 29), 21: (140, 36),
    22: (0, 51), 23: (30, 50), 24: (56, 27), 25: (34, 31), 26: (45, 2),
}

# Rough continent outlines in lon/lat (schematic, drawn for this page).
CONTINENTS = [
    [(-168, 65), (-145, 70), (-120, 72), (-95, 80), (-80, 72), (-65, 60),
     (-55, 47), (-65, 42), (-75, 35), (-81, 31), (-90, 21), (-97, 16),
     (-105, 20), (-115, 29), (-125, 40), (-130, 50), (-145, 60),
     (-160, 58)],
    [(-58, 64), (-45, 60), (-40, 70), (-55, 76), (-65, 75)],
    [(-80, 10), (-72, 12), (-62, 10), (-52, 5), (-50, -5), (-40, -10),
     (-35, -20), (-48, -28), (-58, -35), (-65, -45), (-70, -55),
     (-73, -40), (-72, -20), (-80, -5)],
    [(-10, 36), (-9, 43), (-2, 48), (0, 51), (5, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (24, 59), (28, 60), (30, 70), (25, 71), (18, 69),
     (12, 65), (5, 60), (-5, 58), (-10, 52)],
    [(-17, 15), (-10, 30), (0, 36), (10, 37), (20, 32), (30, 31), (35, 28),
     (40, 15), (43, 11), (48, 11), (51, 12), (44, 0), (40, -10), (35, -20),
     (32, -29), (26, -34), (20, -35), (15, -27), (12, -18), (9, -1),
     (9, 4), (-8, 5), (-13, 8)],
    [(30, 36), (35, 36), (42, 41), (50, 40), (55, 45), (60, 50), (70, 55),
     (80, 60), (90, 65), (100, 70), (110, 73), (130, 72), (160, 70),
     (178, 66), (170, 60), (160, 55), (155, 50), (142, 45), (140, 38),
     (130, 33), (127, 35), (122, 30), (120, 23), (110, 20), (105, 10),
     (100, 8), (95, 15), (90, 22), (85, 20), (80, 15), (75, 8), (70, 25),
     (65, 25), (60, 25), (55, 26), (50, 29), (45, 30), (40, 35)],
    [(113, -22), (114, -30), (120, -34), (130, -32), (140, -38), (150, -37),
     (153, -27), (146, -19), (142, -11), (136, -12), (132, -11), (126, -14),
     (122, -17), (118, -20)],
]

def render():
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    # --- masthead ---
    draw.text((MARGIN, 10), "THE WORLD'S NEWS IN ONE PICTURE",
              font=font(SANS_B, 13), fill=RED)
    right = "26 STORIES \u00b7 7 REGIONS \u00b7 ALL FROM THURSDAY"
    right_w = draw.textlength(right, font=font(SANS_B, 13))
    draw.text((W - MARGIN - right_w, 10), right, font=font(SANS_B, 13), fill=INK)
    draw.text((MARGIN, 30), "Thursday 19 November 2026",
              font=font(SERIF_B, 46), fill=INK)
    draw.line([(MARGIN, 88), (W - MARGIN, 88)], fill=INK, width=3)
    draw.line([(MARGIN, 92), (W - MARGIN, 92)], fill=INK, width=1)

    # --- data strip: six numbers the page can be checked against ---
    cell = CW // 6
    y = 96
    for i, (num, label) in enumerate(DATA_STRIP):
        x = MARGIN + i * cell
        draw.text((x, y), num, font=font(SERIF_B, 19), fill=INK)
        draw_text_block(draw, x, y + 23, label, font(SANS, 9), GREY,
                        cell - 10, 11, max_lines=1)
    draw.line([(MARGIN, 130), (W - MARGIN, 130)], fill=INK, width=1)

    # --- region strip: honest counts, seven groups ---
    strip = ("EUROPE 6  \u00b7  MIDDLE EAST 6  \u00b7  ASIA 4  \u00b7  "
             "AMERICAS 5  \u00b7  AFRICA 2  \u00b7  OCEANIA 1  \u00b7  WORLD 2")
    strip_w = draw.textlength(strip, font=font(SANS_B, 12))
    draw.text(((W - strip_w) / 2, 134), strip, font=font(SANS_B, 12), fill=INK)

    # --- heroes: 3 equal columns, taller pictures than v2 ---
    # sizes: ty_gap, kicker, head size, head dy, head leading,
    #        deck size, deck dy, deck leading, caption height, caption size
    hero_y, hero_w, hero_gap = 150, 324, 12
    for i, story in enumerate(HEROES):
        story_block(img, draw, MARGIN + i * (hero_w + hero_gap), hero_y,
                    hero_w, 140, story, (5, 11, 18, 16, 21, 12, 60, 14, 20, 11))

    # --- mediums row 1: 5 columns (stories 4-8) ---
    row1_y, row1_w, row1_gap = 384, 191, 10
    for i, story in enumerate(MEDIUMS_ROW1):
        story_block(img, draw, MARGIN + i * (row1_w + row1_gap), row1_y,
                    row1_w, 86, story, (4, 9, 13, 13, 15, 10, 43, 12, 17, 9))

    # --- mediums row 2: 5 columns (stories 9-13, Scotland last) ---
    row2_y, row2_w, row2_gap = 543, 191, 10
    for i, story in enumerate(MEDIUMS_ROW2):
        story_block(img, draw, MARGIN + i * (row2_w + row2_gap), row2_y,
                    row2_w, 90, story, (4, 10, 14, 14, 16, 10, 45, 12, 17, 9))

    # --- also-on header ---
    ay = 710
    draw.text((MARGIN, ay), "ALSO ON THURSDAY 19 NOVEMBER",
              font=font(SANS_B, 12), fill=RED)
    draw.line([(MARGIN, ay + 18), (W - MARGIN, ay + 18)], fill=INK, width=1)

    # --- world map, with leader-line badges so nothing piles up ---
    map_x, map_y, map_w, map_h = MARGIN, ay + 26, 340, 200
    draw.rectangle([map_x, map_y, map_x + map_w, map_y + map_h],
                   fill=SKY_LIGHT, outline=LAND_LINE)

    def project(lon, lat):
        px = map_x + (lon + 180) / 360 * map_w
        py = map_y + (75 - lat) / 130 * map_h
        return (px, py)

    for poly in CONTINENTS:
        draw.polygon([project(lon, lat) for lon, lat in poly],
                     fill=SAND, outline=LAND_LINE)
    for num, (lon, lat) in DOTS.items():
        px, py = project(lon, lat)
        draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill=GREY)
    for num, (lon, lat, dx, dy) in PINS.items():
        px, py = project(lon, lat)
        bx, by = px + dx, py + dy
        # keep the badge inside the map frame
        bx = max(map_x + 10, min(map_x + map_w - 10, bx))
        by = max(map_y + 10, min(map_y + map_h - 10, by))
        if dx or dy:
            draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill=INK)
            draw.line([(px, py), (bx, by)], fill=INK, width=1)
        col = REGION_COLORS[PIN_REGION[num]]
        draw.ellipse([bx - 9, by - 9, bx + 9, by + 9], fill=col,
                     outline=WHITE, width=2)
        label = str(num)
        tw = draw.textlength(label, font=font(SANS_B, 10))
        draw.text((bx - tw / 2, by - 7), label, font=font(SANS_B, 10),
                  fill=WHITE)
    draw.text((map_x, map_y + map_h + 4),
              "Pins: stories 1\u201313 \u2014 dots: 14\u201326. 7 world, 8 deep space in the oceans.",
              font=font(SANS, 9), fill=GREY)

    # --- also-on list, two columns ---
    list_x = MARGIN + map_w + 14
    col_w = (W - MARGIN - list_x - 10) // 2
    num_font = font(SANS_B, 11)
    txt_font = font(SANS, 11)
    for col in range(2):
        x = list_x + col * (col_w + 10)
        y = map_y
        for num, text in ALSO_ON[col * 7:(col + 1) * 7]:
            draw.text((x, y), f"{num}", font=num_font, fill=RED)
            lines = wrap(draw, text, txt_font, col_w - 24)
            ly = y
            for line in lines[:2]:
                draw.text((x + 24, ly), line, font=txt_font, fill=INK)
                ly += 12
            y = ly + 4

    # --- footer ---
    foot_y = 972
    draw.text((MARGIN, foot_y),
              "DATE CHECK \u2014 Left out as earlier news: Estonia's border closure, announced 16 Nov; "
              "the NSA network outage, first reported 17 Nov.",
              font=font(SANS_B, 9), fill=INK)
    draw.text((MARGIN, foot_y + 13),
              "Every story here happened or was first reported on Thursday 19 November 2026. "
              "Contested claims are marked as claims. Sources: Reuters, AP, AFP, BBC, Pew, NASA, IMD. Original drawings.",
              font=font(SANS, 9), fill=GREY)

    out = ROOT / "entry.png"
    img.save(out, "PNG", optimize=True)
    return out


if __name__ == "__main__":
    path = render()
    print(f"wrote {path} ({path.stat().st_size} bytes)")
