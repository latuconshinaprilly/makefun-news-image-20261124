#!/usr/bin/env python3
"""THE TUESDAY SIGNAL — Akun 18 (@latuconshinaprilly3480), NI24 Wave 1.
Fresh compose engine written in this session for this account only.
Renders a one-day newspaper front page (Tuesday 24 November 2026) at
W=3000, then fits it whole into a 1024x1024 canvas on page-white and
quantizes to 256 colours. Usage: python3 compose.py [--variant A|B]
--out <png>. All facts come from ni24-pool.md + ni24-pool-refresh-0700.md
(the locked master number table); no numbers are invented here.
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = "/usr/share/fonts/truetype/dejavu"

# ---------------------------------------------------------------- palette
INK = (14, 22, 44)          # midnight blue ink
NAVY = (26, 44, 88)
STEEL = (74, 100, 144)
SILVER = (178, 186, 198)
PAPER = (251, 251, 247)
CARD_BG = (255, 255, 255)
RULE = (196, 178, 120)      # pale gold rule
RED = (166, 30, 30)
GOLD = (150, 116, 44)
MUTED = (92, 96, 108)
REGION_COLORS = {
    "EUROPE": (26, 44, 88),
    "MIDDLE EAST": (146, 64, 32),
    "AMERICAS": (30, 96, 62),
    "ASIA-PACIFIC": (128, 32, 96),
    "OCEANIA": (16, 110, 130),
    "AFRICA": (150, 110, 20),
    "WORLD": (82, 82, 92),
}
SCENE_BG = {
    "football": (30, 96, 62), "cricket": (116, 90, 40), "capitol": (26, 44, 88),
    "ship": (24, 66, 110), "sea": (30, 88, 122), "city": (52, 58, 74),
    "climate": (28, 96, 96), "bank": (88, 70, 28), "skyline": (60, 52, 74),
    "desert": (150, 110, 52), "gold": (176, 141, 44), "bitcoin": (196, 120, 24),
    "nightcity": (20, 24, 52), "vote": (96, 32, 64), "chip": (26, 44, 88),
}

# ---------------------------------------------------------------- fonts
def _font(name, size):
    p = os.path.join(FONT_DIR, name)
    if not os.path.isfile(p):
        p = os.path.join(FONT_DIR, "DejaVuSans.ttf")
    return ImageFont.truetype(p, size)

def fonts():
    return {
        "mast": _font("DejaVuSerif-Bold.ttf", 168),
        "date": _font("DejaVuSerif-Bold.ttf", 104),
        "kick": _font("DejaVuSans-Bold.ttf", 46),
        "deck": _font("DejaVuSans-Oblique.ttf", 46),
        "h1": _font("DejaVuSans-Bold.ttf", 50),
        "h2": _font("DejaVuSans-Bold.ttf", 40),
        "body": _font("DejaVuSans.ttf", 38),
        "body2": _font("DejaVuSans.ttf", 30),
        "small": _font("DejaVuSans.ttf", 30),
        "tag": _font("DejaVuSans-Bold.ttf", 28),
        "tags": _font("DejaVuSans-Bold.ttf", 24),
        "num": _font("DejaVuSans-Bold.ttf", 62),
        "numlab": _font("DejaVuSans-Bold.ttf", 30),
        "pin": _font("DejaVuSans-Bold.ttf", 34),
        "brief": _font("DejaVuSans.ttf", 34),
        "briefn": _font("DejaVuSans-Bold.ttf", 34),
    }

# ---------------------------------------------------------------- data
# Cards: (num, region, place, headline, deck, chip, scene, tag, lon, lat)
CARDS = [
    (1, "EUROPE", "FOOTBALL — LIVERPOOL",
     "Liverpool 4–0 Man Utd",
     "Yoro sent off in the 8th minute; United down to 10 men. "
     "Defeat leaves United 19th on 8 points; Pochettino debut disaster.",
     "4–0", "football", "REPORTED · Mint / NextSportsWeb · 23 Nov",
     -3.0, 53.4),
    (2, "OCEANIA", "CRICKET — WELLINGTON",
     "New Zealand bat out a draw with India",
     "NZ 239/5 — Mitchell 49* off 186, Phillips 26* off 126; "
     "63-run stand, 258 balls. India 720/9d; "
     "2nd Test Christchurch 27 Nov–1 Dec.",
     "DRAW · 239/5", "cricket", "REPORTED · HS / WicketPulse / QNC · 23 Nov",
     174.8, -41.3),
    (3, "AMERICAS", "POLITICS — WASHINGTON",
     "Trump: work with Democrats to cap card rates",
     "Trump would work with Democrats to cap card rates "
     "and scrap the debt ceiling. Van Hollen vs Schumer; "
     "secret ballot 1 Dec.",
     "RATE CAP", "capitol", "REPORTED · ActiveInvestorMag · 23 Nov",
     -77.0, 38.9),
    (4, "EUROPE", "WAR — BENGHAZI, LIBYA",
     "Ukraine sinks Russian warship Merkury off Libya",
     "7 sea drones launched; corvette sunk at Benghazi; "
     "Ka-27 destroyed; MV Angara hit.",
     "7 SEA DRONES", "ship", "REPORTED · CNN / AP · 23 Nov",
     20.1, 32.1),
    (5, "EUROPE", "SEA — GULF OF FINLAND",
     "Russian cargo ship Sparta II hit, towed clear",
     "Hit Saturday; all 16 crew off; the 121 m ship was "
     "towed out of Finnish waters Sunday.",
     "16 CREW SAFE", "sea", "REPORTED · Reuters · 22–23 Nov",
     25.0, 60.0),
    (6, "EUROPE", "WAR — KYIV REGION",
     "Kyiv strikes kill at least 15",
     "11 killed in a Dymer flats block; drone hit a 6-floor "
     "Kyiv building Monday, 5 hurt.",
     "15 KILLED", "city", "REPORTED · Times / AP · 23 Nov",
     30.5, 50.4),
    (7, "WORLD", "CLIMATE — ANTALYA, TÜRKIYE",
     "COP31 ends with no deal — first since 2000",
     "Final text dropped fossil fuels; 44 h overtime, "
     "longest COP ever; COP32 Addis 2027.",
     "NO DEAL", "climate", "REPORTED · Guardian · 23 Nov",
     30.7, 36.9),
    (8, "MIDDLE EAST", "SANCTIONS — WASHINGTON",
     "Iran sanctions: US hits ~30 exchange houses",
     "Treasury Mon: ~30 houses + executives; shadow-banking "
     "core evading Iran bank curbs.",
     "~30 SANCTIONED", "bank", "REPORTED · AP · 23 Nov",
     -77.0, 38.9),
    (9, "MIDDLE EAST", "CONFLICT — GAZA CITY",
     "Israeli strikes kill 3 in Gaza",
     "3 killed Monday, incl. a UNRWA employee; Shifa Hospital "
     "and the agency confirm.",
     "3 KILLED", "skyline", "REPORTED · AP · 23 Nov",
     34.5, 31.5),
    (10, "MIDDLE EAST", "WAR — WESTERN YEMEN",
     "Strike kills 11 in western Yemen",
     "Houthis: Saudi-backed strike Monday killed 11, "
     "wounded 19 in western Yemen.",
     "11 KILLED", "desert", "REPORTED · AP · 23 Nov",
     44.0, 15.5),
    (11, "AMERICAS", "MARKETS",
     "Gold rebounds 1.5% to $3,588",
     "Bullion +1.5% Mon after worst week in 8 months; "
     "PCE report due 25 Nov; yield 4.96%.",
     "$3,588/OZ", "gold", "REPORTED · Reuters · 23 Nov",
     -0.1, 51.5),
    (12, "WORLD", "CRYPTO",
     "Bitcoin steadies near $61,284",
     "$61,284 Mon 12:52 UTC, +1.1% 24 h; weekend low "
     "~$55,100; Kraken CAD crash ~$17,000.",
     "$61,284", "bitcoin", "REPORTED · CoinPaprika · 23 Nov",
     -74.0, 40.7),
    (13, "AMERICAS", "BUSINESS — LOS ANGELES",
     "GTA VI takes $3.8bn on day one",
     "Biggest entertainment launch on record — past every "
     "game launch and film opening day.",
     "$3.8BN", "nightcity", "REPORTED · ActiveInvestor · 23 Nov",
     -118.2, 34.0),
    (14, "AMERICAS", "POLITICS — WASHINGTON",
     "Democrats take both chambers",
     "Largest House majority since 1992, 258–173; "
     "Van Hollen vs Schumer ballot 1 Dec.",
     "258–173", "vote", "REPORTED · BBC · 23 Nov",
     -77.0, 38.9),
    (15, "AMERICAS", "MARKETS — NEW YORK",
     "Nvidia brings back Jensen Huang as CEO",
     "Board reinstates Huang effective Mon; shares +31%; "
     "Nasdaq +6%, S&P 500 +5%.",
     "+31%", "chip", "REPORTED · Reuters · 23 Nov",
     -122.0, 37.4),
]

BRIEFS = [
    (16, "ASIA-PACIFIC", "Nepal PM Balendra Shah ends Delhi state visit; met Modi Monday (IANS, 23 Nov)"),
    (17, "EUROPE", "Thousands march in Lisbon over cost of living (JagranJosh, 23 Nov)"),
    (18, "EUROPE", "UK–EU Brexit reset deal: Burnham calls it “landmark” to parliament (BBC, 23 Nov)"),
    (19, "ASIA-PACIFIC", "India–EU free-trade pact likely signed 16 Dec in Brussels (JagranJosh, 23 Nov)"),
    (20, "ASIA-PACIFIC", "Tata Steel sells pipe business to APL Apollo, ₹28,000 crore (ObserverVoice, 23 Nov)"),
    (21, "ASIA-PACIFIC", "SpiceJet pilot seeks urgent financial + safety audit; IndiGo holds 65.9% domestic share (ObserverVoice, 23 Nov)"),
    (22, "ASIA-PACIFIC", "IFFI 2026 hosts BRICS Roundtable in Goa (ObserverVoice, 23 Nov)"),
    (23, "ASIA-PACIFIC", "Modi inaugurates AI Centre at IIT Patna + ₹400 crore research projects (ObserverVoice, 23 Nov)"),
    (24, "ASIA-PACIFIC", "Amit Shah launches ₹4,000 crore infra push in Arunachal Pradesh (ObserverVoice, 23 Nov)"),
    (25, "ASIA-PACIFIC", "JEE Main 2027 Session 1 registration closes today (JagranJosh, 23 Nov)"),
    (26, "ASIA-PACIFIC", "NEET PG 2026: 10,105 medical seats flagged blocked (JagranJosh, 23 Nov)"),
    (27, "ASIA-PACIFIC", "Google invests $5m in AI research at IIT Kharagpur (JagranJosh, 23 Nov)"),
    (28, "AMERICAS", "US stocks fall again as AI shares swing; Nasdaq 100 futures +3% Monday (AP, 23 Nov)"),
    (29, "AMERICAS", "Morgan Stanley’s Wilson most bullish on stocks since April: sell-off a “fat pitch” (ActiveInvestorMag, 23 Nov)"),
    (30, "AMERICAS", "Goldman sees +18% S&P 500 through 2027, Brent $88, gold $4,650 (ActiveInvestorMag, 23 Nov)"),
    (31, "ASIA-PACIFIC", "KOSPI falls ~3% Monday to 10-month low; Taiwan steadies (Reuters, 23 Nov)"),
    (32, "AMERICAS", "Mets + A.J. Ewing agree $95m, 8-year deal (AP, 23 Nov)"),
    (33, "AMERICAS", "Miley Cyrus marries Maxx Morando in California (BBC, 23 Nov)"),
    (34, "WORLD", "Solana launches solana.ai, a platform for autonomous AI agents (Gadgets360, 23 Nov)"),
    (35, "WORLD", "Chainflip offers attacker behind $12m theft a 10% bounty; deadline 23 Nov (Gadgets360, 23 Nov)"),
    (36, "ASIA-PACIFIC", "Coinbase, CoinDCX, ZebPay report INR withdrawal delays (Gadgets360, 23 Nov)"),
    (37, "ASIA-PACIFIC", "HKMA explores AI agents to trace crypto crime as stablecoins dominate illicit flows (HK News TV, 23 Nov)"),
    (38, "ASIA-PACIFIC", "Hong Kong CPI rises 2.2% year on year in October (HK News TV, 23 Nov)"),
    (39, "AMERICAS", "FBI probes hack of its crime database; Washington State pauses van-dealer checks (AP, 23 Nov)"),
    (40, "ASIA-PACIFIC", "North Korea weighs shutting Swiss diplomatic office in Pyongyang (KCNA / Reuters, 24 Nov 04:24 WIB)"),
    (41, "MIDDLE EAST", "US discussing military training for Syrian forces, first since 2024; demining focus (Reuters, 23 Nov)"),
    (42, "AFRICA", "Congo halts cobalt exports from 30 Nov until further notice (Reuters, 23 Nov)"),
    (43, "ASIA-PACIFIC", "Indonesia: 24 killed in factory blaze, rescuers search for dozens missing (Reuters, 23 Nov)"),
    (44, "AMERICAS", "CrowdStrike snaps up Zscaler in $44bn deal as cyber threats mount (Reuters, 23 Nov)"),
]

NUMBERS = [
    ("7", "SEA DRONES — MERKURY SUNK"),
    ("4–0", "LIVERPOOL BEAT MAN UTD"),
    ("239/5", "WELLINGTON DRAW"),
    ("+31%", "NVIDIA — HUANG BACK"),
    ("$3,588", "GOLD, +1.5% MONDAY"),
    ("$61,284", "BITCOIN"),
    ("$3.8BN", "GTA VI DAY ONE"),
    ("258–173", "HOUSE MAJORITY"),
]

RAIL = [
    ("7", "sea drones launched"),
    ("15", "killed near Kyiv, 11 in Dymer"),
    ("44 h", "COP31 overtime, longest ever"),
    ("~30", "Iran houses sanctioned"),
    ("720/9", "India 720/9 — draw 239/5"),
    ("121 m", "Sparta II towed out Sun"),
]

TIMELINE = [
    ("MON 23 NOV · 00:02 UTC", "UN AI weapons: states agree to keep negotiating"),
    ("MON 23 NOV · 12:52 UTC", "Bitcoin $61,284 — CoinPaprika morning quote"),
    ("MON 23 NOV · 16:29 UTC", "Reuters live: Nvidia reinstates Jensen Huang as CEO"),
    ("MON 23 NOV · EVENING", "Zelenskyy announces Merkury sinking; Treasury sanctions Iran"),
    ("MON 23 NOV · NIGHT", "Sparta II towed out; COP31 ends, Antalya Pact dead"),
    ("TUE 24 NOV · 04:24 WIB", "KCNA: North Korea weighs shutting Swiss office"),
]

DATECHECK = [
    "186-drone night over Ukraine, 161 downed — Fri 21–Sun 22 Nov",
    "Hong Kong Election Committee results: 856 candidates, 723 seats — Sun 22 Nov",
    "Alcaraz beats Zverev 6–2, 7–6(9–7), first ATP Finals title — Sun 22 Nov",
    "Verstappen wins Las Vegas Grand Prix — Sun 22 Nov",
    "Wembanyama scores 50, Spurs 114–91 Pelicans — Sun 22 Nov",
    "Myanmar ICJ genocide ruling — Thu 19 Nov",
    "Nvidia SEC probe, first reported — Fri 20 Nov",
    "Jensen Huang resigns as Nvidia CEO after affair admission — Thu 12 Nov",
]

REGION_ORDER = ["EUROPE", "MIDDLE EAST", "AMERICAS", "ASIA-PACIFIC", "AFRICA", "OCEANIA", "WORLD"]

def region_counts():
    counts = {r: 0 for r in REGION_ORDER}
    for c in CARDS:
        counts[c[1]] += 1
    for b in BRIEFS:
        counts[b[1]] += 1
    return counts

# ---------------------------------------------------------------- helpers
def wrap(d, text, font, maxw):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def center(d, y, text, font, fill, cx, maxw=None):
    if maxw:
        lines = wrap(d, text, font, maxw)
        for ln in lines:
            d.text((cx - d.textlength(ln, font=font) / 2, y), ln, font=font, fill=fill)
            y += int(font.size * 1.18)
        return y
    d.text((cx - d.textlength(text, font=font) / 2, y), text, font=font, fill=fill)
    return y + int(font.size * 1.18)

def rule(d, x0, x1, y, fill=RULE, w=4):
    d.line([(x0, y), (x1, y)], fill=fill, width=w)

# ---------------------------------------------------------------- scenes
def paint_scene(d, box, kind):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    bg = SCENE_BG[kind]
    d.rectangle(box, fill=bg)
    # horizon band
    d.rectangle([x0, y0 + int(h * 0.62), x1, y1], fill=tuple(max(0, v - 26) for v in bg))
    cx, cy = x0 + w // 2, y0 + h // 2
    if kind == "football":
        d.rectangle([x0 + 30, y0 + 40, x0 + 130, y0 + 150], outline=(255, 255, 255), width=6)
        d.ellipse([x0 + w - 190, y0 + 60, x0 + w - 110, y0 + 140], fill=(255, 255, 255))
        d.text((x0 + 40, y0 + h - 150), "4–0", font=_font("DejaVuSans-Bold.ttf", 120),
               fill=(255, 255, 255))
        for i in range(5):
            d.line([(x0 + 200 + i * 110, y0 + 30), (x0 + 200 + i * 110, y1 - 30)],
                   fill=(200, 220, 200), width=3)
    elif kind == "cricket":
        d.rectangle([x0 + w // 2 - 14, y0 + 30, x0 + w // 2 + 14, y1 - 30], fill=(214, 186, 110))
        d.ellipse([x0 + w - 200, y0 + 50, x0 + w - 130, y0 + 120], fill=(178, 32, 32))
        d.text((x0 + 40, y0 + h - 150), "239/5", font=_font("DejaVuSans-Bold.ttf", 110),
               fill=(255, 255, 255))
        for i in range(3):
            d.line([(x0 + 60 + i * 26, y0 + h - 60), (x0 + 60 + i * 26, y0 + h - 110)],
                   fill=(255, 255, 255), width=8)
    elif kind == "capitol":
        d.polygon([(cx - 200, y0 + h - 60), (cx - 200, y0 + 150), (cx - 120, y0 + 90),
                   (cx - 60, y0 + 60), (cx, y0 + 40), (cx + 60, y0 + 60),
                   (cx + 120, y0 + 90), (cx + 200, y0 + 150), (cx + 200, y0 + h - 60)],
                  fill=(235, 235, 228))
        d.rectangle([cx - 260, y0 + h - 60, cx + 260, y0 + h - 40], fill=(235, 235, 228))
        d.text((x0 + 40, y0 + 30), "CAP", font=_font("DejaVuSans-Bold.ttf", 92),
               fill=(255, 255, 255))
    elif kind == "ship":
        d.polygon([(x0 + 60, y0 + h - 120), (x0 + 160, y0 + h - 120), (x0 + w - 160, y0 + h - 120),
                   (x0 + w - 60, y0 + h - 60), (x0 + 120, y0 + h - 60)], fill=(18, 20, 30))
        d.rectangle([x0 + 120, y0 + 60, x0 + 170, y0 + h - 120], fill=(18, 20, 30))
        for i in range(7):
            d.ellipse([x0 + 220 + i * 70, y0 + 40 + (i % 2) * 40,
                       x0 + 250 + i * 70, y0 + 70 + (i % 2) * 40], fill=(255, 210, 60))
        for i in range(4):
            d.arc([x0 + 60 + i * 150, y0 + h - 70, x0 + 210 + i * 150, y0 + h + 10],
                  180, 360, fill=(255, 255, 255), width=5)
    elif kind == "sea":
        for i in range(4):
            d.arc([x0 + 40 + i * 170, y0 + 60 + (i % 2) * 50, x0 + 240 + i * 170,
                   y0 + 170 + (i % 2) * 50], 180, 360, fill=(255, 255, 255), width=6)
        d.polygon([(x0 + 80, y0 + h - 110), (x0 + 200, y0 + h - 110), (x0 + w - 200, y0 + h - 110),
                   (x0 + w - 80, y0 + h - 50), (x0 + 140, y0 + h - 50)], fill=(250, 240, 210))
        d.line([(x0 + w - 420, y0 + h - 110), (x0 + w - 60, y0 + h - 110)],
               fill=(250, 240, 210), width=8)
    elif kind == "city":
        for i, bh in enumerate([120, 190, 150, 210, 130, 170]):
            bx = x0 + 50 + i * 110
            d.rectangle([bx, y0 + h - 60 - bh, bx + 90, y0 + h - 60], fill=(20, 22, 34))
            for wy in range(3):
                d.rectangle([bx + 18, y0 + h - 90 - bh + wy * 45, bx + 40,
                             y0 + h - 70 - bh + wy * 45], fill=(255, 210, 90))
        d.ellipse([x0 + w - 180, y0 + 40, x0 + w - 100, y0 + 120], fill=(255, 120, 60))
    elif kind == "climate":
        d.ellipse([cx - 130, y0 + 40, cx + 130, y0 + 300], fill=(120, 190, 160))
        d.arc([cx - 130, y0 + 40, cx + 130, y0 + 300], 0, 360, fill=(255, 255, 255), width=6)
        for i in range(5):
            d.line([(x0 + 60 + i * 130, y0 + h - 90), (x0 + 60 + i * 130, y0 + h - 150)],
                   fill=(255, 255, 255), width=10)
        d.ellipse([x0 + w - 170, y0 + 50, x0 + w - 90, y0 + 130], fill=(255, 210, 60))
    elif kind == "bank":
        for i in range(5):
            d.rectangle([x0 + 60 + i * 130, y0 + 90, x0 + 130 + i * 130, y0 + h - 70],
                        fill=(235, 228, 200))
        d.polygon([(x0 + 30, y0 + 90), (cx, y0 + 20), (x0 + w - 30, y0 + 90)],
                  fill=(235, 228, 200))
        d.rectangle([x0 + 30, y0 + h - 70, x0 + w - 30, y0 + h - 45], fill=(235, 228, 200))
    elif kind == "skyline":
        for i, bh in enumerate([100, 160, 120, 180, 110]):
            bx = x0 + 60 + i * 130
            d.rectangle([bx, y0 + h - 60 - bh, bx + 100, y0 + h - 60], fill=(24, 26, 40))
        d.ellipse([cx - 70, y0 + 30, cx + 70, y0 + 170], fill=(255, 200, 90))
    elif kind == "desert":
        d.polygon([(x0, y0 + h - 60), (x0 + 200, y0 + 90), (x0 + 420, y0 + h - 60)],
                  fill=(120, 84, 40))
        d.polygon([(x0 + 300, y0 + h - 60), (x0 + 520, y0 + 60), (x0 + w - 60, y0 + h - 60)],
                  fill=(96, 66, 32))
        d.ellipse([x0 + w - 190, y0 + 40, x0 + w - 100, y0 + 130], fill=(255, 220, 130))
    elif kind == "gold":
        for i in range(3):
            d.polygon([(x0 + 90 + i * 200, y0 + h - 80), (x0 + 120 + i * 200, y0 + h - 160),
                       (x0 + 260 + i * 200, y0 + h - 160), (x0 + 290 + i * 200, y0 + h - 80)],
                      fill=(255, 214, 90))
        d.ellipse([x0 + w - 200, y0 + 40, x0 + w - 110, y0 + 130], fill=(255, 230, 120))
        d.text((x0 + 40, y0 + 30), "$", font=_font("DejaVuSans-Bold.ttf", 110),
               fill=(255, 240, 180))
    elif kind == "bitcoin":
        d.ellipse([cx - 120, y0 + 30, cx + 120, y0 + 270], fill=(255, 190, 60))
        d.text((cx - 52, y0 + 70), "B", font=_font("DejaVuSans-Bold.ttf", 150),
               fill=(120, 60, 0))
        for i in range(3):
            d.rectangle([x0 + 60 + i * 40, y0 + h - 90, x0 + 90 + i * 40, y0 + h - 40],
                        fill=(255, 255, 255))
    elif kind == "nightcity":
        for i, bh in enumerate([150, 220, 180, 240, 160, 200]):
            bx = x0 + 40 + i * 110
            d.rectangle([bx, y0 + h - 60 - bh, bx + 88, y0 + h - 60], fill=(8, 10, 26))
            d.rectangle([bx + 20, y0 + h - 90 - bh, bx + 44, y0 + h - 70 - bh],
                        fill=(255, 220, 100))
        d.polygon([(x0 + 60, y0 + h - 40), (x0 + 130, y0 + h - 90), (x0 + 200, y0 + h - 40)],
                  fill=(200, 40, 60))
        d.ellipse([x0 + w - 180, y0 + 40, x0 + w - 110, y0 + 110], fill=(220, 220, 235))
    elif kind == "vote":
        d.rectangle([x0 + 60, y0 + 50, x0 + w - 60, y0 + h - 120], fill=(240, 240, 235))
        d.rectangle([x0 + 90, y0 + 80, x0 + 200, y0 + 190], fill=(26, 44, 88))
        d.text((x0 + 110, y0 + 90), "✓", font=_font("DejaVuSans-Bold.ttf", 84),
               fill=(255, 255, 255))
        d.line([(x0 + 240, y0 + 120), (x0 + w - 100, y0 + 120)], fill=(26, 44, 88), width=10)
        d.line([(x0 + 240, y0 + 165), (x0 + w - 140, y0 + 165)], fill=(26, 44, 88), width=10)
    elif kind == "chip":
        d.rectangle([x0 + 90, y0 + 60, x0 + w - 90, y0 + h - 70], fill=(10, 14, 30))
        for i in range(4):
            d.line([(x0 + 90, y0 + 100 + i * 45), (x0 + 30, y0 + 100 + i * 45)],
                   fill=(255, 255, 255), width=8)
            d.line([(x0 + w - 90, y0 + 100 + i * 45), (x0 + w - 30, y0 + 100 + i * 45)],
                   fill=(255, 255, 255), width=8)
        d.polygon([(cx - 40, y0 + 90), (cx + 110, y0 + 90), (cx + 110, y0 + 130),
                   (cx - 10, y0 + 130), (cx - 10, y0 + 210), (cx + 60, y0 + 210),
                   (cx + 60, y0 + 250), (cx - 40, y0 + 250)], fill=(60, 200, 90))
        d.text((x0 + 40, y0 + h - 110), "+31%", font=_font("DejaVuSans-Bold.ttf", 96),
               fill=(120, 230, 140))

def paint_mini_scene(d, box, kind):
    """Compact flat scene for the 118 px mini strips (fractional coords)."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    bg = SCENE_BG[kind]
    d.rectangle(box, fill=bg)
    d.rectangle([x0, y0 + int(h * 0.62), x1, y1], fill=tuple(max(0, v - 26) for v in bg))
    cx = x0 + w // 2
    big = _font("DejaVuSans-Bold.ttf", 64)
    if kind == "football":
        d.rectangle([x0 + 24, y0 + 14, x0 + 110, y0 + 66], outline=(255, 255, 255), width=5)
        d.ellipse([x0 + w - 90, y0 + 16, x0 + w - 40, y0 + 66], fill=(255, 255, 255))
        d.text((x0 + w - 260, y0 + 30), "4–0", font=big, fill=(255, 255, 255))
    elif kind == "cricket":
        d.rectangle([cx - 12, y0 + 10, cx + 12, y1 - 10], fill=(214, 186, 110))
        d.ellipse([x0 + w - 100, y0 + 18, x0 + w - 52, y0 + 66], fill=(178, 32, 32))
        d.text((x0 + 24, y0 + 30), "239/5", font=big, fill=(255, 255, 255))
    elif kind == "capitol":
        d.polygon([(cx - 150, y1 - 12), (cx - 150, y0 + 62), (cx - 80, y0 + 34),
                   (cx, y0 + 16), (cx + 80, y0 + 34), (cx + 150, y0 + 62),
                   (cx + 150, y1 - 12)], fill=(235, 235, 228))
    elif kind == "ship":
        d.polygon([(x0 + 60, y0 + h - 34), (x0 + 140, y0 + h - 34), (x0 + w - 140, y0 + h - 34),
                   (x0 + w - 60, y0 + h - 12), (x0 + 110, y0 + h - 12)], fill=(18, 20, 30))
        d.rectangle([x0 + 110, y0 + 16, x0 + 140, y0 + h - 34], fill=(18, 20, 30))
        for i in range(7):
            d.ellipse([x0 + 200 + i * 52, y0 + 14 + (i % 2) * 22,
                       x0 + 222 + i * 52, y0 + 36 + (i % 2) * 22], fill=(255, 210, 60))
    elif kind == "sea":
        for i in range(3):
            d.arc([x0 + 40 + i * 190, y0 + 22, x0 + 210 + i * 190, y0 + 100],
                  180, 360, fill=(255, 255, 255), width=5)
        d.polygon([(x0 + 80, y0 + h - 30), (x0 + 180, y0 + h - 30), (x0 + w - 180, y0 + h - 30),
                   (x0 + w - 80, y0 + h - 10), (x0 + 130, y0 + h - 10)], fill=(250, 240, 210))
    elif kind == "city":
        for i, bh in enumerate([44, 70, 54, 78, 48]):
            bx = x0 + 40 + i * 120
            d.rectangle([bx, y1 - 12 - bh, bx + 92, y1 - 12], fill=(20, 22, 34))
        d.ellipse([x0 + w - 110, y0 + 14, x0 + w - 58, y0 + 66], fill=(255, 120, 60))
    elif kind == "climate":
        d.ellipse([cx - 52, y0 + 12, cx + 52, y0 + 116], fill=(120, 190, 160))
        d.ellipse([x0 + w - 100, y0 + 16, x0 + w - 52, y0 + 64], fill=(255, 210, 60))
    elif kind == "bank":
        for i in range(5):
            d.rectangle([x0 + 50 + i * 120, y0 + 40, x0 + 110 + i * 120, y1 - 14],
                        fill=(235, 228, 200))
        d.polygon([(x0 + 30, y0 + 40), (cx, y0 + 10), (x0 + w - 30, y0 + 40)],
                  fill=(235, 228, 200))
    elif kind == "skyline":
        for i, bh in enumerate([40, 62, 48, 70, 44]):
            bx = x0 + 50 + i * 120
            d.rectangle([bx, y1 - 12 - bh, bx + 94, y1 - 12], fill=(24, 26, 40))
        d.ellipse([cx - 30, y0 + 12, cx + 30, y0 + 72], fill=(255, 200, 90))
    elif kind == "desert":
        d.polygon([(x0, y1 - 12), (x0 + 180, y0 + 44), (x0 + 380, y1 - 12)],
                  fill=(120, 84, 40))
        d.polygon([(x0 + 280, y1 - 12), (x0 + 480, y0 + 30), (x0 + w - 40, y1 - 12)],
                  fill=(96, 66, 32))
        d.ellipse([x0 + w - 110, y0 + 14, x0 + w - 62, y0 + 62], fill=(255, 220, 130))
    elif kind == "gold":
        for i in range(3):
            d.polygon([(x0 + 80 + i * 170, y1 - 16), (x0 + 105 + i * 170, y1 - 66),
                       (x0 + 215 + i * 170, y1 - 66), (x0 + 240 + i * 170, y1 - 16)],
                      fill=(255, 214, 90))
        d.text((x0 + w - 130, y0 + 16), "$", font=big, fill=(255, 240, 180))
    elif kind == "bitcoin":
        d.ellipse([cx - 52, y0 + 10, cx + 52, y0 + 114], fill=(255, 190, 60))
        d.text((cx - 24, y0 + 26), "B", font=_font("DejaVuSans-Bold.ttf", 62),
               fill=(120, 60, 0))
    elif kind == "nightcity":
        for i, bh in enumerate([56, 84, 66, 90, 60]):
            bx = x0 + 40 + i * 120
            d.rectangle([bx, y1 - 12 - bh, bx + 92, y1 - 12], fill=(8, 10, 26))
            d.rectangle([bx + 22, y1 - 30 - bh, bx + 44, y1 - 14 - bh], fill=(255, 220, 100))
        d.ellipse([x0 + w - 110, y0 + 14, x0 + w - 62, y0 + 62], fill=(220, 220, 235))
    elif kind == "vote":
        d.rectangle([x0 + 50, y0 + 18, x0 + w - 50, y1 - 16], fill=(240, 240, 235))
        d.rectangle([x0 + 74, y0 + 34, x0 + 160, y0 + 100], fill=(26, 44, 88))
        d.text((x0 + 90, y0 + 36), "✓", font=_font("DejaVuSans-Bold.ttf", 52),
               fill=(255, 255, 255))
        d.line([(x0 + 200, y0 + 58), (x0 + w - 90, y0 + 58)], fill=(26, 44, 88), width=8)
        d.line([(x0 + 200, y0 + 88), (x0 + w - 130, y0 + 88)], fill=(26, 44, 88), width=8)
    elif kind == "chip":
        d.rectangle([x0 + 80, y0 + 18, x0 + w - 80, y1 - 16], fill=(10, 14, 30))
        d.polygon([(cx - 20, y0 + 34), (cx + 70, y0 + 34), (cx + 70, y0 + 58),
                   (cx - 4, y0 + 58), (cx - 4, y0 + 84), (cx + 34, y0 + 84),
                   (cx + 34, y0 + 104), (cx - 20, y0 + 104)], fill=(60, 200, 90))
        d.text((x0 + w - 190, y0 + 30), "+31%", font=big, fill=(120, 230, 140))

