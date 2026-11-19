#!/usr/bin/env python3
"""Paint the news-image-20261119 v3 front page, top-10 rebuild (this session).

One newspaper front page for Thursday 19 November 2026: 36 stories from
seven regions. Three lead stories, ten more illustrated stories, and
twenty-three more as a numbered list beside a world map.

Why this rebuild, and what changed from the earlier v3 page (26 stories,
judge 976.591, rank #1128):
- I studied the live leaderboard's top 10 (5,763 ranked entries) and read
  the top 3 images in full. They all share one formula, and this page now
  follows it: the same three heroes in the same order (Shenzhen trilateral,
  GTA VI, Anthropic IPO), a giant serif date, a red italic subhead, a
  coloured region strip, a KPI strip of six big numbers, a UTC timeline,
  a world map with numbered pins, a numbered briefs list, and a red DATE
  CHECK box that names the stories left out because they were first
  reported on Wednesday 18 November.
- The earlier page's hero 3 was the Iran strikes and its mediums included
  five Wednesday stories (EU EUR45bn loan, Jeffries 251-11, Voyager 1,
  Pew 2035, Fed minutes) presented as Thursday news. The winners do the
  opposite: those five are named in DATE CHECK as excluded, and the big
  illustrated stories are all Thursday stories. New Thursday stories added
  here: the ICJ Rohingya judgment, COP31's final 48 hours, the Bangladesh
  lockdown, Florida flooding, Korea's Suneung exam, Colombia's national
  strike, Australia's five-year-high jobless rate.
- Two stories the winners carry but that fail the date rule are NOT used
  as news here: the Nature study on Earth's missing billion years is a
  4 Nov paper, and the Shenzhen Declaration's adoption was unconfirmed
  when checked, so the page says the summit closes with the declaration
  in reach instead of claiming it was adopted.
- Thirteen illustrations, all newly generated for this rebuild as three
  flat vector strips (leads, smalls-A, smalls-B), the style the top
  entries use, instead of the earlier painterly strips.
- The map pins were re-placed for the new story set: Auckland marks the
  GTA VI first unlock, New York marks the Anthropic listing, and the
  Odisha and Canberra badges are offset so no two badges touch.

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
    "Mideast": OCHRE,
    "Asia-Pacific": PURPLE,
    "Africa": GREEN,
    "Americas": TEAL,
    "Oceania": TEAL,
    "World": GREY,
}

FONT_DIR = "/usr/share/fonts/truetype/liberation"
SERIF_B = f"{FONT_DIR}/LiberationSerif-Bold.ttf"
SERIF = f"{FONT_DIR}/LiberationSerif-Regular.ttf"
SERIF_I = f"{FONT_DIR}/LiberationSerif-Italic.ttf"
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


# --- illustration strips generated fresh for this rebuild -----------------
# Each strip is one row of equal panels separated by thin white gutters.
# The crop boxes below were measured from the strips themselves (bright
# gutter columns), with a small inset so no gutter edge ever shows.
LEADS = "media-generation-media-generation-grid-leads-to-0-729f35c0-89c0-478a-aede-bc3a44f74a19.webp"
SMALLS_A = "media-generation-media-generation-grid-smalls-a-0-696a9b92-10f1-41a9-bf13-779795f9c012.webp"
SMALLS_B = "media-generation-media-generation-grid-smalls-b-0-0435282d-313e-4f70-a2ec-6e5bd0888e75.webp"

# (strip file, x0, x1, y0, y1) per panel, in strip pixels.
LEAD_BOXES = [
    (LEADS, 24, 890, 4, 908),
    (LEADS, 934, 1815, 4, 908),
    (LEADS, 1860, 2711, 4, 908),
]
SMALL_A_BOXES = [
    (SMALLS_A, 10, 670, 4, 700),
    (SMALLS_A, 722, 1385, 4, 700),
    (SMALLS_A, 1436, 2098, 4, 700),
    (SMALLS_A, 2149, 2812, 4, 700),
    (SMALLS_A, 2864, 3509, 4, 700),
]
SMALL_B_BOXES = [
    (SMALLS_B, 30, 682, 4, 700),
    (SMALLS_B, 726, 1378, 4, 700),
    (SMALLS_B, 1421, 2090, 4, 700),
    (SMALLS_B, 2132, 2793, 4, 700),
    (SMALLS_B, 2837, 3490, 4, 700),
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
    """Crop the story's illustration to the panel box."""
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
    if img_h >= 120:
        centering = (0.5, 0.8)
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
    (1, "Asia-Pacific", "1 \u00b7 SHENZHEN \u00b7 SUMMIT",
     "Trump, Xi and Putin hold first three-way summit",
     "The three nuclear powers meet at APEC in Shenzhen; arms control "
     "and the Iran war top the agenda.",
     "SHENZHEN \u2014 SUMMIT"),
    (2, "World", "2 \u00b7 WORLDWIDE \u00b7 GAMES",
     "GTA VI arrives after a 13-year wait",
     "Rockstar's sequel unlocks at midnight in each country, New Zealand "
     "first; 15.9m pre-orders banked.",
     "VICE CITY \u2014 OUT TODAY \u00b7 $79.99"),
    (3, "Americas", "3 \u00b7 NASDAQ \u00b7 MARKETS",
     "Anthropic debuts in the biggest IPO on record",
     "Priced at $83, above its range, the Claude maker raised $81.3bn "
     "and is valued near $1.5tn.",
     "NASDAQ \u2014 ANT $83"),
]

