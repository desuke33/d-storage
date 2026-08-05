# d-storage.com — だいすけの個人サイト

名刺代わりの個人サイト。1枚のトップページ(母艦)から、体験・学習・好きなもの・信じるもの・GitHub・連絡先・AI向け入口(llms.txt)へ辿れる構成。

- コンセプト: 白基調 × 優雅な青 × 透明感（グラスモーフィズム）
- 参考: Brittany Chiang（1ページ母艦）× TAMURA Ikuho（サイズ固定の画像タイル）
- 技術: プレーン HTML / CSS / JavaScript（静的サイト）

## フォルダ構成
```
d-storage/
├── index.html          母艦（7タイル）
├── llms.txt            AI向け自己紹介
├── robots.txt          クローラ向け案内
├── sitemap.xml         サイトマップ
├── CNAME               独自ドメイン(d-storage.com)設定
├── css/style.css       共通スタイル（テーマ変数あり）
├── js/main.js          最小限の動き
├── images/tiles/       タイル画像（SVGプレースホルダ）
├── assets/             favicon / OGP
└── pages/              下層ページ（体験/学習/好きなもの/信じるもの/連絡先）
```

## ローカルでの確認方法
このフォルダを web ルートとして静的サーバで開く（例）:
```bash
python -m http.server 8000
```
→ ブラウザで http://localhost:8000/ を開く。

## タイルを増やすには
`index.html` の `<ul class="tiles">` 内の `<li>...</li>` を複製し、
`images/tiles/` に画像を追加、`pages/` に遷移先ページを足すだけ。

## 今後の予定
- [ ] ローカル(C:\dev\d-storage)へ移設し Git 管理
- [ ] GitHub リポジトリ作成 → GitHub Pages で公開
- [ ] 独自ドメイン d-storage.com を接続（DNS設定）
- [ ] プレースホルダを実コンテンツ・実写真へ差し替え
- [ ] GitHub API で活動を1タイルに表示（任意）