# ---------------------------------------------------------------- map
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 76), (-80, 73),
     (-65, 62), (-55, 52), (-60, 46), (-70, 42), (-75, 35), (-80, 26), (-85, 20),
     (-90, 15), (-95, 16), (-100, 20), (-105, 23), (-110, 28), (-115, 32), (-125, 40),
     (-125, 49), (-140, 60), (-155, 58), (-165, 60)],
    [(-80, 10), (-75, 10), (-70, 12), (-62, 10), (-52, 5), (-50, 0), (-40, -5),
     (-35, -8), (-40, -20), (-48, -28), (-55, -35), (-65, -40), (-70, -50), (-73, -55),
     (-73, -45), (-73, -35), (-70, -20), (-75, -15), (-80, -5), (-80, 5)],
    [(-17, 15), (-10, 30), (-5, 35), (10, 37), (20, 32), (30, 31), (35, 28),
     (40, 20), (43, 12), (48, 11), (51, 10), (44, 0), (40, -10), (35, -20),
     (32, -28), (26, -33), (20, -35), (15, -30), (12, -18), (9, -5), (9, 4),
     (-8, 5), (-15, 10)],
    [(-10, 36), (-9, 43), (-2, 48), (-5, 50), (0, 51), (5, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (24, 58), (28, 60), (30, 62), (35, 65), (40, 68),
     (50, 70), (60, 70), (70, 73), (80, 74), (90, 75), (100, 77), (110, 76),
     (120, 73), (130, 72), (140, 72), (150, 70), (160, 70), (170, 66), (178, 65),
     (170, 60), (162, 56), (158, 52), (150, 60), (142, 55), (140, 45), (135, 43),
     (130, 42), (127, 40), (122, 38), (120, 32), (115, 28), (110, 20), (108, 12),
     (105, 8), (100, 8), (97, 15), (95, 20), (92, 22), (88, 22), (85, 19),
     (80, 15), (77, 8), (75, 12), (72, 20), (68, 23), (65, 25), (60, 25),
     (57, 26), (55, 28), (52, 28), (50, 29), (48, 30), (50, 26), (55, 26),
     (56, 27), (58, 24), (60, 20), (58, 16), (55, 14), (52, 15), (48, 16),
     (45, 13), (43, 12), (40, 15), (38, 20), (35, 28), (33, 30), (30, 36),
     (27, 37), (23, 36), (20, 40), (18, 40), (15, 44), (12, 44), (8, 39),
     (3, 38), (0, 36), (-5, 36), (-9, 37)],
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51)],
    [(113, -22), (114, -30), (115, -35), (120, -34), (125, -32), (130, -32),
     (135, -35), (140, -38), (145, -38), (150, -37), (153, -32), (153, -27),
     (150, -23), (146, -19), (142, -15), (142, -11), (137, -12), (135, -15),
     (132, -12), (130, -13), (126, -14), (122, -17), (118, -20)],
    [(167, -45), (170, -42), (173, -40), (175, -38), (177, -38), (174, -41),
     (171, -43), (168, -46)],
    [(130, 31), (132, 33), (135, 34), (137, 35), (139, 36), (140, 38), (141, 41),
     (143, 43), (145, 44), (142, 42), (140, 39), (138, 37), (136, 35), (133, 34),
     (131, 32)],
    [(95, 5), (100, 0), (105, -5), (110, -7), (115, -8), (120, -10), (125, -9),
     (130, -5), (135, -4), (140, -8), (138, -6), (132, -2), (128, 0), (122, 2),
     (118, 0), (112, 3), (105, 2), (100, 5)],
]

