// ================= views (analysis / TPM / equipment) =================
{ const hd = document.querySelector('header.top'); const setH = () => { if (hd) document.documentElement.style.setProperty('--hdr', hd.offsetHeight + 'px'); };
  setH(); addEventListener('resize', setH); if (window.ResizeObserver && hd) new ResizeObserver(setH).observe(hd); }
const TP = D.tpm;
const VIEWS = ['ana', 'tpm', 'atlas'], inited = { ana: true };
const viewOf = (el) => { const v = el && el.closest && el.closest('.view'); return v ? v.id.slice(2) : null; };
function setView(v, keepScroll) {
  VIEWS.forEach((k) => { document.getElementById('v-' + k).hidden = k !== v; const n = document.querySelector(`nav.links[data-for="${k}"]`); if (n) n.hidden = k !== v; });
  document.querySelectorAll('.vt button').forEach((b) => b.setAttribute('aria-selected', String(b.dataset.v === v)));
  if (!inited[v]) { inited[v] = true; try { INIT[v](); } catch (e) { console.error(e); } }
  if (!keepScroll) scrollTo({ top: 0, behavior: 'instant' });
}
document.querySelectorAll('.vt button').forEach((b) => b.addEventListener('click', () => setView(b.dataset.v)));
document.addEventListener('click', (e) => {
  const a = e.target.closest && e.target.closest('a[href^="#"]'); if (!a) return;
  const t = document.getElementById(a.getAttribute('href').slice(1)); const v = viewOf(t);
  if (v && document.getElementById('v-' + v).hidden) setView(v, true);
}, true);
addEventListener('hashchange', () => { const t = document.getElementById(location.hash.slice(1)); const v = viewOf(t); if (v && document.getElementById('v-' + v).hidden) { setView(v, true); t.scrollIntoView({ block: 'start' }); } });

const SC = (s) => s == null ? 'var(--dim)' : ['', 'var(--bad)', 'var(--flame)', 'var(--warn)', '#9be37a', 'var(--ok)'][s];
const sbox = (id, h) => svgIn(id, h);
const INIT = {};