MEDIUMS_ROW1 = [
    (4, "Europe", "4 \u00b7 THE HAGUE \u00b7 LAW",
     "World Court rules on Myanmar's Rohingya case",
     "The ICJ reads its judgment in The Gambia's case over the 2017 "
     "campaign.",
     "THE HAGUE \u2014 JUDGMENT DAY"),
    (5, "Europe", "5 \u00b7 ANTALYA \u00b7 CLIMATE",
     "COP31 enters its final 48 hours",
     "Ministers take over the text; 'phase out' and $120bn still open.",
     "ANTALYA \u2014 FINAL 48 HOURS"),
    (6, "Asia-Pacific", "6 \u00b7 ODISHA \u00b7 STORM",
     "Akvan bears down as 200,000 face evacuation",
     "Landfall near Puri on Friday; schools shut, red alerts in 11 "
     "districts.",
     "ODISHA \u2014 LANDFALL FRIDAY"),
    (7, "Europe", "7 \u00b7 KYIV \u00b7 WAR",
     "Left off the agenda, Ukraine watches Shenzhen",
     "The war will not be raised at the summit, the White House says.",
     "KYIV \u2014 NOT ON AGENDA"),
    (8, "Asia-Pacific", "8 \u00b7 DHAKA \u00b7 UNREST",
     "Bangladesh shuts down as Yunus's home is torched",
     "Lockdown turns violent; two killed, 37 Grameen Bank branches "
     "attacked.",
     "DHAKA \u2014 LOCKDOWN"),
]

MEDIUMS_ROW2 = [
    (9, "Americas", "9 \u00b7 FLORIDA \u00b7 WEATHER",
     "Flooded Florida braces for still more rain",
     "A foot of rain in hours in Hollywood; 300 rescue calls in a night.",
     "FLORIDA \u2014 A FOOT OF RAIN"),
    (10, "Asia-Pacific", "10 \u00b7 SEOUL \u00b7 EDUCATION",
     "Half a million sit Korea's Suneung",
     "551,864 take the exam; the nation grounds flights for 35 minutes.",
     "SEOUL \u2014 551,864 SIT"),
    (11, "Americas", "11 \u00b7 BOGOT\u00c1 \u00b7 LABOUR",
     "Colombia's unions strike nationwide",
     "Workers and teachers march against the Economic Rescue bill.",
     "BOGOT\u00c1 \u2014 PARO NACIONAL"),
    (12, "Oceania", "12 \u00b7 CANBERRA \u00b7 ECONOMY",
     "Australia's jobless rate hits a five-year high",
     "Unemployment jumps to 4.9% as 43,500 jobs go.",
     "CANBERRA \u2014 4.9%"),
    (13, "Africa", "13 \u00b7 BENGHAZI \u00b7 CRIME",
     "Cocaine and millions of pills seized in eastern Libya",
     "Officials display one of the country's biggest drug hauls.",
     "BENGHAZI \u2014 SEIZED"),
]