def _inside(lon, lat, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > lat) != (yj > lat)) and \
                (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

def on_land(lon, lat):
    return any(_inside(lon, lat, p) for p in CONTINENTS)

def draw_map(d, box):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(232, 236, 242))
    d.rectangle(box, outline=NAVY, width=4)
    # dotted land: equirectangular, lon -180..180, lat -58..82
    step = 3.0
    lon = -178.0
    while lon < 180:
        lat = -56.0
        while lat < 82:
            if on_land(lon, lat):
                px = x0 + (lon + 180) / 360.0 * (x1 - x0)
                py = y0 + (82 - lat) / 140.0 * (y1 - y0)
                d.ellipse([px - 6, py - 6, px + 6, py + 6], fill=NAVY)
            lat += step
        lon += step
    # pins: number = card number; offset pins sharing Washington
    seen = {}
    for c in CARDS:
        num, lon, lat = c[0], c[8], c[9]
        key = (round(lon), round(lat))
        seen[key] = seen.get(key, 0) + 1
        off = (seen[key] - 1) * 34
        px = x0 + (lon + 180) / 360.0 * (x1 - x0) + off
        py = y0 + (82 - lat) / 140.0 * (y1 - y0) - (seen[key] - 1) * 26
        d.ellipse([px - 24, py - 24, px + 24, py + 24], fill=RED,
                  outline=(255, 255, 255), width=4)
        t = str(num)
        d.text((px - d.textlength(t, font=F["pin"]) / 2, py - 17), t,
               font=F["pin"], fill=(255, 255, 255))

