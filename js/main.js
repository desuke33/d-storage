/* =========================================================
   d-storage.me  —  main.js
   最小限の動き（プレーンJS、ライブラリなし）
   ========================================================= */

// フッターの年号を自動更新
document.querySelectorAll('#year').forEach(function (el) {
  el.textContent = new Date().getFullYear();
});

// タイルのホバー演出（軽いズーム）は CSS 側で実装。JSでの装飾は不要。

