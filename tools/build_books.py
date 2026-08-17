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
NOTES_DIR  = os.path.join(ROOT, "images", "books", "notes")
PAGES_DIR  = os.path.join(ROOT, "pages")
BOOKPAGES  = os.path.join(ROOT, "pages", "books")
CARD_SIZE  = 640

for d in (BOOKS_DIR, COVERS_DIR, CARDS_DIR, NOTES_DIR, BOOKPAGES):
    os.makedirs(d, exist_ok=True)

def optimize_note(name):
    """本文の付属写真をWeb用に縮小（最大1100px）。"""
    p = os.path.join(NOTES_DIR, name)
    if not os.path.exists(p): return
    try:
        im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
        w, h = im.size
        if max(w, h) > 1100:
            s = 1100 / max(w, h); im = im.resize((int(w * s), int(h * s)), Image.LANCZOS)
        im.save(p, "JPEG", quality=82, optimize=True, progressive=True)
    except Exception:
        pass

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
            "rating_num": meta.get("rating_num", ""), "genres": meta.get("genres", ""),
            "cover": meta.get("cover", ""), "photos": meta.get("photos", ""), "body": body.strip()}

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

def rating_num(b):
    if b.get("rating_num"):
        try: return int(b["rating_num"])
        except Exception: pass
    return b.get("rating", "").count("★")

def render_list(books):
    # ジャンル収集（絞込セレクト用）
    genset = []
    for b in books:
        for g in [x.strip() for x in b.get("genres", "").split(",") if x.strip()]:
            if g not in genset: genset.append(g)
    genset.sort()
    genre_opts = "".join(f'<option value="{html.escape(g)}">{html.escape(g)}</option>' for g in genset)

    cards = []
    for b in books:
        cards.append(f"""        <li class="book-card" data-date="{html.escape(b.get('date',''))}" data-rating="{rating_num(b)}" data-genres="{html.escape(b.get('genres',''))}">
          <a class="tile" href="/pages/books/{b['id']}.html">
            <img src="/images/books/cards/{b['id']}.jpg" alt="{html.escape(b['title'])} の表紙">
          </a>
          <span class="tile-label">{html.escape(b['title'])}</span>
        </li>""")

    controls = f"""      <div class="book-controls">
        <label>並び替え
          <select id="sortSel">
            <option value="date-desc">日付（新しい順）</option>
            <option value="date-asc">日付（古い順）</option>
            <option value="rating-desc">評価（高い順）</option>
            <option value="rating-asc">評価（低い順）</option>
          </select>
        </label>
        <label>評価
          <select id="ratingSel">
            <option value="0">すべて</option>
            <option value="5">★5</option>
            <option value="4">★4以上</option>
            <option value="3">★3以上</option>
            <option value="2">★2以上</option>
            <option value="1">★1以上</option>
          </select>
        </label>
        <label>ジャンル
          <select id="genreSel"><option value="">すべて</option>{genre_opts}</select>
        </label>
        <label>期間
          <input type="date" id="fromDate"> 〜 <input type="date" id="toDate">
        </label>
        <button id="resetBtn" type="button">リセット</button>
        <span id="countLabel" class="book-count"></span>
      </div>"""

    body = f"""{page_head('積読', '読んだ本と、その感想。')}
    <header class="page-header">
      <a class="back-link" href="/">← 母艦にもどる</a>
      <h1 class="page-title">積読</h1>
      <p class="page-lead">読んだ本と、その感想。並び替え・絞り込みができます。</p>
    </header>
    <main>
{controls}
      <ul class="tiles book-grid" id="bookGrid">
{os.linesep.join(cards) if cards else '        <li><p class="page-lead">まだ登録がありません。</p></li>'}
      </ul>
    </main>
    <script src="/js/books.js"></script>
{FOOT}"""
    open(os.path.join(PAGES_DIR, "tsundoku.html"), "w", encoding="utf-8").write(body)

def render_book(b):
    meta = " ・ ".join([x for x in [b.get("author",""), b.get("date",""), b.get("rating",""), b.get("genres","")] if x])
    photos = [p.strip() for p in b.get("photos", "").split(",") if p.strip()]
    for p in photos:
        optimize_note(p)
    aside = f'          <img class="book-cover" src="/images/books/cards/{b["id"]}.jpg" alt="{html.escape(b["title"])} の表紙">'
    for p in photos:
        aside += ('\n          <a class="book-photo-link" href="/images/books/notes/' + p + '" target="_blank" rel="noopener">'
                  '<img class="book-photo" src="/images/books/notes/' + p + '" alt="' + html.escape(b["title"]) + ' 本文の写真" loading="lazy"></a>')
    body = f"""{page_head(b['title'], b['title'] + ' の感想')}
    <header class="page-header">
      <a class="back-link" href="/pages/tsundoku.html">← 積読にもどる</a>
      <h1 class="page-title">{html.escape(b['title'])}</h1>
      <p class="page-lead">{html.escape(meta)}</p>
    </header>
    <main>
      <div class="book-detail">
        <aside class="book-aside">
{aside}
        </aside>
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
