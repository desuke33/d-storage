/* =========================================================
   d-storage.me  —  main.js
   最小限の動き（プレーンJS、ライブラリなし）
   ========================================================= */

// フッターの年号を自動更新
document.querySelectorAll('#year').forEach(function (el) {
  el.textContent = new Date().getFullYear();
});

// タイルのホバー演出（軽いズーム）は CSS 側で実装。JSでの装飾は不要。


/* =========================================================
   相棒の白いモフモフ犬（画面下に常駐・カーソルに追従）
   ========================================================= */
(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var svg =
    '<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">' +
      '<g class="dog-bob">' +
        '<g class="dog-tail"><path d="M34 68 Q10 60 15 40 Q26 54 37 60 Z" fill="#ffffff" stroke="#dcd2c2" stroke-width="2"/></g>' +
        '<rect x="44" y="92" width="10" height="20" rx="5" fill="#ffffff" stroke="#dcd2c2" stroke-width="2"/>' +
        '<rect x="70" y="92" width="10" height="20" rx="5" fill="#ffffff" stroke="#dcd2c2" stroke-width="2"/>' +
        '<ellipse cx="60" cy="78" rx="34" ry="26" fill="#ffffff" stroke="#dcd2c2" stroke-width="2"/>' +
        '<circle cx="40" cy="72" r="12" fill="#ffffff"/><circle cx="60" cy="66" r="13" fill="#ffffff"/><circle cx="80" cy="74" r="11" fill="#ffffff"/>' +
        '<circle cx="90" cy="60" r="20" fill="#ffffff" stroke="#dcd2c2" stroke-width="2"/>' +
        '<path d="M78 46 L74 26 L91 42 Z" fill="#ffffff" stroke="#dcd2c2" stroke-width="2"/>' +
        '<path d="M100 45 L109 29 L104 47 Z" fill="#ffffff" stroke="#dcd2c2" stroke-width="2"/>' +
        '<circle cx="86" cy="58" r="2.6" fill="#3a2a15"/><circle cx="97" cy="58" r="2.6" fill="#3a2a15"/>' +
        '<ellipse cx="99" cy="66" rx="3.4" ry="2.6" fill="#3a2a15"/>' +
        '<path d="M95 71 Q99 74 103 71" fill="none" stroke="#3a2a15" stroke-width="1.6" stroke-linecap="round"/>' +
      '</g>' +
    '</svg>';
  var dog = document.createElement('div');
  dog.id = 'buddy-dog';
  dog.setAttribute('aria-hidden', 'true');
  dog.innerHTML = svg;
  document.body.appendChild(dog);

  var vw = window.innerWidth;
  var dw = dog.offsetWidth || 120;
  var x = 20, target = 20, dir = 1, idleAfter = 0, wander = 0;
  window.addEventListener('resize', function () { vw = window.innerWidth; dw = dog.offsetWidth || 120; });
  window.addEventListener('pointermove', function (e) {
    idleAfter = 0;
    target = Math.max(0, Math.min(vw - dw, e.clientX - dw / 2));
  });

  function frame() {
    idleAfter++;
    if (idleAfter > 150) {           // しばらく動きが無ければ、のんびり散歩
      wander += 0.008;
      target = (vw - dw) * (0.5 + 0.42 * Math.sin(wander));
    }
    var prev = x;
    x += (target - x) * 0.06;
    if (x - prev > 0.15) dir = 1; else if (x - prev < -0.15) dir = -1;
    dog.style.transform = 'translateX(' + x.toFixed(1) + 'px) scaleX(' + dir + ')';
    requestAnimationFrame(frame);
  }
  if (reduce) { dog.style.transform = 'translateX(24px)'; }
  else { requestAnimationFrame(frame); }
})();

/* =========================================================
   アイテムボックス：スロットにホバー/フォーカスで左の詳細を更新
   （クリックは通常どおりリンク遷移）
   ========================================================= */
(function () {
  var box = document.querySelector('.item-box');
  if (!box) return;
  var img  = document.getElementById('ibImg');
  var name = document.getElementById('ibName');
  var desc = document.getElementById('ibDesc');
  var go   = document.getElementById('ibGo');
  var slots = Array.prototype.slice.call(box.querySelectorAll('.ib-slot'));

  function select(li) {
    var a  = li.querySelector('a.tile');
    var im = li.querySelector('img');
    var lb = li.querySelector('.tile-label');
    if (im && img)  img.src = im.getAttribute('src');
    if (lb && name) name.textContent = lb.textContent;
    if (desc) desc.textContent = li.getAttribute('data-desc') || '';
    if (a && go) go.setAttribute('href', a.getAttribute('href'));
    slots.forEach(function (s) { s.classList.remove('is-sel'); });
    li.classList.add('is-sel');
  }

  slots.forEach(function (li) {
    var a = li.querySelector('a.tile');
    li.addEventListener('pointerenter', function () { select(li); });
    if (a) a.addEventListener('focus', function () { select(li); });
  });
  if (slots[0]) select(slots[0]);
})();
