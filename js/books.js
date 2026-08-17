/* =========================================================
   積読ページ: カードの並び替え・絞り込み（静的サイト向けJS）
   ・並び替え: 日付(新/古) / 評価(高/低)
   ・絞り込み: 評価(以上) / ジャンル / 期間(開始〜終了)
   ========================================================= */
(function () {
  var grid = document.getElementById('bookGrid');
  if (!grid) return;

  var cards    = Array.prototype.slice.call(grid.querySelectorAll('.book-card'));
  var sortSel  = document.getElementById('sortSel');
  var ratingSel= document.getElementById('ratingSel');
  var genreSel = document.getElementById('genreSel');
  var fromDate = document.getElementById('fromDate');
  var toDate   = document.getElementById('toDate');
  var resetBtn = document.getElementById('resetBtn');
  var countLbl = document.getElementById('countLabel');

  function apply() {
    var minR  = parseInt((ratingSel && ratingSel.value) || '0', 10);
    var genre = (genreSel && genreSel.value) || '';
    var from  = (fromDate && fromDate.value) || '';
    var to    = (toDate && toDate.value) || '';

    // 絞り込み（表示/非表示）
    var shown = 0;
    cards.forEach(function (c) {
      var r = parseInt(c.getAttribute('data-rating') || '0', 10);
      var g = (c.getAttribute('data-genres') || '').split(',').map(function (s) { return s.trim(); }).filter(Boolean);
      var d = c.getAttribute('data-date') || '';
      var ok = true;
      if (minR && r < minR) ok = false;
      if (genre && g.indexOf(genre) === -1) ok = false;
      if (from && d && d < from) ok = false;
      if (to && d && d > to) ok = false;
      c.style.display = ok ? '' : 'none';
      if (ok) shown++;
    });

    // 並び替え（表示中のみ並べ替えてDOMを再配置）
    var parts = ((sortSel && sortSel.value) || 'date-desc').split('-');
    var key = parts[0], dir = parts[1];
    var vis = cards.filter(function (c) { return c.style.display !== 'none'; });
    vis.sort(function (a, b) {
      var av, bv;
      if (key === 'rating') {
        av = parseInt(a.getAttribute('data-rating') || '0', 10);
        bv = parseInt(b.getAttribute('data-rating') || '0', 10);
      } else {
        av = a.getAttribute('data-date') || '';
        bv = b.getAttribute('data-date') || '';
      }
      if (av < bv) return dir === 'asc' ? -1 : 1;
      if (av > bv) return dir === 'asc' ? 1 : -1;
      return 0;
    });
    vis.forEach(function (c) { grid.appendChild(c); });

    if (countLbl) countLbl.textContent = shown + ' 冊';
  }

  [sortSel, ratingSel, genreSel, fromDate, toDate].forEach(function (el) {
    if (el) el.addEventListener('change', apply);
  });
  if (resetBtn) resetBtn.addEventListener('click', function () {
    if (sortSel) sortSel.value = 'date-desc';
    if (ratingSel) ratingSel.value = '0';
    if (genreSel) genreSel.value = '';
    if (fromDate) fromDate.value = '';
    if (toDate) toDate.value = '';
    apply();
  });

  apply();
})();
