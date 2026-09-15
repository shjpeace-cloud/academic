/**
 * Interactive GPRNK chart for gprnk.html.
 *
 * Reads data/gprnk/GPRNK_monthly.csv (the same file visitors download) and
 * draws one of three views as inline SVG: the headline index, its negative /
 * positive components, or the four subtopic series. No dependencies.
 *
 * Every value is reachable three ways — hover, keyboard (arrow keys), and the
 * table view below the chart — so nothing is locked behind a tooltip.
 */
(function () {
  'use strict';

  const CSV_PATH = 'data/gprnk/GPRNK_monthly.csv';

  // Colors: site navy for the single-series view; categorical slots 1–4
  // (validated for colorblind separation) where several series share a plot.
  const VIEWS = {
    index: {
      series: [{ key: 'gprnk', label: 'GPRNK', color: '#1a3a5c' }],
      events: true,
      caption: 'Monthly GPRNK index, normalised to a mean of 100 over 1995–2016. ' +
        'Marked months are reference events; hover or use the arrow keys to read individual values.',
      aria: 'Line chart of the monthly GPRNK index, 1995 to 2025.'
    },
    components: {
      series: [
        { key: 'gprnk_negative', label: 'Negative', color: '#eb6834' },
        { key: 'gprnk_positive', label: 'Positive', color: '#2a78d6' }
      ],
      events: false,
      caption: 'The negative component (military tensions and sanctions) and the positive component ' +
        '(talks and economic cooperation), each normalised to a mean of 100 over 1995–2016.',
      aria: 'Line chart comparing the negative and positive components of the GPRNK index, 1995 to 2025.'
    },
    subtopics: {
      series: [
        { key: 'threat', label: 'Military tensions', color: '#2a78d6' },
        { key: 'sanction', label: 'Sanctions', color: '#eb6834' },
        { key: 'talks', label: 'Talks', color: '#1baf7a' },
        { key: 'economic_cooperation', label: 'Economic cooperation', color: '#eda100' }
      ],
      // Four series on one plot is spaghetti; each gets its own panel on a
      // shared scale instead.
      facet: true,
      events: false,
      caption: 'The four keyword categories behind the index, each normalised to a mean of 100 over ' +
        '1995–2016.',
      aria: 'Line chart of four subtopic indices — military tensions, sanctions, talks and economic ' +
        'cooperation — 1995 to 2025.'
    }
  };

  const EVENTS = [
    { month: '2000-06', label: '1st summit', side: 'below' },
    { month: '2006-10', label: '1st nuclear test', side: 'above' },
    { month: '2010-11', label: 'Yeonpyeong', side: 'above' },
    { month: '2013-03', label: '3rd nuclear test', side: 'above' },
    { month: '2017-08', label: '"Fire and fury"', side: 'above' },
    { month: '2018-04', label: 'Panmunjom summit', side: 'below' },
    { month: '2022-10', label: 'Missile barrage', side: 'above' },
    { month: '2023-12', label: '"Two hostile states"', side: 'above' }
  ];

  const INK_MUTED = '#898781';
  const GRID = '#e1e0d9';
  const AXIS = '#c3c2b7';
  const SURFACE = '#ffffff';
  const NS = 'http://www.w3.org/2000/svg';

  const ALL_COLUMNS = [
    'gprnk', 'gprnk_negative', 'gprnk_positive', 'threat',
    'sanction', 'talks', 'economic_cooperation', 'gprnk_raw'
  ];

  let rows = [];
  let view = 'index';
  let cursor = -1;

  const svg = document.getElementById('chart');
  const wrap = document.getElementById('chart-wrap');
  const tooltip = document.getElementById('tooltip');
  const legendEl = document.getElementById('chart-legend');
  const captionEl = document.getElementById('chart-caption');

  function el(name, attrs, text) {
    const node = document.createElementNS(NS, name);
    for (const k in attrs) node.setAttribute(k, attrs[k]);
    if (text != null) node.textContent = text;
    return node;
  }

  function parseCsv(text) {
    const lines = text.trim().split(/\r?\n/);
    const head = lines[0].split(',');
    return lines.slice(1).map(line => {
      const cells = line.split(',');
      const row = { date: cells[head.indexOf('date')] };
      ALL_COLUMNS.forEach(col => {
        const i = head.indexOf(col);
        row[col] = i >= 0 ? parseFloat(cells[i]) : NaN;
      });
      return row;
    });
  }

  function fmt(v) {
    return Number.isFinite(v) ? v.toFixed(1) : '—';
  }

  function monthLabel(date) {
    const [y, m] = date.split('-');
    const names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return names[parseInt(m, 10) - 1] + ' ' + y;
  }

  function niceTicks(max) {
    const step = max > 320 ? 100 : max > 160 ? 50 : 25;
    const ticks = [];
    for (let v = 0; v <= max; v += step) ticks.push(v);
    return ticks;
  }

  function draw() {
    if (!rows.length) return;
    const conf = VIEWS[view];
    const width = Math.max(280, wrap.clientWidth);
    const narrow = width < 560;
    const facet = !!conf.facet;
    const cols = facet ? (narrow ? 1 : 2) : 1;
    const panelRows = facet ? Math.ceil(conf.series.length / cols) : 1;
    const height = facet ? (narrow ? 520 : 400) : (narrow ? 260 : 360);

    // Endpoint labels need room; size the right margin to the longest one.
    const labelled = !facet && conf.series.length > 1 && !narrow;
    const longest = labelled
      ? Math.max(...conf.series.map(s => s.label.length)) : 0;
    const m = {
      top: facet ? 22 : 16,
      right: labelled ? Math.min(140, longest * 6.4 + 22) : 14,
      bottom: 28,
      left: 40
    };
    const gapX = 34;
    const gapY = facet ? 34 : 0;
    const plotW = width - m.left - m.right;
    const plotH = height - m.top - m.bottom;
    const panelW = (plotW - gapX * (cols - 1)) / cols;
    const panelH = (plotH - gapY * (panelRows - 1)) / panelRows;

    let max = 0;
    conf.series.forEach(s => rows.forEach(r => {
      if (Number.isFinite(r[s.key]) && r[s.key] > max) max = r[s.key];
    }));
    const headroom = conf.events && !narrow ? 1.22 : 1.06;
    const yMax = max * headroom;

    // Panel geometry: one entry per plot area, each with its own series list.
    const panels = (facet ? conf.series.map(s => [s]) : [conf.series]).map((series, p) => {
      const col = p % cols;
      const row = Math.floor(p / cols);
      const left = m.left + col * (panelW + gapX);
      const top = m.top + row * (panelH + gapY);
      return {
        series: series, left: left, top: top, w: panelW, h: panelH,
        bottomRow: row === panelRows - 1,
        firstCol: col === 0,
        x: i => left + (panelW * i) / (rows.length - 1),
        y: v => top + panelH * (1 - v / yMax)
      };
    });

    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    svg.setAttribute('height', height);
    svg.setAttribute('aria-label', conf.aria +
      ' Values are also listed in the data table below the chart.');
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const firstYear = parseInt(rows[0].date.slice(0, 4), 10);
    const lastYear = parseInt(rows[rows.length - 1].date.slice(0, 4), 10);
    const stepYears = narrow || facet ? 10 : 5;

    panels.forEach(p => {
      // Gridlines + y labels
      niceTicks(yMax).forEach(v => {
        svg.appendChild(el('line', {
          x1: p.left, x2: p.left + p.w, y1: p.y(v), y2: p.y(v),
          stroke: GRID, 'stroke-width': 1
        }));
        if (p.firstCol || facet) {
          svg.appendChild(el('text', {
            x: p.left - 8, y: p.y(v) + 4, 'text-anchor': 'end',
            fill: INK_MUTED, 'font-size': 11
          }, String(v)));
        }
      });

      // X axis
      svg.appendChild(el('line', {
        x1: p.left, x2: p.left + p.w, y1: p.top + p.h, y2: p.top + p.h,
        stroke: AXIS, 'stroke-width': 1
      }));
      for (let yr = Math.ceil(firstYear / stepYears) * stepYears; yr <= lastYear; yr += stepYears) {
        const i = rows.findIndex(r => r.date.slice(0, 4) === String(yr));
        if (i < 0) continue;
        svg.appendChild(el('text', {
          x: p.x(i), y: p.top + p.h + 18, 'text-anchor': 'middle',
          fill: INK_MUTED, 'font-size': 11
        }, String(yr)));
      }

      // Base line at 100
      svg.appendChild(el('line', {
        x1: p.left, x2: p.left + p.w, y1: p.y(100), y2: p.y(100),
        stroke: AXIS, 'stroke-width': 1
      }));

      // Series
      p.series.forEach(s => {
        const d = rows.map((r, i) =>
          `${i ? 'L' : 'M'}${p.x(i).toFixed(1)},${p.y(r[s.key]).toFixed(1)}`).join('');
        svg.appendChild(el('path', {
          d: d, fill: 'none', stroke: s.color, 'stroke-width': facet ? 1.2 : 1.6,
          'stroke-linejoin': 'round', 'stroke-linecap': 'round'
        }));
      });

      // Panel title (faceted view)
      if (facet) {
        svg.appendChild(el('circle', {
          cx: p.left + 4, cy: p.top - 9, r: 3.5, fill: p.series[0].color
        }));
        svg.appendChild(el('text', {
          x: p.left + 13, y: p.top - 5, fill: '#52514e', 'font-size': 11.5
        }, p.series[0].label));
      }
    });

    const main = panels[0];

    // Endpoint labels when several series share one plot
    if (labelled) {
      const labels = conf.series.map(s => ({
        s: s, yy: main.y(rows[rows.length - 1][s.key])
      })).sort((a, b) => a.yy - b.yy);
      for (let i = 1; i < labels.length; i++) {
        if (labels[i].yy - labels[i - 1].yy < 14) labels[i].yy = labels[i - 1].yy + 14;
      }
      labels.forEach(l => {
        svg.appendChild(el('circle', {
          cx: width - m.right + 8, cy: l.yy, r: 3, fill: l.s.color,
          stroke: SURFACE, 'stroke-width': 2
        }));
        svg.appendChild(el('text', {
          x: width - m.right + 16, y: l.yy + 4, fill: INK_MUTED, 'font-size': 11
        }, l.s.label));
      });
    }

    // Reference events (headline view only)
    if (conf.events && !narrow) {
      EVENTS.forEach(ev => {
        const i = rows.findIndex(r => r.date.slice(0, 7) === ev.month);
        if (i < 0) return;
        const px = main.x(i);
        const py = main.y(rows[i][conf.series[0].key]);
        const dy = ev.side === 'above' ? -10 : 10;
        svg.appendChild(el('line', {
          x1: px, x2: px, y1: py + (dy < 0 ? -3 : 3), y2: py + dy,
          stroke: AXIS, 'stroke-width': 1
        }));
        svg.appendChild(el('circle', {
          cx: px, cy: py, r: 3, fill: conf.series[0].color,
          stroke: SURFACE, 'stroke-width': 1.5
        }));
        const anchor = px < m.left + 60 ? 'start' : px > width - m.right - 60 ? 'end' : 'middle';
        // White halo so a label stays readable where it crosses the line.
        svg.appendChild(el('text', {
          x: px, y: py + dy + (dy < 0 ? -4 : 13), 'text-anchor': anchor,
          fill: '#52514e', 'font-size': 10.5,
          stroke: SURFACE, 'stroke-width': 3, 'stroke-linejoin': 'round',
          'paint-order': 'stroke fill'
        }, ev.label));
      });
    }

    // Hover layer — one crosshair per panel, one dot per series
    const crosshairs = panels.map(p => {
      const line = el('line', {
        y1: p.top, y2: p.top + p.h, stroke: AXIS, 'stroke-width': 1, visibility: 'hidden'
      });
      svg.appendChild(line);
      return line;
    });
    const dots = [];
    panels.forEach(p => p.series.forEach(s => {
      const c = el('circle', {
        r: 4, fill: s.color, stroke: SURFACE, 'stroke-width': 2, visibility: 'hidden'
      });
      svg.appendChild(c);
      dots.push({ node: c, panel: p, series: s });
    }));

    const hits = panels.map(p => {
      const rect = el('rect', {
        x: p.left, y: p.top, width: p.w, height: p.h, fill: 'transparent'
      });
      svg.appendChild(rect);
      return rect;
    });

    function indexFromX(clientX) {
      const box = svg.getBoundingClientRect();
      const px = ((clientX - box.left) / box.width) * width;
      const rel = Math.min(1, Math.max(0,
        (((px - m.left) % (panelW + gapX)) / panelW)));
      return Math.min(rows.length - 1, Math.max(0, Math.round(rel * (rows.length - 1))));
    }

    function showCursor(i) {
      cursor = i;
      const r = rows[i];
      panels.forEach((p, k) => {
        crosshairs[k].setAttribute('x1', p.x(i));
        crosshairs[k].setAttribute('x2', p.x(i));
        crosshairs[k].setAttribute('visibility', 'visible');
      });
      dots.forEach(d => {
        d.node.setAttribute('cx', d.panel.x(i));
        d.node.setAttribute('cy', d.panel.y(r[d.series.key]));
        d.node.setAttribute('visibility', 'visible');
      });
      tooltip.hidden = false;
      tooltip.innerHTML = '<b>' + monthLabel(r.date) + '</b><br>' +
        conf.series.map(s =>
          '<span style="color:' + s.color + '">●</span> ' + s.label +
          ' <span class="v">' + fmt(r[s.key]) + '</span>'
        ).join('<br>');
      const box = svg.getBoundingClientRect();
      const scale = box.width / width;
      const left = main.x(i) * scale;
      const tw = tooltip.offsetWidth;
      tooltip.style.left = Math.min(box.width - tw - 4, Math.max(4, left + 12)) + 'px';
      tooltip.style.top = (m.top * scale + 4) + 'px';
    }

    function hideCursor() {
      cursor = -1;
      crosshairs.forEach(c => c.setAttribute('visibility', 'hidden'));
      dots.forEach(d => d.node.setAttribute('visibility', 'hidden'));
      tooltip.hidden = true;
    }

    hits.forEach(hit => {
      hit.addEventListener('pointermove', e => showCursor(indexFromX(e.clientX)));
      hit.addEventListener('pointerleave', hideCursor);
    });
    svg.onkeydown = e => {
      const step = e.shiftKey ? 12 : 1;
      let i = cursor < 0 ? rows.length - 1 : cursor;
      if (e.key === 'ArrowRight') i = Math.min(rows.length - 1, i + step);
      else if (e.key === 'ArrowLeft') i = Math.max(0, i - step);
      else if (e.key === 'Home') i = 0;
      else if (e.key === 'End') i = rows.length - 1;
      else if (e.key === 'Escape') { hideCursor(); svg.blur(); return; }
      else return;
      e.preventDefault();
      showCursor(i);
    };
    svg.addEventListener('blur', hideCursor);

    // Legend — present whenever two or more series share a plot. A single
    // series is named by the caption, and faceted panels carry their own
    // titles, so neither needs a legend box.
    legendEl.innerHTML = conf.series.length > 1 && !facet
      ? conf.series.map(s =>
        '<span style="color:' + s.color + '"><i></i><span style="color:var(--text-muted)">' +
        s.label + '</span></span>').join('')
      : '';
    captionEl.innerHTML = conf.caption;
  }

  function renderStats() {
    const host = document.getElementById('stat-row');
    if (!host) return;
    const last = rows[rows.length - 1];
    let hi = rows[0];
    rows.forEach(r => { if (r.gprnk > hi.gprnk) hi = r; });
    host.innerHTML = [
      ['Latest month', fmt(last.gprnk), monthLabel(last.date)],
      ['Highest on record', fmt(hi.gprnk), monthLabel(hi.date)],
      ['Base period', '100', 'Mean over 1995–2016']
    ].map(([label, value, note]) =>
      '<div class="stat"><div class="stat-label">' + label + '</div>' +
      '<div class="stat-value">' + value + '</div>' +
      '<div class="stat-note">' + note + '</div></div>'
    ).join('');
  }

  function renderTable() {
    const host = document.getElementById('table-host');
    if (!host) return;
    const head = '<tr><th>Month</th>' +
      ALL_COLUMNS.map(c => '<th class="num">' + c + '</th>').join('') + '</tr>';
    const body = rows.map(r =>
      '<tr><td class="mon">' + r.date + '</td>' +
      ALL_COLUMNS.map(c => '<td class="num">' + fmt(r[c]) + '</td>').join('') + '</tr>'
    ).join('');
    host.innerHTML = '<table class="data-table"><thead>' + head +
      '</thead><tbody>' + body + '</tbody></table>';
  }

  function renderCoverage() {
    const line = document.getElementById('coverage-line');
    if (!line) return;
    line.textContent = rows.length + ' monthly observations (' +
      rows[0].date.slice(0, 7) + ' – ' + rows[rows.length - 1].date.slice(0, 7) + ')';
  }

  document.addEventListener('DOMContentLoaded', async () => {
    if (!svg || !wrap) return;

    document.querySelectorAll('[data-view]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('[data-view]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        view = btn.getAttribute('data-view');
        cursor = -1;
        tooltip.hidden = true;
        draw();
      });
    });

    try {
      const res = await fetch(CSV_PATH, { cache: 'no-cache' });
      if (!res.ok) throw new Error(res.status);
      rows = parseCsv(await res.text());
    } catch (err) {
      wrap.innerHTML = '<p style="color:var(--text-muted);font-size:0.9rem;">' +
        'The chart could not load. The data is available in the download links below.</p>';
      return;
    }

    draw();
    renderStats();
    renderCoverage();

    const details = document.querySelector('details.table-view');
    if (details) {
      details.addEventListener('toggle', function once() {
        if (details.open) { renderTable(); details.removeEventListener('toggle', once); }
      });
    }

    let timer = null;
    let lastWidth = wrap.clientWidth;
    window.addEventListener('resize', () => {
      if (wrap.clientWidth === lastWidth) return;
      lastWidth = wrap.clientWidth;
      clearTimeout(timer);
      timer = setTimeout(draw, 120);
    });
  });
})();
