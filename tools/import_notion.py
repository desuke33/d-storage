# -*- coding: utf-8 -*-
"""
Notion取込（データ担当）: Notion「読書記録」DBから
  - books/<ID>.md（front-matter＋感想＝あなたの文章そのまま）を生成
  - 表紙を自動取得（「画像」列のファイル → 無ければ ISBN/タイトルで Web検索）
    → images/books/covers/ に保存
その後 build_books.py でサイトに反映。

秘密情報は tools/.env（.gitignore済み）:
    NOTION_TOKEN=...
    NOTION_DB=...
使い方:  python tools/import_notion.py  →  python tools/build_books.py
"""
import os, re, json, urllib.request

ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS_DIR  = os.path.join(ROOT, "books")
COVERS_DIR = os.path.join(ROOT, "images", "books", "covers")
os.makedirs(BOOKS_DIR, exist_ok=True)
os.makedirs(COVERS_DIR, exist_ok=True)

def load_env():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip())
load_env()
TOKEN = os.environ.get("NOTION_TOKEN", "")
DB    = os.environ.get("NOTION_DB", "")
NH = {"Authorization": "Bearer " + TOKEN, "Notion-Version": "2022-06-28"}

def http_json(url, headers=None, body=None, method="GET"):
    data = json.dumps(body).encode() if body is not None else None
    h = dict(headers or {})
    if body is not None: h["Content-Type"] = "application/json"
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h, method=method), timeout=30) as r:
        return json.load(r)

def download(url, dst):
    req = urllib.request.Request(url, headers={"User-Agent": "d-storage-bot"})
    with urllib.request.urlopen(req, timeout=30) as r:
        open(dst, "wb").write(r.read())

def prop(props, *names):
    low = {k.lower(): v for k, v in props.items()}
    for n in names:
        if n.lower() in low: return low[n.lower()]
    return None

def read_text(p):
    if not p: return ""
    t = p.get("type")
    if t == "title":     return "".join(x.get("plain_text","") for x in p["title"])
    if t == "rich_text": return "".join(x.get("plain_text","") for x in p["rich_text"])
    if t == "select":    return (p.get("select") or {}).get("name","")
    if t == "status":    return (p.get("status") or {}).get("name","")
    if t == "number":    return str(p.get("number") or "")
    if t == "date":      return (p.get("date") or {}).get("start","")
    if t == "url":       return p.get("url") or ""
    if t == "multi_select": return ", ".join(x["name"] for x in p.get("multi_select", []))
    return ""

# 感想が rich_text プロパティで長い場合の完全取得（25runs超の切り詰め対策）
def full_property_text(page_id, prop_obj):
    pid = prop_obj.get("id")
    if not pid: return read_text(prop_obj)
    url = f"https://api.notion.com/v1/pages/{page_id}/properties/{urllib.parse.quote(pid)}"
    try:
        parts, cursor = [], None
        while True:
            u = url + (f"?start_cursor={cursor}" if cursor else "")
            j = http_json(u, NH)
            if j.get("object") == "list":
                for it in j.get("results", []):
                    rt = it.get("rich_text") or it.get("title")
                    if rt: parts.append(rt.get("plain_text", ""))
                if j.get("has_more"): cursor = j.get("next_cursor"); continue
            break
        s = "".join(parts)
        return s if s else read_text(prop_obj)
    except Exception:
        return read_text(prop_obj)

import urllib.parse  # noqa

def cover_from_files(props, id_):
    p = prop(props, "画像", "Cover", "表紙", "Image")
    if p and p.get("type") == "files":
        for f in p.get("files", []):
            ft = f.get("type")
            url = f.get(ft, {}).get("url") if ft in ("file", "external") else None
            if url:
                try:
                    download(url, os.path.join(COVERS_DIR, id_ + ".jpg")); return True
                except Exception: pass
    return False

def cover_by_search(title, author, id_):
    q = urllib.parse.quote((title + " " + author).strip())
    try:
        j = http_json(f"https://www.googleapis.com/books/v1/volumes?q={q}&maxResults=1")
        items = j.get("items", [])
        if items:
            links = items[0].get("volumeInfo", {}).get("imageLinks", {})
            url = links.get("thumbnail") or links.get("smallThumbnail")
            if url:
                download(url.replace("http://", "https://"), os.path.join(COVERS_DIR, id_ + ".jpg")); return True
    except Exception: pass
    return False

def query_db():
    out, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor: body["start_cursor"] = cursor
        j = http_json(f"https://api.notion.com/v1/databases/{DB}/query", NH, body=body, method="POST")
        out += j.get("results", [])
        if j.get("has_more"): cursor = j.get("next_cursor")
        else: break
    return out

def main():
    if not TOKEN or not DB:
        print("!! tools/.env に NOTION_TOKEN と NOTION_DB を設定してください。"); return
    rows = query_db()
    n_book = n_cov = 0
    for pg in rows:
        props = pg.get("properties", {})
        title = read_text(prop(props, "名前", "Title", "書名", "Name"))
        if not title: continue
        status = read_text(prop(props, "Status", "ステータス", "状態"))
        if status and status not in ("読了", "Done", "完了"): continue
        author = read_text(prop(props, "著者名", "Author", "著者"))
        rating = read_text(prop(props, "評価", "Rating", "★"))
        date   = read_text(prop(props, "日付", "Read", "読了日", "Date"))
        kanso_p = prop(props, "感想", "Review", "レビュー")
        body = full_property_text(pg["id"], kanso_p) if kanso_p else ""
        bid = pg["id"].replace("-", "")

        fm = ["---", f'title: "{title}"']
        if author: fm.append(f'author: "{author}"')
        if date:   fm.append(f'date: "{date}"')
        if rating: fm.append(f'rating: "{rating}"')
        fm.append("---")
        open(os.path.join(BOOKS_DIR, bid + ".md"), "w", encoding="utf-8").write(
            "\n".join(fm) + "\n\n" + (body or "") + "\n")
        n_book += 1

        got = cover_from_files(props, bid) or cover_by_search(title, author, bid)
        if got: n_cov += 1
        print(f"  ・{title}  表紙:{'OK' if got else '—'}")

    print(f"\n取込 {n_book}冊 / 表紙 {n_cov}冊")
    print("次: python tools/build_books.py")

if __name__ == "__main__":
    main()