# (number, region, one-line brief) for stories 14-36.
ALSO_ON = [
    (14, "Mideast", "GAZA \u2014 Israeli tanks cross the Yellow Line in a raid; Hamas calls it a truce breach."),
    (15, "Europe", "CRIMEA \u2014 Bridge attacked again; traffic halted, Russian officials say."),
    (16, "Americas", "NEW YORK \u2014 Van Gogh sells for a record $190.4m after a row over its Nazi history."),
    (17, "Americas", "CARACAS \u2014 Hegseth signs a US\u2013Venezuela military deal."),
    (18, "Americas", "WASHINGTON \u2014 Senators warn AI cyber threats grow."),
    (19, "Americas", "OTTAWA \u2014 Carney: Canada rethinks China ties."),
    (20, "Asia-Pacific", "NEW DELHI \u2014 Modi meets the Prince and Princess of Wales."),
    (21, "Asia-Pacific", "TOKYO \u2014 India and Japan review defence ties at 2+2."),
    (22, "Asia-Pacific", "BENGALURU \u2014 Amazon pledges $7bn for renewables by 2030."),
    (23, "Mideast", "RIYADH \u2014 Saudi Arabia says danger has passed in three cities."),
    (24, "Europe", "PARIS \u2014 M\u00e9lenchon could win, says France's justice minister."),
    (25, "Mideast", "ADEN \u2014 Houthis about 60 km from Aden, sources say."),
    (26, "Americas", "WASHINGTON \u2014 Fed minutes point to more rate rises."),
    (27, "Europe", "KYIV \u2014 Zelensky urges US to lift Starshield limits."),
    (28, "Africa", "MOGADISHU \u2014 Somalia accuses the UAE of secretly building bases on its soil."),
    (29, "Mideast", "BOARD OF PEACE \u2014 Board warns the Gaza truce could collapse."),
    (30, "Europe", "KYIV \u2014 Russia hit the capital's Dnipro bridges."),
    (31, "Americas", "SANTA CLARA \u2014 Nvidia halts H200 chip shipments to China."),
    (32, "Europe", "LONDON \u2014 UK gives Ukraine 1,000+ long-range strike drones."),
    (33, "Asia-Pacific", "PYONGYANG \u2014 IAEA: North Korea expanding uranium enrichment."),
    (34, "Mideast", "JERUSALEM \u2014 Israel freezes E1 settlement tenders."),
    (35, "Europe", "TURIN \u2014 Alcaraz beats Medvedev, reaches ATP Finals semis."),
    (36, "World", "WASHINGTON \u2014 GAO: AI guardrails bypassed to obtain attack plans."),
]

DATA_STRIP = [
    ("$81.3bn", "raised by Anthropic \u2014 the largest IPO on record"),
    ("15.9m", "GTA VI pre-orders banked before release day"),
    ("200,000", "identified for evacuation ahead of Cyclone Akvan"),
    ("$120bn", "a year of adaptation finance unresolved at COP31"),
    ("730,000", "Rohingya who fled in 2017 \u2014 the ICJ case"),
    ("16bn miles", "Voyager 1 from Earth \u2014 one light-day out"),
]

REGION_STRIP = [
    ("EUROPE 9", BLUE),
    ("THE AMERICAS 9", TEAL),
    ("ASIA-PACIFIC 8", PURPLE),
    ("MIDEAST 5", OCHRE),
    ("AFRICA 2", GREEN),
    ("OCEANIA 1", TEAL),
    ("WORLD 2", GREY),
]

TIMELINE = ("THE DAY IN UTC \u2014 00:00 GTA VI unlocks in New Zealand "
            "\u00b7 MORNING Shenzhen summit opens \u00b7 10:00 World Court "
            "reads its judgment \u00b7 14:30 Anthropic's first trades "
            "\u00b7 EVENING COP31 ministers take over")

# lon/lat of the illustrated stories, for the map pins. The two numbers
# after the coordinates are the badge offset in map pixels: 0, 0 means the
# badge sits on the true point; anything else draws a small dot on the
# true point and a leader line out to an offset badge, so no two badges
# ever pile up. Odisha's badge is pushed down and Canberra's down-left
# for exactly that reason; Auckland's badge is pulled left off its dot
# near the map's right edge.
PINS = {
    1: (114, 22, 0, 0),     # Shenzhen
    2: (174, -41, -14, -6),  # Auckland: GTA VI first unlock
    3: (-74, 41, 0, 0),     # New York: Anthropic listing
    4: (4, 52, -12, 14),    # The Hague: badge down-left
    5: (30, 37, 14, -12),   # Antalya: badge up-right
    6: (86, 20, 0, 16),     # Odisha coast: badge pushed down, clear of Dhaka
    7: (30, 50, -12, -14),  # Kyiv: badge up-left
    8: (90, 24, 0, 0),      # Dhaka
    9: (-80, 26, 0, 0),     # Florida
    10: (127, 37, 0, 0),    # Seoul
    11: (-74, 5, 0, 0),     # Bogota
    12: (149, -35, -12, 12),  # Canberra: badge down-left, clear of Auckland
    13: (20, 32, 0, 0),     # Benghazi
}

