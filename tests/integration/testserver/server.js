const express = require('express');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const dotenv = require('dotenv');



const app = express();
app.use(express.json());

const fixtures = path.resolve(__dirname, 'fixtures');

let currentScenario = 'happy-path';
// DC-020: 差分更新テストのため、実行時にページ本文を上書きできるようにする。
const pageOverrides = {};
// DC-022: 削除ページテストのため、sitemap記載URLを実行時に絞り込めるようにする。
let sitemapUrlFilter = null; // null = 制限なし。Set<string> を設定すると該当URLのみ配信。
// DC-027: ロック競合テストのため、応答に遅延を挿入できるようにする。
let responseDelayMs = 0;

function htmlPage(title, body, extraLinks = []) {
  const links = extraLinks.map((href) => `<a href="${href}">link</a>`).join('');
  return `<!DOCTYPE html><html><head><title>${title}</title></head><body><p>${body}</p>${links}</body></html>`;
}

function sitemapXml(urls) {
  const entries = urls.map((u) => `  <url><loc>${u}</loc></url>`).join('\n');
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${entries}\n</urlset>`;
}
dotenv.config({ path: ".env.test" })
const TESTSERVER_HOST = process.env.TESTSERVER_HOST
const TESTSERVER_PORT = process.env.TESTSERVER_PORT
const HOST = 'http://'+TESTSERVER_HOST + ':' + TESTSERVER_PORT;

// --- シナリオ別のページ定義 --------------------------------------------
// 各シナリオは { sitemapUrls, robots, pages } を返す。
// sitemapUrls が null の場合は /sitemap.xml 自体を404にする（フォールバッククロール誘発用）。

function baseRobots(extra = '') {
  return `User-agent: *\nAllow: /\n${extra}Sitemap: ${HOST}/sitemap.xml\n`;
}

const scenarioDefs = {
  'happy-path': () => ({
    sitemapUrls: [
      `${HOST}/pages/docs-guides.html`,
      `${HOST}/pages/blog-post1.html`,
    ],
    robots: baseRobots(),
    pages: {
      '/pages/docs-guides.html': () => htmlPage('Docs Guides', 'Documentation guide.'),
      '/pages/blog-post1.html': () => htmlPage('Blog Post 1', 'Blog content.'),
    },
  }),

  // DC-015: 重複ページ（同一本文のSHA256が一致する複数URL）
  'with-duplicates': () => ({
    sitemapUrls: [
      `${HOST}/pages/dup-old.html`,
      `${HOST}/pages/dup-new.html`,
    ],
    robots: baseRobots(),
    pages: {
      '/pages/dup-old.html': () => htmlPage('Duplicate Old', 'Identical duplicate content.'),
      '/pages/dup-new.html': () => htmlPage('Duplicate New', 'Identical duplicate content.'),
    },
  }),

  // DC-016: robots.txtでのDisallow
  'with-robots-deny': () => ({
    sitemapUrls: [
      `${HOST}/pages/docs-guides.html`,
      `${HOST}/pages/blog-post1.html`,
    ],
    robots: baseRobots('Disallow: /pages/blog-post1.html\n'),
    pages: {
      '/pages/docs-guides.html': () => htmlPage('Docs Guides', 'Documentation guide.'),
      '/pages/blog-post1.html': () => htmlPage('Blog Post 1', 'Blog content.'),
    },
  }),

  // DC-017 / DC-018: INCLUDE/EXCLUDE絞り込み、暗黙INCLUDE
  'with-include-exclude': () => ({
    sitemapUrls: [
      `${HOST}/pages/docs/guides.html`,
      `${HOST}/pages/blog/post1.html`,
    ],
    robots: baseRobots(),
    pages: {
      '/pages/docs/guides.html': () => htmlPage('Docs Guides', 'Documentation guide under /docs/.'),
      '/pages/blog/post1.html': () => htmlPage('Blog Post', 'Blog content under /blog/.'),
    },
  }),

  // DC-025用にも使えるerror-responses：404/429/5xxを返すURL群
  'error-responses': () => ({
    sitemapUrls: [
      `${HOST}/pages/ok.html`,
      `${HOST}/pages/not-found.html`,
      `${HOST}/pages/server-error.html`,
      `${HOST}/pages/too-many-requests.html`,
    ],
    robots: baseRobots(),
    pages: {
      '/pages/ok.html': () => htmlPage('OK Page', 'This page is fine.'),
      // /pages/not-found.html は意図的にpages定義に存在させず404を返す
      '/pages/server-error.html': { status: 500, body: 'Internal Server Error' },
      '/pages/too-many-requests.html': { status: 429, headers: { 'Retry-After': '1' }, body: 'Too Many Requests' },
    },
  }),

  // DC-029/DC-030: sitemap記載件数がMAX_PAGESを超える大量ページシナリオ
  'large-site': () => ({
    sitemapUrls: Array.from({ length: 20 }, (_, i) => `${HOST}/pages/large-${i}.html`),
    robots: baseRobots(),
    pages: Object.fromEntries(
      Array.from({ length: 20 }, (_, i) => [
        `/pages/large-${i}.html`,
        () => htmlPage(`Large Page ${i}`, `Content for large page number ${i}.`),
      ]),
    ),
  }),

  // DC-012/DC-029: sitemap不在（404）。リンクを辿るフォールバッククロール用に
  // 各ページが次のページへリンクするチェーンを構成する。
  'no-sitemap-fallback': () => ({
    sitemapUrls: null,
    robots: 'User-agent: *\nAllow: /\n', // Sitemap行なし
    pages: {
      '/': () => htmlPage('Root', 'Fallback root page.', ['/pages/fb-0.html']),
      ...Object.fromEntries(
        Array.from({ length: 50 }, (_, i) => [
          `/pages/fb-${i}.html`,
          () =>
            htmlPage(`Fallback Page ${i}`, `Fallback content ${i}.`, [
              `/pages/fb-${i + 1}.html`,
            ]),
        ]),
      ),
    },
  }),
};

function currentDef() {
  const factory = scenarioDefs[currentScenario] || scenarioDefs['happy-path'];
  return factory();
}

// --- 管理エンドポイント --------------------------------------------------

app.post('/__scenario__', (req, res) => {
  const { scenario } = req.body;
  if (!scenario || !scenarioDefs[scenario]) {
    return res.status(400).json({ error: 'unknown scenario' });
  }
  currentScenario = scenario;
  res.json({ scenario });
});

// DC-020: 特定ページの本文を実行時に上書きする（差分更新テスト用）。
app.post('/__override-page__', (req, res) => {
  const { pagePath, title, body } = req.body;
  if (!pagePath) {
    return res.status(400).json({ error: 'pagePath is required' });
  }
  pageOverrides[pagePath] = () => htmlPage(title || 'Overridden', body || 'Overridden content.');
  res.json({ status: 'ok' });
});

app.post('/__clear-overrides__', (req, res) => {
  for (const key of Object.keys(pageOverrides)) delete pageOverrides[key];
  res.json({ status: 'ok' });
});

// DC-022: sitemapに含めるURLを絞り込む（削除ページテスト用）。
app.post('/__sitemap-filter__', (req, res) => {
  const { urls } = req.body;
  sitemapUrlFilter = Array.isArray(urls) ? new Set(urls) : null;
  res.json({ status: 'ok' });
});

app.post('/__clear-sitemap-filter__', (req, res) => {
  sitemapUrlFilter = null;
  res.json({ status: 'ok' });
});

// DC-027: 応答遅延を設定する（ロック競合テスト用）。
app.post('/__delay__', (req, res) => {
  const { ms } = req.body;
  responseDelayMs = Number(ms) || 0;
  res.json({ status: 'ok', delayMs: responseDelayMs });
});

app.post('/__reset__', (req, res) => {
  currentScenario = 'happy-path';
  for (const key of Object.keys(pageOverrides)) delete pageOverrides[key];
  sitemapUrlFilter = null;
  responseDelayMs = 0;
  res.json({ status: 'ok' });
});

// --- 通常エンドポイント ---------------------------------------------------

function withDelay(handler) {
  return (req, res) => {
    if (responseDelayMs > 0) {
      setTimeout(() => handler(req, res), responseDelayMs);
    } else {
      handler(req, res);
    }
  };
}

app.get(
  '/robots.txt',
  withDelay((req, res) => {
    const def = currentDef();
    res.type('text/plain');
    res.send(def.robots);
  }),
);

app.get(
  '/sitemap.xml',
  withDelay((req, res) => {
    const def = currentDef();
    if (def.sitemapUrls === null) {
      return res.status(404).send('not found');
    }
    let urls = def.sitemapUrls;
    if (sitemapUrlFilter) {
      urls = urls.filter((u) => sitemapUrlFilter.has(u));
    }
    res.type('application/xml');
    res.send(sitemapXml(urls));
  }),
);

function resolvePageHandler(pagePath) {
  if (pageOverrides[pagePath]) return pageOverrides[pagePath];
  const def = currentDef();
  return def.pages ? def.pages[pagePath] : undefined;
}

function servePage(req, res, pagePath) {
  const handler = resolvePageHandler(pagePath);

  if (handler === undefined) {
    return res.status(404).send('not found');
  }

  if (typeof handler === 'function') {
    const html = handler();

    // ETag/If-None-Match による304対応（DC-019）。
    const etag = '"' + crypto.createHash('md5').update(html).digest('hex') + '"';
    if (req.headers['if-none-match'] === etag) {
      res.status(304);
      res.set('ETag', etag);
      return res.end();
    }
    res.set('ETag', etag);
    res.type('text/html');
    return res.send(html);
  }

  // { status, body, headers } 形式（エラー応答シナリオ用）。
  const { status = 200, body = '', headers = {} } = handler;
  Object.entries(headers).forEach(([k, v]) => res.set(k, v));
  res.status(status);
  res.type(status >= 400 ? 'text/plain' : 'text/html');
  return res.send(body);
}

app.get(
  '/',
  withDelay((req, res) => servePage(req, res, '/')),
);

app.get(
  /^\/pages\/(.+)$/,
  withDelay((req, res) => servePage(req, res, `/pages/${req.params[0]}`)),
);

// 元のfixtures配下ファイルへの後方互換アクセス（旧テスト用）。
app.get('/fixtures/pages/:name', (req, res) => {
  const filePath = path.join(fixtures, 'pages', req.params.name);
  if (!fs.existsSync(filePath)) {
    return res.status(404).send('not found');
  }
  res.type('text/html');
  res.send(fs.readFileSync(filePath, 'utf8'));
});

app.listen(Number(TESTSERVER_POST), () => {
  console.log('testserver listening on ' + HOST);
});
