/* =========================================================
   d-storage.me  —  main.js
   最小限の動き（プレーンJS、ライブラリなし）
   ========================================================= */

// 1) フッターの年号を自動更新
document.querySelectorAll('#year').forEach(function (el) {
  el.textContent = new Date().getFullYear();
});

// 2) タイルにマウス位置追従の淡いハイライト（透明感の演出）
//    ※ 動きを減らす設定の人には適用しない
var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if (!reduceMotion) {
  document.querySelectorAll('.tile').forEach(function (tile) {
    tile.addEventListener('pointermove', function (e) {
      var r = tile.getBoundingClientRect();
      var x = ((e.clientX - r.left) / r.width) * 100;
      var y = ((e.clientY - r.top) / r.height) * 100;
      tile.style.background =
        'radial-gradient(circle at ' + x + '% ' + y + '%,' +
        ' rgba(125,211,252,0.35), rgba(255,255,255,0.55) 60%)';
    });
    tile.addEventListener('pointerleave', function () {
      tile.style.background = '';
    });
  });
}

