/**
 * Auto-renders the 4 research-interest cards (and optional Current Projects
 * list) by scanning data/publications.json + data/current-projects.json and
 * picking the most recent matching item per category via keyword scoring.
 *
 * To make a new publication or project surface here, just add it to the
 * relevant JSON file — no code changes needed. Categories are fixed to four.
 */
(function () {
  'use strict';

  const CATEGORIES = [
    {
      id: 'nk-economy',
      title: 'North Korean Economy',
      description: 'Marketization, price formation, border-closure effects, and the evolution of economic strategy under successive Party Congresses.',
      keywords: [
        'marketization', 'price formation', 'border closure', 'border closures',
        'party congress', 'five-year plan', 'regional development', '20×10', '20x10',
        'dollarization', 'kim jong-un regime', 'positive growth', 'livelihoods',
        'economic plan', 'market policy', 'fiscal', 'seigniorage',
        '시장화', '시장 물가', '환율', '당대회',
        '경제계획', '경제정책', '우리식 경제관리',
        '시장정책', '북한경제', '시장물가'
      ]
    },
    {
      id: 'foreign-relations',
      title: 'Foreign Economic Relations: China & Russia',
      description: 'North Korea’s trade with China (firm- and aggregate-level), the economic implications of strengthened North Korea–Russia ties amid the Russia–Ukraine war, and the structural reconfiguration of the regional economy linking Russia’s Far East, Northeast China, and the northern Korean Peninsula under deepening North Korea–China–Russia cooperation.',
      keywords: [
        'china', 'russia', 'russia–ukraine', 'russia-ukraine',
        'sanctions', 'firm-level', 'processing trade', 'supply chain',
        'north korea-china', 'north korea–china', 'cooperation with russia',
        'trilateral', 'far east', 'northeast china', 'regional economy',
        'logistics', 'energy cooperation', 'labor mobility',
        '중국', '러시아', '중러북', '북중러', '미중',
        '단둥', '가공무역', '북중', '북·중',
        '북-중', '동북3성', '대중국 의존도',
        '공급망', '극동', '북방경제'
      ]
    },
    {
      id: 'unification',
      title: 'Unification & Economic Integration',
      description: 'Inter-Korean geopolitical risk and its transmission to corporate investment, stock returns, and financial markets; the political economy of public attitudes toward unification; historical perspectives on Korean economic integration.',
      keywords: [
        'geopolitical', 'inter-korea', 'inter-korean', 'unification',
        'integration', 'stock returns', 'public opinion', 'corporate investment',
        'gprnk', 'real options',
        'inter-korean economic cooperation', 'knowledge partnership',
        '남북', '통일', '경협', '지정학',
        '통일의식', '국민정체성', '반이민',
        '남북경협'
      ]
    },
    {
      id: 'refugees',
      title: 'North Korean Refugees',
      description: 'Labor-market assimilation, health trajectories and chronic disease, early-life nutritional shocks, and subjective well-being among North Korean defectors resettled in South Korea.',
      keywords: [
        'defector', 'defectors', 'refugee', 'refugees', 'resettlement',
        'assimilation', 'mental health', 'health status', 'happiness',
        'financial behaviors', 'labor market participation', 'health-seeking',
        'famine', 'early-life shock', 'early-life', 'labor market',
        '북한이탈주민', '탈북', '신용행태',
        '정착', '사회적 지지', '고난의 행군'
      ]
    }
  ];

  function scoreItem(item, cat) {
    const text = [
      item.title || '', item.book || '', item.journal || '',
      item.note || '', (item.tags || []).join(' ')
    ].join(' ').toLowerCase();
    let s = 0;
    for (const kw of cat.keywords) {
      const k = kw.toLowerCase();
      if (k && text.includes(k)) s += k.length > 6 ? 2 : 1;
    }
    return s;
  }

  // EAI publishes Global NK 논평 in both English (commentary-en) and Korean
  // (commentary-kr, journal "동아시아연구원"). Counting both would double-surface
  // the same piece. Only the English version is scored. Standalone Korean
  // commentaries (e.g., 인천대 중국학술원 관행중국) are preserved.
  function isEAIKoreanTranslation(it) {
    return it.type === 'commentary-kr' && it.journal === '동아시아연구원';
  }

  function pickLatest(items, cat) {
    const matched = items
      .map(it => ({ it, s: scoreItem(it, cat) }))
      .filter(x => x.s > 0 && !isEAIKoreanTranslation(x.it))
      .sort((a, b) => {
        const ao = a.it._ongoing ? 1 : 0;
        const bo = b.it._ongoing ? 1 : 0;
        if (ao !== bo) return bo - ao;
        const ay = a.it.year || 0, by = b.it.year || 0;
        if (by !== ay) return by - ay;
        return (b.it.month || 0) - (a.it.month || 0);
      });
    return matched.length ? matched[0].it : null;
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }

  function highlightHtml(item) {
    if (!item) return '';
    const titleHtml = item.url
      ? `<a href="${esc(item.url)}" target="_blank" rel="noopener">${esc(item.title)}</a>`
      : esc(item.title);
    const venue = item.journal || item.book || item.publisher;
    const venueHtml = venue ? `, <em>${esc(venue)}</em>` : '';
    let yearStr = '';
    if (item._ongoing) {
      yearStr = '';
    } else if (item.note && /forthcoming/i.test(item.note)) {
      yearStr = item.year ? `${item.year}, forthcoming` : 'forthcoming';
    } else if (item.year) {
      yearStr = String(item.year);
    }
    const label = item._ongoing ? 'Current project' : 'Latest';
    const tail = yearStr ? ` (${esc(yearStr)})` : '';
    return `<div class="research-card-latest"><span class="research-card-latest-label">${label}</span> ${titleHtml}${venueHtml}${tail}.</div>`;
  }

  async function getJson(path) {
    try {
      const r = await fetch(path);
      if (!r.ok) return null;
      return await r.json();
    } catch (e) {
      return null;
    }
  }

  function renderInterests(grid, items) {
    grid.innerHTML = CATEGORIES.map(cat => {
      const latest = pickLatest(items, cat);
      return `
        <div class="research-card" data-category="${cat.id}">
          <div class="research-card-title">${esc(cat.title)}</div>
          <p>${cat.description}</p>
          ${highlightHtml(latest)}
        </div>
      `;
    }).join('');
  }

  function renderProjects(container, projects) {
    container.innerHTML = projects.map(p => {
      const titleHtml = p.url
        ? `<a href="${esc(p.url)}" target="_blank" rel="noopener">${esc(p.title)}</a>`
        : esc(p.title);
      return `
        <div class="course-item">
          <div class="course-title">${titleHtml}</div>
          <div class="course-meta">${p.meta || ''}</div>
          <div class="course-desc">${p.description || ''}</div>
        </div>
      `;
    }).join('');
  }

  document.addEventListener('DOMContentLoaded', async () => {
    const grid = document.getElementById('research-grid');
    const projectsEl = document.getElementById('current-projects');
    if (!grid && !projectsEl) return;

    const [pubs, projects] = await Promise.all([
      getJson('data/publications.json'),
      getJson('data/current-projects.json')
    ]);

    if (projectsEl && Array.isArray(projects) && projects.length) {
      renderProjects(projectsEl, projects);
    }

    if (grid) {
      const items = [];
      if (Array.isArray(projects)) {
        projects.forEach(p => items.push(Object.assign({ _ongoing: true }, p)));
      }
      if (Array.isArray(pubs)) items.push(...pubs);
      if (items.length) renderInterests(grid, items);
    }
  });
})();
