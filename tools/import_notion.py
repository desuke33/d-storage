# -*- coding: utf-8 -*-
"""
Notion取込（データ担当）: Notionの読書データベースから
  - books/<ID>.md（front-matter＋感想本文＝ページ本文）を生成
  - ISBN から表紙画像を自動取得（openBD → Google Books）して images/books/covers/ に保存
その後 build_books.py を実行すればサイトに反映される。

秘密情報（トークン）は tools/.env に置く（.gitignore 済み・リポジトリには入らない）:
    NOTION_TOKEN=secret_xxx
    NOTION_DB=データベースID（32桁）

使い方:  python tools/import_notion.py   （続けて python tools/build_books.py）
"""
import os, re, json, unicodedata, urllib.request, urllib.parse

ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS_DIR  = os.path.join(ROOT, "books")
COVERS_DIR = os.path.join(ROOT, "images", "books", "covers")
os.makedirs(BOOKS_DIR, exist_ok=True)
os.makedirs(COVERS_DIR, exist_ok=True)

# ---- .env 読み込み（KEY=VALUE） ----
def load_env():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
load_env()
TOKEN = os.environ.get("NOTION_TOKEN", "")
DB    = os.environ.get("NOTION_DB", "")
NOTION_HEADERS = {"Authorization": "Bearer " + TOKEN, "Notion-Version": "2022-06-28"}

# ---- HTTP ヘルパ ----
def http_json(url, headers=None, body=None, method="GET"):
    data = json.dumps(body).encode() if body is not None else None
    h = dict(headers or {})
    if body is not None: h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def download(url, dst):
    req = urllib.request.Request(url, headers={"User-Agent": "d-storage-bot"})
    with urllib.request.urlopen(req, timeout=30) as r:
        open(dst, "wb").write(r.read())
    return dst

# ---- Notion プロパティ抽出 ----
def prop(props, *names):
    """名前候補（大文字小文字無視）で最初に一致したプロパティを返す"""
    low = {k.lower(): v for k, v in props.items()}
    for n in names:
        if n.lower() in low:
            return low[n.lower()]
    return None

def read_text(p):
    if not p: return ""
    t = p.get("type")
    if t == "title":     return "".join(x.get("plain_text","") for x in p["title"])
    if t == "rich_text": return "".join(x.get("plain_text","") for x in p["rich_text"])
    if t == "select":    return (p["select"] or {}).get("name","") if p.get("select") else ""
    if t == "status":    return (p["status"] or {}).get("name","") if p.get("status") else ""
    if t == "number":    return str(p.get("number") or "")
    if t == "date":      return (p["date"] or {}).get("start","") if p.get("date") else ""
    if t == "url":       return p.get("url") or ""
    if t == "multi_select": return ", ".join(x["name"] for x in p.get("multi_select",[]))
    return ""

# ---- 本文ブロック → Markdown ----
def rich_to_md(rich):
    s = ""
    for r in rich:
        t = r.get("plain_text","")
        if r.get("annotations",{}).get("bold"): t = f"**{t}**"
        s += t
    return s

def fetch_blocks_md(page_id):
    lines, cursor = [], None
    while True:
        url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
        if cursor: url += "&start_cursor=" + cursor
        j = http_json(url, NOTION_HEADERS)
        for b in j.get("results", []):
            bt = b.get("type"); data = b.get(bt, {})
            text = rich_to_md(data.get("rich_text", []))
            if bt == "paragraph":                 lines.append(text)
            elif bt in ("heading_1","heading_2","heading_3"): lines.append("**" + text + "**")
            elif bt == "bulleted_list_item":       lines.append("・" + text)
            elif bt == "numbered_list_item":       lines.append("・" + text)
            elif bt == "quote":                    lines.append("> " + text)
            elif bt == "to_do":
                lines.append(("[x] " if data.get("checked") else "[ ] ") + text)
            elif bt == "divider":                  lines.append("---")
            elif text:                             lines.append(text)
        if j.get("has_more"): cursor = j.get("next_cursor")
        else: break
    return "\n\n".join(lines).strip()

# ---- 表紙自動取得（ISBN → openBD → Google Books） ----
def fetch_cover(isbn, id_):
    if not isbn: return False
    isbn = re.sub(r"[^0-9Xx]", "", isbn)
    dst = os.path.join(COVERS_DIR, id_ + ".jpg")
    try:
        j = http_json(f"https://api.openbd.jp/v1/get?isbn={isbn}")
        if j and j[0]:
            cov = (j[0].get("summary") or {}).get("cover") or ""
            if cov:
                download(cov, dst); return True
    except Exception: pass
    try:
        j = http_json(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}")
        items = j.get("items", [])
        if items:
            links = items[0].get("volumeInfo", {}).get("imageLinks", {})
            url = links.get("thumbnail") or links.get("smallThumbnail")
            if url:
                download(url.replace("http://", "https://"), dst); return True
    except Exception: pass
    return False

# ---- ID（URL用の安定名） ----
def make_id(id_prop, isbn, page_id):
    if id_prop: return re.sub(r"[^0-9A-Za-z_\-]", "-", id_prop)
    if isbn:    return "isbn-" + re.sub(r"[^0-9Xx]", "", isbn)
    return page_id.replace("-", "")[:12]

def query_db():
    results, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor: body["start_cursor"] = cursor
        j = http_json(f"https://api.notion.com/v1/databases/{DB}/query",
                      NOTION_HEADERS, body=body, method="POST")
        results += j.get("results", [])
        if j.get("has_more"): cursor = j.get("next_cursor")
        else: break
    return results

def main():
    if not TOKEN or not DB:
        print("!! tools/.env に NOTION_TOKEN と NOTION_DB を設定してください。")
        return
    pages = query_db()
    n_cover = n_book = 0
    for pg in pages:
        props = pg.get("properties", {})
        title  = read_text(prop(props, "Title", "名前", "書名", "Name"))
        if not title: continue
        status = read_text(prop(props, "Status", "ステータス", "状態"))
        # 読了のみ公開（ステータスが無ければ全部）
        if status and status not in ("読了", "Done", "完了", "読み終わった"): continue
        author = read_text(prop(props, "Author", "著者"))
        isbn   = read_text(prop(props, "ISBN", "ISBN13"))
        rating = read_text(prop(props, "Rating", "評価", "★"))
        date   = read_text(prop(props, "Read", "読了日", "Date", "日付"))
        idprop = read_text(prop(props, "ID", "Slug", "スラッグ"))
        bid    = make_id(idprop, isbn, pg["id"])

        body = fetch_blocks_md(pg["id"])
        fm = ["---", f"title: \"{title}\""]
        if author: fm.append(f"author: \"{author}\"")
        if date:   fm.append(f"date: \"{date}\"")
        if rating: fm.append(f"rating: \"{rating}\"")
        fm.append("---")
        open(os.path.join(BOOKS_DIR, bid + ".md"), "w", encoding="utf-8").write(
            "\n".join(fm) + "\n\n" + body + "\n")
        n_book += 1
        if fetch_cover(isbn, bid): n_cover += 1
        print(f"  ・{bid}  {title}  (表紙:{'OK' if isbn else '—'})")

    print(f"\n取込: {n_book}冊 / 表紙自動取得: {n_cover}冊")
    print("続けて:  python tools/build_books.py  でサイトに反映")

if __name__ == "__main__":
    main()