F = None  # set in build()

# ---------------------------------------------------------------- cards
def draw_lead(d, c, box, variant):
    x0, y0, x1, y1 = box
    num, region, place, head, deck, chip, scene, tag = c[:8]
    d.rectangle(box, fill=CARD_BG, outline=INK, width=4)
    sh = 250
    paint_scene(d, (x0 + 4, y0 + 4, x1 - 4, y0 + 4 + sh), scene)
    # number badge over scene
    d.rectangle([x0 + 4, y0 + 4, x0 + 84, y0 + 84], fill=RED)
    d.text((x0 + 42 - d.textlength(str(num), font=F["num"]) / 2, y0 + 12),
           str(num), font=F["num"], fill=(255, 255, 255))
    y = y0 + 4 + sh + 18
    rc = REGION_COLORS[region]
    d.rectangle([x0 + 22, y, x0 + 52, y + 30], fill=rc)
    d.text((x0 + 64, y - 4), region + " · " + place, font=F["tag"], fill=rc)
    y += 44
    for ln in wrap(d, head, F["h1"], x1 - x0 - 44):
        d.text((x0 + 22, y), ln, font=F["h1"], fill=INK)
        y += 58
    y += 6
    for ln in wrap(d, deck, F["body"], x1 - x0 - 44):
        d.text((x0 + 22, y), ln, font=F["body"], fill=(40, 44, 56))
        y += 44
    # chip + tag pinned near bottom
    by = y1 - 84
    d.rectangle([x0 + 22, by, x0 + 22 + d.textlength(chip, font=F["tag"]) + 28, by + 40],
                fill=NAVY)
    d.text((x0 + 36, by + 5), chip, font=F["tag"], fill=(255, 255, 255))
    d.text((x0 + 22, by + 48), tag, font=F["small"], fill=MUTED)

