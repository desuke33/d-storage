# -*- coding: utf-8 -*-
"""
積読ビルダー（描画担当）: books/*.md から静的ページを生成する。
  - pages/tsundoku.html         … 本のカード一覧（ホームと同じカード形式）
  - pages/books/<ID>.html       … 各本の感想ページ（あなたの文章をそのまま表示）
  - images/books/cards/<ID>.jpg … 正方形のカード画像（表紙を四角形に）

データ元は books/<ID>.md（Notion取込= import_notion.py が生成 / 手書きも可）。
使い方:  python tools/build_books.py
"""
import os, re, glob, html
from PIL import Image, ImageOps, ImageFilter, ImageDraw, ImageFont, ImageEnhance

ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS_DIR  = os.path.join(ROOT, "books")
COVERS_DIR = os.path.join(ROOT, "images", "books", "covers")
CARDS_DIR  = os.path.join(ROOT, "images", "books", "cards")
PAGES_DIR  = os.path.join(ROOT, "pages")
BOOKPAGES  = os.path.join(ROOT, "pages", "books")
CARD_SIZE  = 640

for d in (BOOKS_DIR, COVERS_DIR, CARDS_DIR, BOOKPAGES):
    os.makedirs(d, exist_ok=True)

def jp_font(size):
    for name in ("meiryo.ttc", "YuGothM.ttc", "YuGothR.ttc", "msgothic.ttc"):
        p = os.path.join(r"C:\Windows\Fonts", name)
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

def parse_book(path):
    raw = open(path, encoding="utf-8").read()
    meta, body = {}, raw
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", raw, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"')
        body = m.group(2)
    bid = os.path.splitext(os.path.basename(path))[0]
    return {"id": bid, "title": meta.get("title", bid), "author": meta.get("author", ""),
            "date": meta.get("date", ""), "rating": meta.get("rating", ""),
            "cover": meta.get("cover", ""), "body": body.strip()}

def md_to_html(md):
    out = []
    for block in re.split(r"\n\s*\n", md.strip()):
        if not block.strip(): continue
        esc = html.escape(block)
        esc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc)
        esc = esc.replace("\n", "<br>\n")
        out.append("<p>" + esc + "</p>")
    return "\n".join(out) if out else '<p class="placeholder-note">（感想はまだありません）</p>'

def make_card_image(book):
    bid, title = book["id"], book["title"]
    dst = os.path.join(CARDS_DIR, bid + ".jpg")
    src = None
    cand = ([os.path.join(COVERS_DIR, book["cover"])] if book["cover"] else [])
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".JPG", ".PNG"):
        cand.append(os.path.join(COVERS_DIR, bid + ext))
    for c in cand:
        if os.path.exists(c): src = c; break
    S = CARD_SIZE
    if src:
        cov = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        bg = ImageOps.fit(cov, (S, S), Image.LANCZOS).filter(ImageFilter.GaussianBlur(20))
        bg = ImageEnhance.Brightness(bg).enhance(0.55)
        fg = cov.copy(); fg.thumbnail((int(S*0.80), int(S*0.90)), Image.LANCZOS)
        x, y = (S - fg.width)//2, (S - fg.height)//2
        sh = Image.new("RGBA", (S, S), (0,0,0,0))
        ImageDraw.Draw(sh).rectangle([x-6,y-6,x+fg.width+6,y+fg.height+6], fill=(0,0,0,90))
        sh = sh.filter(ImageFilter.GaussianBlur(10))
        canvas = bg.convert("RGBA"); canvas.alpha_composite(sh); canvas.paste(fg, (x, y))
        canvas.convert("RGB").save(dst, "JPEG", quality=84, optimize=True, progressive=True)
        return False
    else:
        img = Image.new("RGB", (S, S)); d = ImageDraw.Draw(img)
        for i in range(S):
            t = i/S
            d.line([(0,i),(S,i)], fill=(int(11+40*t), int(61+60*t), int(145+60*t)))
        f = jp_font(34); fs = jp_font(24); lines=[]; cur=""
        for ch in list(title):
            if d.textlength(cur+ch, font=f) > S-80: lines.append(cur); cur=ch
            else: cur += ch
        lines.append(cur); lines = lines[:6]
        ty = S//2 - len(lines)*24
        for ln in lines:
            w = d.textlength(ln, font=f); d.text(((S-w)/2, ty), ln, font=f, fill=(255,255,255)); ty += 52
        note = "表紙 自動取得できず"; w = d.textlength(note, font=fs)
        d.text(((S-w)/2, S-70), note, font=fs, fill=(210,225,255))
        img.save(dst, "JPEG", quality=84, optimize=True, progressive=True)
        return True

