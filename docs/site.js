// Northbridge IT Desk project site: small, dependency-free interactions.
(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

  // Mobile menu
  const menu = $('#menu'), nav = $('nav');
  if (menu) menu.onclick = () => nav.classList.toggle('open');

  // Reading progress + back-to-top
  const prog = $('#progress'), top = $('#top');
  const onScroll = () => {
    const h = document.documentElement;
    const p = h.scrollTop / Math.max(1, h.scrollHeight - h.clientHeight);
    prog.style.width = (p * 100) + '%';
    const tb = $('.tocbar i'); if (tb) tb.style.width = (p * 100) + '%';
    top.classList.toggle('show', h.scrollTop > 600);
  };
  addEventListener('scroll', onScroll, { passive: true });
  top.onclick = () => scrollTo({ top: 0 });
  const tt = $('.toctop'); if (tt) tt.onclick = e => { e.preventDefault(); scrollTo({ top: 0 }); };
  // keep the current tab visible in the scrolling tab strip
  const on = $('.tabs a.on'); if (on) on.scrollIntoView({ block: 'nearest', inline: 'center' });

  // "On this page" table of contents from the h2 headings, with scroll-spy
  const toc = $('.toc'), tl = $('.toclist');
  let heads = $$('main h2'); if (heads.length < 2) heads = $$('main h3');
  if (toc && heads.length > 1) {
    heads.forEach((h, i) => {
      if (!h.id) h.id = 's' + i + '-' + h.textContent.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40);
      const a = document.createElement('a'); a.href = '#' + h.id;
      const c = h.cloneNode(true); c.querySelectorAll('.good,.adequate,.gap').forEach(x => x.remove()); a.textContent = c.textContent.replace(/\s+/g, ' ').trim().replace(/^\d+\.\s*/, ''); tl.appendChild(a);
    });
    const links = $$('a', tl);
    let lock = 0;
    const mark = i => links.forEach((l, k) => l.classList.toggle('on', k === i));
    const spy = () => {
      if (Date.now() < lock) return;
      const h = document.documentElement;
      if (h.scrollTop + innerHeight >= h.scrollHeight - 4) return mark(heads.length - 1); // at the bottom: last section
      let i = 0;
      heads.forEach((hd, k) => { if (hd.getBoundingClientRect().top <= 140) i = k; });
      mark(i);
    };
    links.forEach((l, k) => l.addEventListener('click', () => { mark(k); lock = Date.now() + 900; }));
    addEventListener('scroll', spy, { passive: true }); addEventListener('resize', spy); spy();
  } else if (toc) toc.remove();
  onScroll();

  // Fade-in on scroll
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { rootMargin: '0px 0px -40px 0px' });
  $$('main figure, main .card, main .tile, main .pillar, main table, main .diagram, main .compare').forEach(el => { el.classList.add('reveal'); io.observe(el); });

  // Copy buttons on code blocks
  $$('pre').forEach(pre => {
    const b = document.createElement('button'); b.className = 'copy'; b.textContent = 'Copy';
    b.onclick = () => navigator.clipboard.writeText(pre.innerText.replace(/Copy$|Copied!$/, '').trim()).then(() => { b.textContent = 'Copied!'; setTimeout(() => b.textContent = 'Copy', 1500); });
    pre.appendChild(b);
  });

  // Lightbox with caption and keyboard navigation
  const imgs = $$('figure img'), z = $('#z');
  let cur = 0;
  const show = i => {
    cur = (i + imgs.length) % imgs.length; const im = imgs[cur];
    $('img', z).src = im.src; $('p', z).innerHTML = im.closest('figure').querySelector('figcaption')?.innerHTML || '';
    z.classList.add('on');
  };
  imgs.forEach((im, i) => im.onclick = () => show(i));
  if (z) {
    $('.zx', z).onclick = () => z.classList.remove('on');
    $('.zp', z).onclick = e => { e.stopPropagation(); show(cur - 1); };
    $('.zn', z).onclick = e => { e.stopPropagation(); show(cur + 1); };
    z.onclick = e => { if (e.target === z) z.classList.remove('on'); };
    addEventListener('keydown', e => {
      if (!z.classList.contains('on')) return;
      if (e.key === 'Escape') z.classList.remove('on');
      if (e.key === 'ArrowLeft') show(cur - 1);
      if (e.key === 'ArrowRight') show(cur + 1);
    });
  }

  // Before/after compare slider
  $$('.compare').forEach(c => {
    const before = $('.before', c), bimg = $('.before img', c), knob = $('.knob', c), r = $('input', c), after = $(':scope > img', c);
    const size = () => { bimg.style.width = after.clientWidth + 'px'; bimg.style.height = after.clientHeight + 'px'; };
    const set = v => { before.style.width = v + '%'; knob.style.left = v + '%'; };
    r.oninput = () => set(r.value); addEventListener('resize', size);
    after.complete ? size() : after.onload = size; set(r.value);
  });

  // Filter buttons for tables: <div class="filters" data-table="id"><button data-f="all|fail">
  $$('.filters').forEach(f => {
    const rows = $$('#' + f.dataset.table + ' tr[data-tags]');
    $$('button', f).forEach(b => b.onclick = () => {
      $$('button', f).forEach(x => x.classList.toggle('on', x === b));
      rows.forEach(r => r.style.display = (b.dataset.f === 'all' || r.dataset.tags.includes(b.dataset.f)) ? '' : 'none');
    });
  });

  // Interactive diagram: steps highlight the path of a question
  const svg = $('.diagram svg');
  if (svg) {
    const info = $('.stepinfo'), btns = $$('.steps button[data-step]');
    const text = JSON.parse($('#steptext').textContent);
    let timer = null;
    const pick = n => {
      btns.forEach(b => b.classList.toggle('on', b.dataset.step === String(n)));
      if (!n) { svg.classList.remove('focus'); info.innerHTML = text[0]; return; }
      svg.classList.add('focus');
      $$('.step, .box', svg).forEach(el => el.classList.toggle('hl', (el.dataset.s || '').split(' ').includes(String(n))));
      info.innerHTML = text[n];
    };
    btns.forEach(b => b.onclick = () => { clearInterval(timer); pick(+b.dataset.step); });
    $('.steps .play').onclick = () => {
      clearInterval(timer); let n = 1; pick(n);
      timer = setInterval(() => { n++; if (n > 5) { clearInterval(timer); pick(0); } else pick(n); }, 3000);
    };
    pick(0);
  }
})();