// ---------- TPM view
INIT.tpm = () => {
  // maturity gauge
  reg(() => {
    const el = document.getElementById('matGauge'); el.replaceChildren(); const w = 320, h = 196, cx = 160, cy = 168, r = 128;
    const s = d3.select(el).append('svg').attr('viewBox', `0 0 ${w} ${h}`);
    const ang = (v) => Math.PI * (1 - (v - 1) / 4);
    for (let i = 1; i <= 4; i++) { const a0 = ang(i), a1 = ang(i + 1); s.append('path').attr('d', d3.arc()({ innerRadius: r - 26, outerRadius: r, startAngle: Math.PI / 2 - a0, endAngle: Math.PI / 2 - a1 })).attr('transform', `translate(${cx},${cy})`).attr('fill', SC(i + (i === 4 ? 1 : 0))).attr('opacity', 0.85); }
    [1, 2, 3, 4, 5].forEach((v) => { const a = ang(v); s.append('text').attr('x', cx + (r + 12) * Math.cos(a)).attr('y', cy - (r + 12) * Math.sin(a) + 4).attr('text-anchor', 'middle').attr('fill', 'var(--muted)').attr('font-size', 12).text(bn(v)); });
    const m = TP.maturity.mean, a = ang(m);
    s.append('line').attr('x1', cx).attr('y1', cy).attr('x2', cx + (r - 34) * Math.cos(a)).attr('y2', cy - (r - 34) * Math.sin(a)).attr('stroke', 'var(--fg)').attr('stroke-width', 4).attr('stroke-linecap', 'round');
    s.append('circle').attr('cx', cx).attr('cy', cy).attr('r', 9).attr('fill', 'var(--fg)');
    s.append('text').attr('x', cx).attr('y', cy - 44).attr('text-anchor', 'middle').attr('font-family', 'var(--f-display)').attr('font-weight', 800).attr('font-size', 40).attr('fill', 'var(--fg)').text(bn(m.toFixed(1)));
    s.append('text').attr('x', cx).attr('y', cy - 22).attr('text-anchor', 'middle').attr('fill', 'var(--muted)').attr('font-size', 13).text('out of 5');
  });
  // TPM house
  const P = TP.pillars, PI = TP.pillar_info;
  const short = { jh: 'Autonomous', pm: 'Planned', kk: 'Kaizen', qm: 'Quality', ot: 'Office', she: 'Safety', et: 'Training', eem: 'New equipment' };
  let sel = 'pm';
  function detail(k) {
    const p = P.find((x) => x.k === k), info = PI[k];
    document.getElementById('pdetail').innerHTML = `<h3>${p.name}</h3><span class="jp">${info.jp}</span>
      <div class="sc" style="--c:${SC(p.score)}">${[1, 2, 3, 4, 5].map((i) => `<i class="${p.score && i <= p.score ? 'f' : ''}"></i>`).join('')}</div>
      <p><b>Current level: ${p.score ? bn(p.score) + ' / 5' : 'not measured'}</b></p><p>${p.evidence}</p>
      <span class="lb">Goal</span><p>${info.goal}</p><span class="lb">Where at Barabkunda</span><p>${info.focus}</p>
      <span class="lb">First 90 days</span><ul>${info.act.map((a) => `<li>${a}</li>`).join('')}</ul>
      <span class="lb">KPIs</span><p>${info.kpi}</p><span class="lb">Owner</span><p>${info.owner}</p>`;
    document.querySelectorAll('.pillar').forEach((g) => g.classList.toggle('on', g.dataset.k === k));
  }
  reg(() => {
    const el = document.getElementById('house'); el.replaceChildren(); const w = 640, h = 430; const s = d3.select(el).append('svg').attr('viewBox', `0 0 ${w} ${h}`).attr('role', 'img').attr('aria-label', 'TPM house');
    s.append('path').attr('d', `M20 112 L320 18 L620 112 Z`).attr('fill', 'url(#gSteel)').attr('stroke', '#0b1220');
    s.append('text').attr('x', 320).attr('y', 84).attr('text-anchor', 'middle').attr('font-family', 'var(--f-display)').attr('font-weight', 800).attr('font-size', 15).attr('fill', '#0b1220').text('Zero breakdowns · zero defects · zero accidents');
    s.append('text').attr('x', 320).attr('y', 103).attr('text-anchor', 'middle').attr('font-size', 12).attr('fill', '#1b2636').text('LPG safely, at the right weight, on time');
    const order = ['jh', 'pm', 'kk', 'qm', 'ot', 'she', 'et', 'eem'], pw = 66, gap = (600 - 8 * pw) / 7;
    order.forEach((k, i) => {
      const p = P.find((x) => x.k === k), x = 20 + i * (pw + gap);
      const g = s.append('g').attr('class', 'pillar').attr('data-k', k).attr('tabindex', 0).attr('role', 'button').attr('aria-label', p.name);
      g.append('rect').attr('class', 'col').attr('x', x).attr('y', 122).attr('width', pw).attr('height', 214).attr('rx', 6).attr('fill', SC(p.score)).attr('fill-opacity', 0.22).attr('stroke', SC(p.score)).attr('stroke-width', 1.6);
      g.append('rect').attr('x', x).attr('y', 122).attr('width', pw).attr('height', 214 * ((p.score || 0) / 5)).attr('transform', `translate(0 ${214 * (1 - (p.score || 0) / 5)})`).attr('rx', 6).attr('fill', SC(p.score)).attr('opacity', 0.55);
      g.append('text').attr('x', x + pw / 2).attr('y', 160).attr('text-anchor', 'middle').attr('font-family', 'var(--f-display)').attr('font-weight', 800).attr('font-size', 26).attr('fill', 'var(--fg)').text(p.score ? bn(p.score) : '?');
      g.append('text').attr('transform', `translate(${x + pw / 2 + 6},${250}) rotate(-90)`).attr('text-anchor', 'middle').attr('font-size', 17).attr('font-weight', 700).attr('fill', '#ffffff').attr('paint-order', 'stroke').attr('stroke', '#060a12').attr('stroke-width', 3).text(short[k]);
      g.on('click', () => { sel = k; detail(k); }).on('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); sel = k; detail(k); } });
    });
    s.append('rect').attr('x', 14).attr('y', 340).attr('width', 612).attr('height', 34).attr('rx', 6).attr('fill', '#2b3646').attr('stroke', '#0b1220');
    s.append('text').attr('x', 320).attr('y', 362).attr('text-anchor', 'middle').attr('font-weight', 700).attr('font-size', 15).attr('fill', 'var(--fg)').text('Foundation: 5S · sort, set in order, shine, standardise, sustain');
    s.append('rect').attr('x', 6).attr('y', 378).attr('width', 628).attr('height', 34).attr('rx', 6).attr('fill', '#1a2433').attr('stroke', '#0b1220');
    s.append('text').attr('x', 320).attr('y', 400).attr('text-anchor', 'middle').attr('font-size', 14).attr('fill', 'var(--muted)').text('People: leadership commitment, teamwork, training');
    detail(sel);
  });
  sparkDraw('spk');
  // SAP funnel
  reg(() => {
    const { s, w } = sbox('funnel', 230); const F = TP.funnel, m = { l: 150, r: 70 }, bh = 30;
    const x = d3.scaleLinear([0, F[0].n], [m.l, w - m.r]);
    F.forEach((f, i) => { const y = 12 + i * (bh + 12);
      s.append('rect').attr('x', m.l).attr('y', y).attr('width', w - m.r - m.l).attr('height', bh).attr('rx', 6).attr('fill', 'var(--ink0)');
      s.append('rect').attr('x', m.l).attr('y', y).attr('width', Math.max(2, x(f.n) - m.l)).attr('height', bh).attr('rx', 6).attr('fill', f.pct > 50 ? 'var(--fleet)' : f.pct > 5 ? 'var(--warn)' : 'var(--bad)');
      s.append('text').attr('x', m.l - 8).attr('y', y + bh / 2 + 4).attr('text-anchor', 'end').attr('class', 'strong').text(f.stage);
      s.append('text').attr('x', Math.max(x(f.n), m.l) + 8).attr('y', y + bh / 2 + 4).attr('class', 'strong').text(`${bn(f.n)} (${bn(f.pct.toFixed(f.pct < 10 && f.pct > 0 ? 1 : 0))}%)`); });
  });
  reg(() => {
    const { s, w } = sbox('lateQ', 220); const data = TP.quarters.filter((q) => q.orders >= 5 && q.q >= '2022Q1'), m = { l: 40, r: 10, t: 12, b: 30 };
    const x = d3.scaleBand(data.map((d) => d.q), [m.l, w - m.r]).padding(0.25), y = d3.scaleLinear([0, 100], [220 - m.b, m.t]);
    yAxis(s.append('g'), y, m.l, w - m.r, (v) => bn(v) + '%', 4);
    s.append('line').attr('x1', m.l).attr('x2', w - m.r).attr('y1', y(10)).attr('y2', y(10)).attr('stroke', 'var(--ok)').attr('stroke-dasharray', '4 3');
    data.forEach((d) => { s.append('rect').attr('x', x(d.q)).attr('width', x.bandwidth()).attr('y', y(d.backdated)).attr('height', y(0) - y(d.backdated)).attr('rx', 3).attr('fill', d.backdated > 30 ? 'var(--bad)' : 'var(--warn)')
      .on('mousemove', (ev) => showTip(ev, `<b>${bn(d.q.replace('Q', ' Q'))}</b><br>${bn(d.backdated.toFixed(0))}% back-dated · ${bn(d.orders)} orders`)).on('mouseleave', hideTip);
      if (d.q.endsWith('Q1')) s.append('text').attr('x', x(d.q)).attr('y', 220 - 10).text(bn(d.q.slice(0, 4))); });
  });
  // 5S audit
  const sels = [...document.querySelectorAll('.s5 select')];
  const KEY = 'bk-5s-audit';
  try { const saved = JSON.parse(localStorage.getItem(KEY) || '[]'); sels.forEach((x, i) => { if (saved[i] != null) x.value = saved[i]; }); } catch (e) {}
  const score = () => { const t = d3.sum(sels, (x) => +x.value), mx = sels.length * 4, p = t / mx * 100;
    document.getElementById('s5score').innerHTML = `${bn(t)} / ${bn(mx)} · <span style="color:${p >= 80 ? 'var(--ok)' : p >= 50 ? 'var(--warn)' : 'var(--bad)'}">${bn(p.toFixed(0))}%</span>`;
    try { localStorage.setItem(KEY, JSON.stringify(sels.map((x) => x.value))); } catch (e) {} };
  sels.forEach((x) => x.addEventListener('change', score)); score();
  document.getElementById('s5reset').addEventListener('click', () => { sels.forEach((x) => { x.value = '0'; }); score(); });
  document.getElementById('s5print').addEventListener('click', () => print());
  // planned-maintenance filter
  document.querySelectorAll('#whoF .btn').forEach((b) => b.addEventListener('click', () => {
    document.querySelectorAll('#whoF .btn').forEach((x) => x.classList.toggle('on', x === b));
    document.querySelectorAll('.pmcal .tk').forEach((t) => t.classList.toggle('dim', b.dataset.who !== 'all' && t.dataset.w !== b.dataset.who));
  }));
  // roadmap gantt
  reg(() => {
    const el = document.getElementById('gantt'); el.replaceChildren(); const R = TP.roadmap, w = Math.max(640, el.clientWidth || 900), rowH = 26, m = { l: Math.min(330, w * 0.4), r: 12, t: 30, b: 10 };
    const h = m.t + R.length * rowH + m.b, s = d3.select(el).append('svg').attr('viewBox', `0 0 ${w} ${h}`).attr('role', 'img').attr('aria-label', 'TPM roadmap');
    const x = d3.scaleLinear([-1, 36], [m.l, w - m.r]); const PC = { 'Preparation': 'var(--renew)', 'Kick-off': 'var(--flame)', 'Implementation': 'var(--fleet)', 'Consolidation': 'var(--ok)' };
    for (let k = 0; k <= 36; k += 3) { const d = new Date(2026, 11 + k, 1); s.append('line').attr('x1', x(k)).attr('x2', x(k)).attr('y1', m.t - 6).attr('y2', h - m.b).attr('stroke', 'var(--line)');
      s.append('text').attr('x', x(k) + 3).attr('y', m.t - 12).attr('font-size', 11).text(MON[d.getMonth()] + ' ' + bn(String(d.getFullYear()).slice(2))); }
    R.forEach(([nm, ph, st, du], i) => { const y = m.t + i * rowH;
      s.append('text').attr('x', m.l - 8).attr('y', y + 17).attr('text-anchor', 'end').attr('font-size', 12.5).attr('fill', 'var(--fg)').text(nm.length > 34 && w < 760 ? nm.slice(0, 32) + '…' : nm);
      s.append('rect').attr('x', x(st)).attr('y', y + 5).attr('width', x(st + du) - x(st)).attr('height', rowH - 10).attr('rx', 5).attr('fill', PC[ph]).attr('fill-opacity', 0.28).attr('stroke', PC[ph])
        .on('mousemove', (ev) => showTip(ev, `<b>${nm}</b><br>${ph} · ${bn(du)} months<br><span class=m>Progress: not started</span>`)).on('mouseleave', hideTip); });
    s.append('line').attr('x1', x(-1) + 4).attr('x2', x(-1) + 4).attr('y1', m.t - 6).attr('y2', h - m.b).attr('stroke', 'var(--flame2)').attr('stroke-width', 2);
    s.append('text').attr('x', x(-1) + 8).attr('y', h - m.b - 4).attr('font-size', 11).attr('fill', 'var(--flame2)').text('Today');
  });
};

// ---------- equipment view
INIT.atlas = () => {
  const goEq = (id) => { const el = document.getElementById('eq-' + id); if (!el) return; el.hidden = false; el.style.display = ''; el.scrollIntoView({ block: 'start', behavior: 'smooth' }); el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash'); };
  document.querySelectorAll('.hs').forEach((g) => { g.addEventListener('click', () => goEq(g.dataset.eq)); g.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); goEq(g.dataset.eq); } }); });
  document.querySelectorAll('.eq').forEach((card) => {
    const fig = card.querySelector('.eqfig'), lis = [...card.querySelectorAll('.parts li')];
    const on = (n) => { fig.classList.add('hl'); fig.querySelectorAll('.pt, .co').forEach((p) => p.classList.toggle('hot', p.dataset.p === n)); lis.forEach((l) => l.classList.toggle('on', l.dataset.p === n)); };
    const off = () => { fig.classList.remove('hl'); fig.querySelectorAll('.hot').forEach((p) => p.classList.remove('hot')); lis.forEach((l) => l.classList.remove('on')); };
    lis.forEach((l) => { l.addEventListener('mouseenter', () => on(l.dataset.p)); l.addEventListener('mouseleave', off); l.addEventListener('click', () => (l.classList.contains('on') ? off() : on(l.dataset.p))); });
    fig.querySelectorAll('.co').forEach((c) => { c.addEventListener('mouseenter', () => on(c.dataset.p)); c.addEventListener('mouseleave', off); c.addEventListener('click', () => on(c.dataset.p)); });
  });
  let st = 'all';
  const q = document.getElementById('eqQ');
  const apply = () => { const qq = q.value.trim().toLowerCase(); document.querySelectorAll('.eq').forEach((c) => { const ok = (st === 'all' || c.dataset.st === st) && (!qq || c.dataset.name.toLowerCase().includes(qq) || c.textContent.toLowerCase().includes(qq)); c.style.display = ok ? '' : 'none'; }); };
  document.querySelectorAll('#stF .btn').forEach((b) => b.addEventListener('click', () => { st = b.dataset.st; document.querySelectorAll('#stF .btn').forEach((x) => x.classList.toggle('on', x === b)); apply(); }));
  q.addEventListener('input', apply);
};