def page_head(title, desc=""):
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)} | D-STORAGE</title>
  <meta name="description" content="{html.escape(desc)}">
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="/css/style.css">
</head>
<body>
  <div class="wrap">"""

FOOT = """    <footer class="site-footer">
      <p>&copy; <span id="year">2026</span> D-STORAGE / d-storage.me</p>
    </footer>
  </div>
  <script src="/js/main.js"></script>
</body>
</html>
"""

def render_list(books):
    cards = []
    for b in books:
        cards.append(f"""        <li>
          <a class="tile" href="/pages/books/{b['id']}.html">
            <img src="/images/books/cards/{b['id']}.jpg" alt="{html.escape(b['title'])} の表紙">
          </a>
          <span class="tile-label">{html.escape(b['title'])}</span>
        </li>""")
    body = f"""{page_head('積読', '読んだ本と、その感想。')}
    <header class="page-header">
      <a class="back-link" href="/">← 母艦にもどる</a>
      <h1 class="page-title">積読</h1>
      <p class="page-lead">読んだ本と、その感想。カードをクリックすると感想が開きます。</p>
    </header>
    <main>
      <ul class="tiles">
{os.linesep.join(cards) if cards else '        <li><p class="page-lead">まだ登録がありません。</p></li>'}
      </ul>
    </main>
{FOOT}"""
    open(os.path.join(PAGES_DIR, "tsundoku.html"), "w", encoding="utf-8").write(body)

def render_book(b):
    meta = " ・ ".join([x for x in [b.get("author",""), b.get("date",""), b.get("rating","")] if x])
    body = f"""{page_head(b['title'], b['title'] + ' の感想')}
    <header class="page-header">
      <a class="back-link" href="/pages/tsundoku.html">← 積読にもどる</a>
      <h1 class="page-title">{html.escape(b['title'])}</h1>
      <p class="page-lead">{html.escape(meta)}</p>
    </header>
    <main>
      <div class="book-detail">
        <img class="book-cover" src="/images/books/cards/{b['id']}.jpg" alt="{html.escape(b['title'])} の表紙">
        <article class="book-review card">
{md_to_html(b['body'])}
        </article>
      </div>
    </main>
{FOOT}"""
    open(os.path.join(BOOKPAGES, b["id"] + ".html"), "w", encoding="utf-8").write(body)

def main():
    paths = sorted(glob.glob(os.path.join(BOOKS_DIR, "*.md")))
    books = [parse_book(p) for p in paths]
    missing = []
    for b in books:
        if make_card_image(b): missing.append(b)
        render_book(b)
    render_list(books)
    print(f"生成: {len(books)}冊 -> pages/tsundoku.html, pages/books/*.html, images/books/cards/*.jpg")
    if missing:
        print("\n[表紙を自動取得できなかった本（プレースホルダで生成）]")
        for b in missing:
            print(f"   - {b['id']} \u300c{b['title']}\u300d -> images/books/covers/{b['id']}.jpg に手動で置けば反映")
    else:
        print("すべての本に表紙あり。")

if __name__ == "__main__":
    main()