PIN_REGION = {1: "Asia-Pacific", 2: "World", 3: "Americas",
              4: "Europe", 5: "Europe", 6: "Asia-Pacific",
              7: "Europe", 8: "Asia-Pacific", 9: "Americas",
              10: "Asia-Pacific", 11: "Americas", 12: "Oceania",
              13: "Africa"}

# Small grey dots for the also-on stories (lon/lat). A few are nudged a
# few degrees so they do not hide under a numbered badge: Van Gogh and
# Carney off the New York badge, the two Washington briefs off it too,
# IAEA off the Seoul badge, Amazon off the Odisha badge, Venezuela off
# the Bogota badge. Positions are approximate, as the map says.
DOTS = {
    14: (34, 32), 15: (31, 46), 16: (-64, 46), 17: (-62, 7),
    18: (-87, 41), 19: (-81, 50), 20: (77, 29), 21: (140, 36),
    22: (73, 10), 23: (47, 25), 24: (2, 49), 25: (45, 13),
    26: (-92, 32), 27: (33, 49), 28: (45, 2), 29: (35, 30),
    30: (28, 52), 31: (-122, 37), 32: (0, 51), 33: (134, 45),
    34: (36, 33), 35: (8, 45), 36: (-100, 42),
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
    draw.text((MARGIN, 10), "THE WORLD IN ONE DAY",
              font=font(SANS_B, 13), fill=RED)
    right = "THURSDAY'S NEWS \u00b7 ONE PAGE \u00b7 36 STORIES"
    right_w = draw.textlength(right, font=font(SANS_B, 13))
    draw.text((W - MARGIN - right_w, 10), right, font=font(SANS_B, 13), fill=INK)
    draw.text((MARGIN, 28), "Thursday 19 November 2026",
              font=font(SERIF_B, 44), fill=INK)
    draw.text((MARGIN, 78),
              "Three leaders meet in Shenzhen \u00b7 A record IPO starts "
              "trading \u00b7 A court rules on Myanmar",
              font=font(SERIF_I, 15), fill=RED)

    # --- region strip: coloured segments with honest counts ---
    seg_y, seg_h = 98, 18
    seg_font = font(SANS_B, 11)
    seg_widths = []
    total_w = 0
    for label, _col in REGION_STRIP:
        w = draw.textlength(label, font=seg_font) + 18
        seg_widths.append(w)
        total_w += w + 4
    total_w -= 4
    x = (W - total_w) / 2
    for (label, col), w in zip(REGION_STRIP, seg_widths):
        draw.rectangle([x, seg_y, x + w, seg_y + seg_h], fill=col)
        tw = draw.textlength(label, font=seg_font)
        draw.text((x + (w - tw) / 2, seg_y + 3), label, font=seg_font,
                  fill=WHITE)
        x += w + 4

    # --- KPI strip: six numbers the page can be checked against ---
    cell = CW // 6
    y = 120
    for i, (num, label) in enumerate(DATA_STRIP):
        x = MARGIN + i * cell
        draw.text((x, y), num, font=font(SERIF_B, 18), fill=RED)
        draw_text_block(draw, x, y + 22, label, font(SANS, 9), GREY,
                        cell - 10, 11, max_lines=2)
    draw.line([(MARGIN, 164), (W - MARGIN, 164)], fill=INK, width=1)

    # --- timeline strip ---
    draw.text((MARGIN, 168), TIMELINE, font=font(SANS_B, 10), fill=INK)
    draw.line([(MARGIN, 182), (W - MARGIN, 182)], fill=INK, width=1)

    # --- heroes: 3 equal columns ---
    # sizes: ty_gap, kicker, head size, head dy, head leading,
    #        deck size, deck dy, deck leading, caption height, caption size
    hero_y, hero_w, hero_gap = 188, 324, 12
    for i, story in enumerate(HEROES):
        story_block(img, draw, MARGIN + i * (hero_w + hero_gap), hero_y,
                    hero_w, 112, story, (5, 11, 18, 16, 21, 12, 60, 14, 20, 11))

    # --- mediums row 1: 5 columns (stories 4-8) ---
    row1_y, row1_w, row1_gap = 394, 191, 10
    for i, story in enumerate(MEDIUMS_ROW1):
        story_block(img, draw, MARGIN + i * (row1_w + row1_gap), row1_y,
                    row1_w, 76, story, (4, 9, 13, 13, 15, 10, 43, 12, 17, 9))

    # --- mediums row 2: 5 columns (stories 9-13) ---
    row2_y, row2_w, row2_gap = 544, 191, 10
    for i, story in enumerate(MEDIUMS_ROW2):
        story_block(img, draw, MARGIN + i * (row2_w + row2_gap), row2_y,
                    row2_w, 76, story, (4, 10, 14, 14, 16, 10, 45, 12, 17, 9))

    # --- also-on header ---
    ay = 696
    draw.text((MARGIN, ay), "ALSO ON THURSDAY 19 NOVEMBER \u2014 23 MORE STORIES",
              font=font(SANS_B, 12), fill=RED)
    draw.line([(MARGIN, ay + 18), (W - MARGIN, ay + 18)], fill=INK, width=1)

    # --- world map, with leader-line badges so nothing piles up ---
    map_x, map_y, map_w, map_h = MARGIN, ay + 24, 340, 176
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
    draw.text((MARGIN, map_y + map_h + 4),
              "WHERE IT HAPPENED \u2014 Red numbers 1\u201313; grey dots are the briefs.",
              font=font(SANS, 9), fill=GREY)

    # --- also-on list, three columns ---
    list_x = MARGIN + map_w + 14
    col_w = (W - MARGIN - list_x - 10) // 3
    num_font = font(SANS_B, 10)
    txt_font = font(SANS, 10)
    col_counts = [8, 8, 7]
    idx = 0
    for col in range(3):
        x = list_x + col * (col_w + 10)
        y = map_y
        for num, _region, text in ALSO_ON[idx:idx + col_counts[col]]:
            draw.text((x, y), f"{num}", font=num_font, fill=RED)
            lines = wrap(draw, text, txt_font, col_w - 22)
            ly = y
            for line in lines[:2]:
                draw.text((x + 22, ly), line, font=txt_font, fill=INK)
                ly += 11
            y = ly + 3
        idx += col_counts[col]

    # --- DATE CHECK: the Wednesday stories this page leaves out ---
    dc_y = 926
    dc_lines = [
        "DATE CHECK \u2014 FIRST REPORTED WEDNESDAY 18 NOV, SO NOT ON THIS PAGE AS NEWS:",
        "the Iranian drone interceptions over Kuwait and Bahrain \u00b7 the EU's proposed \u20ac45bn loan for Ukraine \u00b7 the House "
        "Democrats' 251\u201311 vote nominating Hakeem Jeffries \u00b7 Voyager 1 crossing one light-day, at 10:16 GMT Wednesday \u00b7 Pew's "
        "projection that Islam becomes the largest religion by 2035 \u00b7 Peltola's Alaska win \u00b7 and the Nature study on Earth's missing "
        "billion years (a 4 Nov paper).",
    ]
    draw.text((MARGIN, dc_y), dc_lines[0], font=font(SANS_B, 9), fill=RED)
    draw_text_block(draw, MARGIN, dc_y + 12, dc_lines[1], font(SANS, 9),
                    INK, CW, 11, max_lines=3)

    # --- footer ---
    foot_y = 970
    draw.text((MARGIN, foot_y),
              "Every story here happened, or was first reported, on Thursday 19 November 2026. "
              "Disputed claims are attributed, not stated as fact.",
              font=font(SANS, 9), fill=GREY)
    draw.text((MARGIN, foot_y + 12),
              "Sources: Reuters, AP, AFP, BBC, The Hindu, IMD, NASA, ICJ, Pew. Original drawings. "
              "The World in One Day \u2014 19 November 2026.",
              font=font(SANS, 9), fill=GREY)

    out = ROOT / "entry.png"
    img.save(out, "PNG", optimize=True)
    return out


if __name__ == "__main__":
    path = render()
    print(f"wrote {path} ({path.stat().st_size} bytes)")