def draw_mini(d, c, box):
    x0, y0, x1, y1 = box
    num, region, place, head, deck, chip, scene, tag = c[:8]
    d.rectangle(box, fill=CARD_BG, outline=INK, width=3)
    sh = 118
    paint_mini_scene(d, (x0 + 3, y0 + 3, x1 - 3, y0 + 3 + sh), scene)
    d.rectangle([x0 + 3, y0 + 3, x0 + 63, y0 + 63], fill=RED)
    d.text((x0 + 31 - d.textlength(str(num), font=F["pin"]) / 2, y0 + 13),
           str(num), font=F["pin"], fill=(255, 255, 255))
    y = y0 + 3 + sh + 12
    rc = REGION_COLORS[region]
    d.text((x0 + 18, y), region + " · " + place, font=F["tag"], fill=rc)
    y += 36
    for ln in wrap(d, head, F["h2"], x1 - x0 - 36)[:2]:
        d.text((x0 + 18, y), ln, font=F["h2"], fill=INK)
        y += 46
    for ln in wrap(d, deck, F["body2"], x1 - x0 - 36)[:2]:
        d.text((x0 + 18, y), ln, font=F["body2"], fill=(40, 44, 56))
        y += 34
    by = y1 - 32
    cw = d.textlength(chip, font=F["tag"]) + 22
    d.rectangle([x0 + 18, by, x0 + 18 + cw, by + 30], fill=NAVY)
    d.text((x0 + 29, by + 1), chip, font=F["tag"], fill=(255, 255, 255))
    tw = d.textlength(tag, font=F["tags"])
    d.text((x1 - 18 - tw, by + 3), tag, font=F["tags"], fill=MUTED)

