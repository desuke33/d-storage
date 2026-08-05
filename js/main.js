/* =========================================================
   d-storage.me  —  main.js
   プレーンJS（ライブラリなし）
   1) フッターの年号を自動更新
   2) 母艦タイルをスクロールでふわっと出現
   3) アクアリウム：かわいい魚がスクロールに付いてくる＋泡が昇る
   ========================================================= */

// ---- 1) フッターの年号を自動更新 ----------------------------------------
document.querySelectorAll('#year').forEach(function (el) {
  el.textContent = new Date().getFullYear();
});

// 「動きを減らす」設定なら、装飾アニメーションは一切動かさない
var prefersReduced =
  window.matchMedia &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// ---- 2) タイルをスクロールでふわっと出現 --------------------------------
(function revealTiles() {
  var items = document.querySelectorAll('.tiles li');
  if (!items.length) return;

  if (prefersReduced || !('IntersectionObserver' in window)) {
    items.forEach(function (li) { li.classList.add('is-visible'); });
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry, i) {
      if (entry.isIntersecting) {
        // 少しずつ時間差をつけて水中から浮かび上がるように
        var delay = (entry.target.dataset.index || 0) * 70;
        setTimeout(function () {
          entry.target.classList.add('is-visible');
        }, delay % 500);
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  items.forEach(function (li, i) {
    li.dataset.index = i;
    io.observe(li);
  });
})();

// ---- 3) アクアリウム -----------------------------------------------------
(function aquarium() {
  if (prefersReduced) return;

  var stage = document.querySelector('.aquarium');
  if (!stage) return;

  var W = window.innerWidth;
  var H = window.innerHeight;

  // かわいい魚のSVG（丸みのある体＋ひれ＋つぶらな目）。色は水中トーン。
  function fishSVG(scale, color) {
    return (
      '<svg width="' + (72 * scale) + '" height="' + (44 * scale) + '" viewBox="0 0 72 44" fill="none" aria-hidden="true">' +
        '<path d="M50 22c0-9-9-16-21-16C16 6 6 12 6 22s10 16 23 16c12 0 21-7 21-16z" fill="' + color + '"/>' +
        '<path d="M50 22c6-5 10-8 16-9-3 5-3 13 0 18-6-1-10-4-16-9z" fill="' + color + '" opacity="0.9"/>' +
        '<path d="M30 6c2-4 6-6 10-6-1 4-1 8 0 11-4-2-8-3-10-5z" fill="' + color + '" opacity="0.55"/>' +
        '<path d="M30 38c2 4 6 6 10 6-1-4-1-8 0-11-4 2-8 3-10 5z" fill="' + color + '" opacity="0.55"/>' +
        '<circle cx="17" cy="19" r="3.4" fill="#0b3d91"/>' +
        '<circle cx="16" cy="18" r="1.1" fill="#fff"/>' +
      '</svg>'
    );
  }

  var palette = [
    'rgba(56,189,248,0.85)',   // 水色
    'rgba(30,99,208,0.72)',    // 青
    'rgba(125,211,252,0.9)',   // 淡い水色
    'rgba(11,61,145,0.6)'      // 深い青
  ];

  var fishes = [];
  // 画面の広さに応じて魚の数を決める（詰め込みすぎない）
  var count = Math.max(4, Math.min(8, Math.round(W / 220)));

  for (var i = 0; i < count; i++) {
    var el = document.createElement('div');
    el.className = 'fish';

    var scale = 0.55 + Math.random() * 0.9;
    var color = palette[i % palette.length];
    el.innerHTML = fishSVG(scale, color);

    var dir = Math.random() < 0.5 ? 1 : -1;         // 泳ぐ向き
    var f = {
      el: el,
      x: Math.random() * W,
      baseY: 60 + Math.random() * (H - 160),        // 基準の高さ
      y: 0,
      follow: 0,                                     // スクロール追従の遅れ（トレイル）
      speed: (0.25 + Math.random() * 0.5) * dir,     // 横方向の速さ
      dir: dir,
      amp: 8 + Math.random() * 18,                   // 上下のゆらぎ幅
      phase: Math.random() * Math.PI * 2,
      wobble: 0.6 + Math.random() * 0.8,             // ゆらぎの速さ
      width: 72 * scale
    };
    fishes.push(f);
    stage.appendChild(el);

    // ふわっと出現
    (function (node) {
      setTimeout(function () { node.classList.add('is-swimming'); }, 200 + i * 160);
    })(el);
  }

  // スクロール追従：スクロール量の変化を「引っぱり」として魚に伝える。
  // 魚は少し遅れて付いてくる（トレイル）ので「着いてくる」感じになる。
  var lastScroll = window.pageYOffset;
  var pull = 0;
  window.addEventListener('scroll', function () {
    var now = window.pageYOffset;
    var delta = now - lastScroll;
    lastScroll = now;
    // 一気に引っぱられすぎないよう上限をつける
    pull += Math.max(-60, Math.min(60, delta));
  }, { passive: true });

  window.addEventListener('resize', function () {
    W = window.innerWidth;
    H = window.innerHeight;
  });

  var t = 0;
  function tick() {
    t += 0.016;
    // 引っぱりは時間とともに水の抵抗で減衰させる
    pull *= 0.9;

    for (var i = 0; i < fishes.length; i++) {
      var f = fishes[i];

      // 横に泳ぐ（画面外に出たら反対側から回り込む）
      f.x += f.speed;
      if (f.speed > 0 && f.x > W + f.width) f.x = -f.width;
      if (f.speed < 0 && f.x < -f.width)  f.x = W + f.width;

      // スクロール追従：目標の追従量へゆっくり近づける（＝遅れて付いてくる）
      // 大きい魚ほどゆったり、小さい魚ほど機敏に。
      var target = pull * (0.5 + (1 - f.width / 130));
      f.follow += (target - f.follow) * 0.06;

      // 上下のやわらかなゆらぎ
      var bob = Math.sin(t * f.wobble + f.phase) * f.amp;
      f.y = f.baseY + bob + f.follow;

      // 進行方向に顔を向ける（左向きは水平反転）
      var flip = f.speed < 0 ? -1 : 1;
      f.el.style.transform =
        'translate(' + f.x + 'px,' + f.y + 'px) scaleX(' + flip + ')';
    }
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);

  // ---- 泡：たまに下からゆっくり昇る -------------------------------------
  function spawnBubble() {
    var b = document.createElement('div');
    b.className = 'bubble';
    var size = 6 + Math.random() * 16;
    b.style.width = size + 'px';
    b.style.height = size + 'px';
    var startX = Math.random() * W;
    var drift = (Math.random() - 0.5) * 80;   // 昇りながら左右に少し流れる
    var dur = 6000 + Math.random() * 6000;
    stage.appendChild(b);

    var start = null;
    function rise(ts) {
      if (start === null) start = ts;
      var p = (ts - start) / dur;             // 0 → 1
      if (p >= 1) { b.remove(); return; }
      var x = startX + drift * p;
      var y = -(H + 80) * p;                   // 下から上へ
      // 途中で一番濃く、上端でふっと消える
      b.style.opacity = String(Math.sin(p * Math.PI) * 0.55);
      b.style.transform = 'translate(' + x + 'px,' + y + 'px)';
      requestAnimationFrame(rise);
    }
    requestAnimationFrame(rise);
  }
  // 3秒に1回くらい、控えめに
  setInterval(spawnBubble, 3000);
  spawnBubble();
})();