// ---------- deeper analytics (analysis view, drawn now)
reg(() => {
  const W = TP.waterfall; const { s, w } = svgIn('cWater', 300); const m = { l: 56, r: 10, t: 14, b: 70 };
  const steps = [{ c: 'H2 2025', a: 0, b: W.start, tot: true }]; let run = W.start;
  W.steps.forEach((d) => { steps.push({ c: d.c, a: run, b: run + d.d, d: d.d }); run += d.d; }); steps.push({ c: 'H1 2026', a: 0, b: W.end, tot: true });
  const x = d3.scaleBand(steps.map((d, i) => i), [m.l, w - m.r]).padding(0.25), y = d3.scaleLinear([d3.min(steps, (d) => Math.min(d.a, d.b)) * 0.85, d3.max(steps, (d) => Math.max(d.a, d.b)) * 1.04], [300 - m.b, m.t]);
  yAxis(s.append('g'), y, m.l, w - m.r, lakh, 4);
  steps.forEach((d, i) => { const y0 = y(Math.max(d.a, d.b)), y1 = y(d.tot ? y.domain()[0] : Math.min(d.a, d.b));
    s.append('rect').attr('x', x(i)).attr('width', x.bandwidth()).attr('y', d.tot ? y(d.b) : y0).attr('height', Math.max(1, (d.tot ? y(y.domain()[0]) - y(d.b) : y1 - y0))).attr('rx', 3)
      .attr('fill', d.tot ? 'var(--fleet)' : d.d > 0 ? 'var(--bad)' : 'var(--ok)').on('mousemove', (ev) => showTip(ev, `<b>${d.c}</b><br>${d.tot ? tk(d.b) : (d.d > 0 ? '+' : '−') + tk(Math.abs(d.d))}`)).on('mouseleave', hideTip);
    s.append('text').attr('x', x(i) + x.bandwidth() / 2).attr('y', (d.tot ? y(d.b) : y0) - 4).attr('text-anchor', 'middle').attr('font-size', 10.5).attr('class', 'strong').text(d.tot ? lakh(d.b) : (d.d > 0 ? '+' : '−') + lakh(Math.abs(d.d)));
    s.append('text').attr('transform', `translate(${x(i) + x.bandwidth() / 2},${300 - m.b + 10}) rotate(35)`).attr('font-size', 10.5).text(d.c.length > 18 ? d.c.slice(0, 17) + '…' : d.c); });
});
reg(() => {
  const data = TP.cost_q.filter((d) => d.q >= '2022Q1'); const { s, w } = svgIn('cCostQ', 260); const m = { l: 56, r: 10, t: 12, b: 30 };
  const x = d3.scaleBand(data.map((d) => d.q), [m.l, w - m.r]).padding(0.2), y = d3.scaleLinear([0, d3.max(data, (d) => d.fleet + d.plant + d.renew) * 1.1], [260 - m.b, m.t]).nice();
  yAxis(s.append('g'), y, m.l, w - m.r, lakh, 4);
  data.forEach((d) => { let y0 = 0; const gapq = d.q >= '2024Q3' && d.q <= '2025Q1';
    if (gapq) s.append('rect').attr('x', x(d.q)).attr('width', x.bandwidth()).attr('y', m.t).attr('height', 260 - m.b - m.t).attr('fill', 'var(--muted)').attr('opacity', 0.1);
    [['fleet', 'var(--fleet)'], ['plant', 'var(--plant)'], ['renew', 'var(--renew)']].forEach(([k, c]) => { if (d[k] > 0) s.append('rect').attr('x', x(d.q)).attr('width', x.bandwidth()).attr('y', y(y0 + d[k])).attr('height', y(y0) - y(y0 + d[k])).attr('fill', c); y0 += d[k]; });
    s.append('rect').attr('x', x(d.q)).attr('width', x.bandwidth()).attr('y', m.t).attr('height', 260 - m.b - m.t).attr('fill', 'transparent').on('mousemove', (ev) => showTip(ev, `<b>${bn(d.q.replace('Q', ' Q'))}</b><br>Fleet ${tk(d.fleet)}<br>Plant ${tk(d.plant)}<br>Renewals ${tk(d.renew)}`)).on('mouseleave', hideTip);
    if (d.q.endsWith('Q1')) s.append('text').attr('x', x(d.q)).attr('y', 260 - 10).text(bn(d.q.slice(0, 4))); });
});
reg(() => {
  const C = TP.cost_type, lab = ['Scheduled service only', 'Service + repair', 'Repair only'], col = ['var(--c2)', 'var(--c6)', 'var(--c1)'];
  const { s, w } = svgIn('cCostType', 230); const m = { l: 150, r: 110, t: 10 }, bh = 26;
  const x = d3.scaleLinear([0, d3.max(C.sum)], [m.l, w - m.r]);
  lab.forEach((l, i) => { const y = m.t + i * 70;
    s.append('text').attr('x', m.l - 8).attr('y', y + 18).attr('text-anchor', 'end').attr('class', 'strong').text(l);
    s.append('text').attr('x', m.l - 8).attr('y', y + 36).attr('text-anchor', 'end').attr('font-size', 11).text(`${bn(C.n[i])} jobs · median ${f0(C.med[i])}`);
    s.append('rect').attr('x', m.l).attr('y', y + 6).attr('width', x(C.sum[i]) - m.l).attr('height', bh).attr('rx', 5).attr('fill', col[i]);
    s.append('text').attr('x', x(C.sum[i]) + 6).attr('y', y + 24).attr('class', 'strong').text(tk(C.sum[i])); });
});
reg(() => {
  const E = TP.fc_err; const { s, w } = svgIn('cFcErr', 260); const m = { l: 56, r: 10, t: 14, b: 30 };
  const x = d3.scaleBand(E.map((d) => d.m), [m.l, w - m.r]).padding(0.3), y = d3.scaleLinear([0, d3.max(E, (d) => Math.max(d.y, d.p, d.naive)) * 1.1], [260 - m.b, m.t]).nice();
  yAxis(s.append('g'), y, m.l, w - m.r, lakh, 4);
  E.forEach((d) => { const cx = x(d.m) + x.bandwidth() / 2;
    s.append('rect').attr('x', x(d.m)).attr('width', x.bandwidth()).attr('y', y(d.y)).attr('height', y(0) - y(d.y)).attr('rx', 3).attr('fill', 'var(--fleet)').attr('opacity', 0.75);
    s.append('line').attr('x1', cx - 10).attr('x2', cx + 10).attr('y1', y(d.p)).attr('y2', y(d.p)).attr('stroke', 'var(--flame)').attr('stroke-width', 3);
    s.append('line').attr('x1', cx).attr('x2', cx).attr('y1', y(d.p)).attr('y2', y(d.y)).attr('stroke', 'var(--flame)').attr('stroke-dasharray', '3 2');
    s.append('circle').attr('cx', cx + 14).attr('cy', y(d.naive)).attr('r', 4).attr('fill', 'var(--muted)');
    s.append('rect').attr('x', x(d.m)).attr('width', x.bandwidth()).attr('y', m.t).attr('height', 260 - m.b - m.t).attr('fill', 'transparent').on('mousemove', (ev) => showTip(ev, `<b>${mlab(d.m)}</b><br>Actual ${tk(d.y)}<br>Forecast ${tk(d.p)} (error ${tk(Math.abs(d.y - d.p))})<br><span class=m>Naive ${tk(d.naive)}</span>`)).on('mouseleave', hideTip);
    s.append('text').attr('x', cx).attr('y', 260 - 10).attr('text-anchor', 'middle').text(mlab(d.m)); });
  const lg = s.append('g').attr('transform', `translate(${m.l + 6},${m.t + 4})`).attr('font-size', 11);
  [['var(--fleet)', 'Actual'], ['var(--flame)', 'Forecast'], ['var(--muted)', 'Naive']].forEach(([c, t], i) => { lg.append('rect').attr('x', i * 84).attr('y', 0).attr('width', 10).attr('height', 10).attr('fill', c); lg.append('text').attr('x', i * 84 + 14).attr('y', 9).text(t); });
});
reg(() => {
  const B = TP.cal_bins; const { s, w } = svgIn('cCal', 260); const m = { l: 44, r: 16, t: 12, b: 34 }, mx = Math.max(50, d3.max(B, (b) => Math.max(b.pred, b.obs)) * 1.1);
  const x = d3.scaleLinear([0, mx], [m.l, w - m.r]), y = d3.scaleLinear([0, mx], [260 - m.b, m.t]);
  yAxis(s.append('g'), y, m.l, w - m.r, (v) => bn(v) + '%', 4);
  s.append('line').attr('x1', x(0)).attr('y1', y(0)).attr('x2', x(mx)).attr('y2', y(mx)).attr('stroke', 'var(--muted)').attr('stroke-dasharray', '4 3');
  s.append('path').attr('d', d3.line().x((b) => x(b.pred)).y((b) => y(b.obs))(B)).attr('fill', 'none').attr('stroke', 'var(--flame)').attr('stroke-width', 2);
  B.forEach((b) => s.append('circle').attr('cx', x(b.pred)).attr('cy', y(b.obs)).attr('r', 5).attr('fill', 'var(--flame)').on('mousemove', (ev) => showTip(ev, `Model said ${bn(b.pred.toFixed(0))}% on average<br>Actually happened ${bn(b.obs.toFixed(0))}%<br><span class=m>${bn(b.n)} vehicle-months</span>`)).on('mouseleave', hideTip));
  x.ticks(4).forEach((t) => s.append('text').attr('x', x(t)).attr('y', 260 - 16).attr('text-anchor', 'middle').text(bn(t) + '%'));
  s.append('text').attr('x', (m.l + w) / 2).attr('y', 258).attr('text-anchor', 'middle').attr('font-size', 11).text('Model probability');
});
// ---------- quarterly progress (shared with the TPM view)
const Q = TP.quarters.filter((q) => q.jobs >= 8 && q.q >= '2023Q1');
const SPK = [['planned', 'Planned work %', 70, true], ['reactive', 'Repair only after breakdown %', 30, false], ['repeat', 'Repeat repairs within 90 days %', 8, false], ['backdated', 'Back-dated orders %', 10, false], ['cost_per_vehicle_month', 'Cost per vehicle per month (Tk)', null, false]];
function sparkDraw(id) { reg(() => {
  const host = document.getElementById(id); host.replaceChildren();
  SPK.forEach(([k, lab, tgt, up]) => {
    const pts = TP.quarters.filter((q) => q.q >= '2023Q1').map((q) => ({ q: q.q, v: q.jobs >= 8 || (k === 'backdated' && q.orders >= 8) ? q[k] : null }));
    const last = [...pts].reverse().find((p) => p.v != null), prev = [...pts].reverse().filter((p) => p.v != null)[1];
    const card = document.createElement('div'); card.className = 'sp'; host.appendChild(card);
    const good = last && prev ? ((last.v > prev.v) === up || tgt == null && last.v < prev.v) : null;
    card.innerHTML = `<b>${lab}</b><span class="now" style="color:${good == null ? 'var(--fg)' : good ? 'var(--ok)' : 'var(--bad)'}">${last ? (k.startsWith('cost') ? lakh(last.v) : bn(last.v.toFixed(0)) + '%') : '—'}</span>`;
    const w = 260, h = 92, m = { l: 4, r: 4, t: 10, b: 16 };
    const s = d3.select(card).append('svg').attr('viewBox', `0 0 ${w} ${h}`);
    const vals = pts.filter((p) => p.v != null).map((p) => p.v).concat(tgt != null ? [tgt] : []);
    const x = d3.scalePoint(pts.map((p) => p.q), [m.l + 6, w - m.r - 6]), y = d3.scaleLinear([Math.min(0, d3.min(vals)), d3.max(vals) * 1.12], [h - m.b, m.t]);
    if (tgt != null) s.append('line').attr('x1', m.l).attr('x2', w - m.r).attr('y1', y(tgt)).attr('y2', y(tgt)).attr('stroke', 'var(--flame2)').attr('stroke-dasharray', '4 3');
    s.append('path').attr('d', d3.line().defined((p) => p.v != null).x((p) => x(p.q)).y((p) => y(p.v))(pts)).attr('fill', 'none').attr('stroke', 'var(--fleet)').attr('stroke-width', 2);
    pts.forEach((p, i) => { if (p.v == null) return; const pv = pts.slice(0, i).reverse().find((z) => z.v != null); const g = pv ? ((p.v > pv.v) === up || (tgt == null && p.v < pv.v)) : null;
      s.append('circle').attr('cx', x(p.q)).attr('cy', y(p.v)).attr('r', 3.4).attr('fill', g == null ? 'var(--fleet)' : g ? 'var(--ok)' : 'var(--bad)').on('mousemove', (ev) => showTip(ev, `<b>${bn(p.q.replace('Q', ' Q'))}</b><br>${k.startsWith('cost') ? tk(p.v) : bn(p.v.toFixed(1)) + '%'}`)).on('mouseleave', hideTip); });
    [pts[0], pts[pts.length - 1]].forEach((p, i) => s.append('text').attr('x', x(p.q)).attr('y', h - 3).attr('text-anchor', i ? 'end' : 'start').text(bn(p.q.replace('Q', ' Q'))));
  });
}); }
sparkDraw('spk2');

// ---------- opened from the hub or a link with a view or section name
try {
  const tab = window.__tab || (location.hash ? decodeURIComponent(location.hash.slice(1)) : '');
  if (tab) {
    if (VIEWS.includes(tab)) setView(tab);
    else { const el = document.getElementById(tab); if (el) { const v = viewOf(el); if (v && v !== 'ana') setView(v, true); const go = () => el.scrollIntoView({ block: 'start', behavior: 'instant' }); setTimeout(go, 60); addEventListener('load', () => setTimeout(go, 50)); setTimeout(go, 700); } }
  }
} catch (e) {}
// ---------- nav highlight (one nav per view)
document.querySelectorAll('nav.links').forEach((nav) => {
  const links = [...nav.querySelectorAll('a')], secs = links.map((a) => document.getElementById(a.getAttribute('href').slice(1))).filter(Boolean);
  if (!('IntersectionObserver' in window)) return;
  const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) links.forEach((a) => a.classList.toggle('on', a.getAttribute('href') === '#' + e.target.id)); }), { rootMargin: '-45% 0px -50% 0px' });
  secs.forEach((s) => io.observe(s));
});