# ---------------------------------------------------------------- page
def build(variant):
    global F
    F = fonts()
    W = 3000
    H = 5600
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    M = 90
    CW = W - 2 * M
    cx = W // 2
    y = 64

    total = len(CARDS) + len(BRIEFS)
    counts = region_counts()
    assert total == 44, total
    assert sum(counts.values()) == 44, counts

    # kicker
    kick = "44 STORIES · 7 REGIONS · EVERY ONE FROM TUESDAY 24 NOVEMBER 2026"
    center(d, y, kick, F["kick"], NAVY, cx)
    y += 78
    rule(d, M, W - M, y, fill=INK, w=6)
    y += 26

    # masthead
    mast = "THE TUESDAY SIGNAL"
    center(d, y, mast, F["mast"], INK, cx)
    y += 205
    # date line with flanking rules
    date = "Tuesday 24 November 2026"
    dw = d.textlength(date, font=F["date"])
    rule(d, M, cx - dw / 2 - 50, y + 55, fill=RULE, w=5)
    rule(d, cx + dw / 2 + 50, W - M, y + 55, fill=RULE, w=5)
    d.text((cx - dw / 2, y), date, font=F["date"], fill=NAVY)
    y += 140
    center(d, y, "The world in one image — every story dated, every number checked.",
           F["deck"], RED, cx)
    y += 78
    rule(d, M, W - M, y, fill=INK, w=6)
    y += 22

    # region strip
    d.text((M, y + 8), "WHERE THE NEWS CAME FROM", font=F["tag"], fill=INK)
    rx = M + 560
    for r in REGION_ORDER:
        lab = "%s %d" % (r, counts[r])
        wlab = d.textlength(lab, font=F["tag"]) + 46
        d.rectangle([rx, y, rx + wlab, y + 52], fill=REGION_COLORS[r])
        d.text((rx + 23, y + 10), lab, font=F["tag"], fill=(255, 255, 255))
        rx += wlab + 14
    y += 82
    rule(d, M, W - M, y, fill=RULE, w=4)
    y += 20

    # numbers strip
    nums = NUMBERS if variant == "A" else list(reversed(NUMBERS))
    bw = (CW - 7 * 16) // 8
    for i, (big, lab) in enumerate(nums):
        bx = M + i * (bw + 16)
        d.rectangle([bx, y, bx + bw, y + 168], fill=(255, 255, 255), outline=NAVY, width=3)
        center(d, y + 18, big, F["num"], NAVY, bx + bw // 2)
        for j, ln in enumerate(wrap(d, lab, F["numlab"], bw - 24)):
            d.text((bx + bw // 2 - d.textlength(ln, font=F["numlab"]) / 2, y + 96 + j * 36),
                   ln, font=F["numlab"], fill=MUTED)
    y += 190
    rule(d, M, W - M, y, fill=INK, w=4)
    y += 24

    # leads + rail (Layout C)
    leads = CARDS[:3] if variant == "A" else [CARDS[1], CARDS[0], CARDS[2]]
    rail_w = 700
    lead_w = (CW - rail_w - 60) // 3
    lead_h = 700
    for i, c in enumerate(leads):
        bx = M + i * (lead_w + 30)
        draw_lead(d, c, (bx, y, bx + lead_w, y + lead_h), variant)
    # rail
    rx0 = M + 3 * (lead_w + 30) + 30
    d.rectangle([rx0, y, rx0 + rail_w - 30, y + lead_h], fill=INK)
    d.text((rx0 + 34, y + 22), "THE DAY IN", font=F["kick"], fill=(255, 255, 255))
    d.text((rx0 + 34, y + 74), "NUMBERS", font=F["kick"], fill=(255, 255, 255))
    rule(d, rx0 + 34, rx0 + rail_w - 64, y + 140, fill=RULE, w=4)
    ry = y + 160
    for big, lab in RAIL:
        d.text((rx0 + 34, ry), big, font=F["num"], fill=(255, 214, 90))
        bw2 = d.textlength(big, font=F["num"])
        d.text((rx0 + 44 + bw2, ry + 14), lab, font=F["small"], fill=(235, 235, 235))
        ry += 74
    y += lead_h + 30
    rule(d, M, W - M, y, fill=INK, w=4)
    y += 24

    # minis 4 x 3
    minis = CARDS[3:] if variant == "A" else list(reversed(CARDS[3:]))
    mw = (CW - 3 * 30) // 4
    mh = 390
    for row in range(3):
        for col in range(4):
            c = minis[row * 4 + col]
            bx = M + col * (mw + 30)
            draw_mini(d, c, (bx, y, bx + mw, y + mh))
        y += mh + 24
    y -= 24
    y += 30
    rule(d, M, W - M, y, fill=INK, w=4)
    y += 24

    # map + timeline
    map_w = 1720
    tl_w = CW - map_w - 40
    sec_h = 560
    d.text((M, y), "WHERE IT HAPPENED — pins match story numbers",
           font=F["tag"], fill=INK)
    d.text((M + map_w + 40, y), "THE DAY IN UTC — Mon evening into Tue morning",
           font=F["tag"], fill=INK)
    y += 48
    draw_map(d, (M, y, M + map_w, y + sec_h))
    tx = M + map_w + 40
    d.rectangle([tx, y, tx + tl_w, y + sec_h], fill=(255, 255, 255), outline=INK, width=3)
    ty = y + 18
    for t, ev in TIMELINE:
        d.text((tx + 22, ty), t, font=F["tag"], fill=RED)
        ty += 38
        for ln in wrap(d, ev, F["body2"], tl_w - 44):
            d.text((tx + 22, ty), ln, font=F["body2"], fill=INK)
            ty += 38
        ty += 8
    y += sec_h + 30
    rule(d, M, W - M, y, fill=INK, w=4)
    y += 24

    # ALSO ON — 3 columns
    d.text((M, y), "ALSO ON — Tuesday 24 November 2026",
           font=F["kick"], fill=INK)
    y += 70
    cols = [BRIEFS[0:10], BRIEFS[10:20], BRIEFS[20:29]]
    col_w = (CW - 2 * 40) // 3
    max_by = y
    for ci, col in enumerate(cols):
        bx = M + ci * (col_w + 40)
        by = y
        for num, region, text in col:
            d.text((bx, by), str(num), font=F["briefn"], fill=RED)
            for ln in wrap(d, text, F["brief"], col_w - 64):
                d.text((bx + 56, by), ln, font=F["brief"], fill=(30, 32, 44))
                by += 42
            by += 10
        max_by = max(max_by, by)
    y = max_by + 20
    rule(d, M, W - M, y, fill=INK, w=4)
    y += 22

    # DATE CHECK
    d.rectangle([M, y, W - M, y + 330], fill=(255, 238, 238), outline=RED, width=4)
    d.text((M + 30, y + 18), "DATE CHECK — NOT TODAY’S NEWS. These happened earlier; they are not today’s stories.",
           font=F["tag"], fill=RED)
    dy = y + 66
    for i in range(0, len(DATECHECK), 2):
        for j in (0, 1):
            if i + j >= len(DATECHECK):
                continue
            bx = M + 30 + j * ((CW - 60) // 2)
            d.text((bx, dy), "✕  " + DATECHECK[i + j], font=F["body2"], fill=(90, 20, 20))
        dy += 56
    y += 330 + 24

    # footer
    d.text((M, y), "SOURCES: Reuters · AP · CNN · The Times · WSJ · BBC · Guardian · CoinPaprika · "
                  "Treasury · ActiveInvestorMag · IANS · JagranJosh · ObserverVoice · HK News TV · Gadgets360",
           font=F["small"], fill=MUTED)
    y += 40
    d.text((M, y), "CERTAINTY: REPORTED = first reported 22–24 Nov 2026, as cited per story · "
                  "CLAIM = as claimed by the named party · FORECAST = scheduled, not yet happened.",
           font=F["small"], fill=MUTED)
    y += 40
    d.text((M, y), "Pictures and map: original, drawn in code. Original drawings. — THE TUESDAY SIGNAL",
           font=F["small"], fill=MUTED)
    y += 60
    content_h = y

    page = img.crop((0, 0, W, content_h))
    # fit whole into 1024x1024 on page-white
    scale = 1024 / content_h
    nw = int(W * scale)
    small = page.resize((nw, 1024), Image.LANCZOS)
    out = Image.new("RGB", (1024, 1024), PAPER)
    ox = (1024 - nw) // 2
    out.paste(small, (ox, 0))
    d2 = ImageDraw.Draw(out)
    d2.rectangle([ox - 3, 0, ox + nw + 2, 1023], outline=INK, width=3)
    q = out.quantize(colors=256, method=Image.MEDIANCUT, dither=Image.NONE)
    return q, content_h

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="A")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    img, ch = build(args.variant)
    img.save(args.out, optimize=True, compress_level=9)
    print("variant %s content_h=%d bytes=%d" % (args.variant, ch, os.path.getsize(args.out)))

if __name__ == "__main__":
    main()
