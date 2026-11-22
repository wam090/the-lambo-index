#!/usr/bin/env node
// Smoke test for the built page. Run after `python3 tools/build.py`:  node tools/smoke.js [page.html]
// Opens index.html in headless Chromium with the network blocked (photos and fonts are remote, so
// the page must work without them), visits every view, and fails on any JavaScript error or on a
// count that disagrees with data/cars.json. Uses the Playwright pre-installed in cloud sessions.
'use strict';
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.join(__dirname, '..');
const PAGE = path.resolve(process.argv[2] || path.join(ROOT, 'index.html'));
const { cars } = require(path.join(ROOT, 'data', 'cars.json'));
const problems = [];
const expect = (ok, msg) => { if (!ok) problems.push(msg); };

(async () => {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();
    await page.route(/^https?:/, (r) => r.abort());
    page.on('pageerror', (e) => problems.push(`JavaScript error: ${e.message}`));
    let localHits = 0;   // no visit counting on file:// (or http://)
    page.on('request', (r) => { if (r.url().includes('goatcounter')) localHits++; });
    page.on('console', (m) => {
      if (m.type() === 'error' && !/Failed to load resource|net::ERR_/.test(m.text())) problems.push(`console.error: ${m.text()}`);
    });
    const go = async (hash) => { await page.evaluate((h) => { location.hash = h; }, hash); await page.waitForTimeout(200); };
    const count = async () => +(((await page.textContent('#count')) || '').match(/[\d,]+/) || ['-1'])[0].replace(/,/g, '');
    const n = (sel) => page.locator(sel).count();

    await page.goto('file://' + PAGE);
    await page.waitForSelector('#grid .card', { timeout: 10000 });
    expect(await count() === cars.length, `browse: count shows ${await count()}, data has ${cars.length} cars`);

    const perFamily = {};
    for (const c of cars) perFamily[c.family] = (perFamily[c.family] || 0) + 1;
    const [fam, famN] = Object.entries(perFamily).sort((a, b) => b[1] - a[1])[0];
    await go('#/?family=' + encodeURIComponent(fam));
    expect(await count() === famN, `filter family=${fam}: count shows ${await count()}, expected ${famN}`);

    await go('#/');
    await page.fill('#q', cars[0].name);
    await page.waitForTimeout(400);
    expect(await count() >= 1, `search "${cars[0].name}": no results`);
    await page.fill('#q', '');
    await page.waitForTimeout(400);

    for (const c of [cars.find((x) => x.imgs.length), cars.find((x) => !x.imgs.length)].filter(Boolean)) {
      await go('#/m/' + c.id);
      expect(await page.isVisible('#sheet'), `car page #/m/${c.id}: not shown`);
      expect(((await page.textContent('#sheet-panel')) || '').includes(c.name), `car page #/m/${c.id}: name "${c.name}" missing`);
    }

    const withPhoto = cars.find((c) => c.imgs.length);
    await go('#/m/' + withPhoto.id);
    expect(await n('#stage-credit a[href^="https://github.com/wam090/the-lambo-index/issues/new"]') === 1, 'car page: "Report a photo" link missing');
    await go('#/timeline');
    const debuts = cars.filter((c) => c.debut).length;
    expect(await page.isVisible('#view-timeline'), 'timeline: view not shown');
    expect(await n('#timeline .tl-item') === cars.length, `timeline: ${await n('#timeline .tl-item')} entries, expected ${cars.length}`);
    expect(await n('#timeline .tl-item.debut') === debuts, `timeline: ${await n('#timeline .tl-item.debut')} debut frames, expected ${debuts}`);
    const framedKinds = ['Limited series', 'One-off', 'Race car'];
    const plainDebuts = cars.filter((c) => c.debut && !framedKinds.includes(c.kind)).length;
    expect(await n('#timeline .tl-item .frame') === plainDebuts, `timeline: ${await n('#timeline .tl-item .frame')} orange frames, expected ${plainDebuts} (debuts without a higher frame)`);
    for (const [cls, kind] of [['lim', 'Limited series'], ['one', 'One-off'], ['race', 'Race car']]) {
      const want = cars.filter((c) => c.kind === kind).length;
      const got = await n(`#timeline .tl-item.${cls}`);
      expect(got === want, `timeline: ${got} ${kind} frames, expected ${want}`);
    }

    await go('#/timeline?only=one');
    const shownOne = await page.$$eval('#timeline .tl-item', (els) => els.filter((e) => e.offsetParent !== null).length);
    const oneOffs = cars.filter((c) => c.kind === 'One-off').length;
    expect(shownOne === oneOffs, `timeline legend filter: ${shownOne} cars shown for One-off, expected ${oneOffs}`);

    await go('#/timeline?only=debut,race');
    const shownBoth = await page.$$eval('#timeline .tl-item', (els) => els.filter((e) => e.offsetParent !== null).length);
    const debutRace = cars.filter((c) => c.debut && c.kind === 'Race car').length;
    expect(shownBoth === debutRace, `timeline legend filter: ${shownBoth} cars shown for Debut + Race car, expected ${debutRace}`);

    await go('#/fast10');
    expect(await page.isVisible('#view-fast') && await n('#fast .f10') === 10, `fast 10: ${await n('#fast .f10')} entries, expected 10`);

    await go('#/stats');   // the Stats page was removed (2026-11-11): old links land on Browse
    expect(await page.isVisible('#view-browse') && await n('a[href="#/stats"]') === 0 && !(await page.$('#view-stats')),
      'stats: old #/stats link should show Browse, and no Stats view or link should remain');

    await go('#/compare?ids=' + cars.slice(0, 2).map((c) => c.id).join(','));
    expect(await n('#compare table.cmp thead td') === 2, 'compare: expected 2 cars side by side');

    await go('#/');   // the car of the day replaces the family strip and steps aside while filtering
    expect(await page.isVisible('#masthead') && !(await page.isVisible('#strip')) && await n('#hero a.hero-tag[href^="#/m/"]') === 1
      && await n('#hero .hero-credit a[href^="https://"]') >= 1, 'browse: hero, its car link, its credit links or the hidden family strip is wrong');
    await go('#/?family=Countach');
    expect(!(await page.isVisible('#masthead')), 'browse: the hero should step aside while filtering');

    expect(!(await page.locator('meta[name="robots"]').evaluateAll((ms) => ms.some((m) => /noindex/i.test(m.content)))),
      'head: the page is live (2026-11-12); a robots noindex tag is back');

    // Footer (2026-11-12): the data line, then the fan-site, photo and visit notes, on every view.
    const NOTES = ['Unofficial fan site, not affiliated with Automobili Lamborghini', 'Photos credited to their authors, under their licences', 'Visits counted anonymously, no cookies'];
    const nPhotos = cars.reduce((s, c) => s + c.imgs.length, 0).toLocaleString('en-US');
    const DATA = new RegExp(`^Index compiled \\d{4}-\\d{2}-\\d{2} · ${cars.length} cars · ${nPhotos} photos$`);
    for (const h of ['#/', '#/m/' + cars[0].id, '#/timeline', '#/fast10', '#/compare?ids=' + cars.slice(0, 2).map((c) => c.id).join(','), '#/stats']) {
      await go(h);
      const notes = await page.$$eval('#foot-notes li', (els) => els.map((e) => e.textContent.trim()));
      expect(await page.isVisible('#fan-note') && JSON.stringify(notes) === JSON.stringify(NOTES), `footer: notes missing or changed on ${h}: ${JSON.stringify(notes)}`);
      expect(DATA.test(((await page.textContent('#foot-l')) || '').trim()), `footer: data line wrong on ${h}`);
    }
    expect(localHits === 0, `visits: ${localHits} counter requests from a file:// page, expected none`);

    // Visit counting (2026-11-12): served from a fake https origin; the pixel is intercepted, nothing leaves.
    const live = await browser.newPage();
    const hits = [];
    live.on('pageerror', (e) => problems.push(`JavaScript error (https): ${e.message}`));
    await live.route(/^https?:/, (r) => {
      const u = new URL(r.request().url());
      if (u.origin === 'https://lambo.test') return r.fulfill({ contentType: 'text/html', path: PAGE });
      if (u.hostname.endsWith('goatcounter.com')) { hits.push(u); return r.fulfill({ contentType: 'image/gif', body: Buffer.from('R0lGODlhAQABAAAAACw=', 'base64') }); }
      return r.abort();
    });
    const lgo = async (hash) => { await live.evaluate((h) => { location.hash = h; }, hash); await live.waitForTimeout(200); };
    const REF = 'https://example.org/somewhere';
    await live.goto('https://lambo.test/#/', { referer: REF });
    await live.waitForSelector('#grid .card', { timeout: 10000 });
    await live.waitForTimeout(200);
    const c0 = cars.find((c) => /[^a-z0-9-]/i.test(c.name)) || cars[0];
    for (const h of ['#/?family=' + encodeURIComponent(fam), '#/m/' + c0.id, '#/stats', '#/m/<b>x?y=1', '#/timeline', '#/fast10', '#/compare']) await lgo(h);
    const ps = hits.map((u) => u.searchParams.get('p'));
    const want = ['/', '/m/' + c0.id, '/', '/timeline', '/fast10', '/compare'];
    expect(JSON.stringify(ps) === JSON.stringify(want), `visits: counted ${JSON.stringify(ps)}, expected ${JSON.stringify(want)} (filters and unknown ids do not count; #/stats counts as Browse)`);
    expect(hits.every((u) => u.origin + u.pathname === 'https://thelamboindex.goatcounter.com/count'), 'visits: a count went to the wrong address');
    expect(hits[0] && hits[0].searchParams.get('r') === REF && hits.slice(1).every((u) => !u.searchParams.has('r')), 'visits: the referrer should go with the first count only');
    expect(hits[1] && (hits[1].searchParams.get('t') || '').startsWith(c0.name), `visits: car page title not sent for ${c0.id}`);
    expect(new Set(hits.map((u) => u.searchParams.get('rnd'))).size === hits.length, 'visits: each count needs its own cache-buster');

    // Static car pages (tools/STATIC_PAGES.md, 2026-11-22): the repo is served at its real address from
    // disk, the network stays blocked. Every car page is checked, and its facts compared with the app's.
    const SITE = 'https://wam090.github.io/the-lambo-index/';
    const BASE = '/the-lambo-index/';
    const PAGE_CSP = `default-src 'none'; style-src ${SITE}src/page.css; font-src ${SITE}fonts/; img-src https://thumb.wikimedia.org https://live.staticflickr.com https://thelamboindex.goatcounter.com ${SITE}favicon.svg; base-uri 'none'; form-action 'none'`;
    const OG_OK = /^(Public domain|CC0|CC BY(-SA)? \d\.\d)$/;
    const TYPES = { html: 'text/html', css: 'text/css', svg: 'image/svg+xml', woff2: 'font/woff2', txt: 'text/plain', xml: 'application/xml', json: 'application/json' };
    const serve = (pg) => pg.route(/^https?:/, (r) => {
      const u = new URL(r.request().url());
      if (u.origin !== 'https://wam090.github.io' || !u.pathname.startsWith(BASE)) return r.abort();
      let rel = decodeURIComponent(u.pathname.slice(BASE.length));
      if (rel === '' || rel.endsWith('/')) rel += 'index.html';
      const f = path.join(ROOT, rel);
      if (!f.startsWith(ROOT + path.sep) || !fs.existsSync(f) || !fs.statSync(f).isFile()) return r.fulfill({ status: 404, body: 'not found' });
      return r.fulfill({ path: f, contentType: TYPES[path.extname(f).slice(1)] || 'application/octet-stream' });
    });
    const sp = await browser.newPage();
    await serve(sp);
    sp.on('pageerror', (e) => problems.push(`static page: JavaScript error: ${e.message}`));
    sp.on('console', (m) => { if (m.type() === 'error' && !/Failed to load resource|net::ERR_/.test(m.text())) problems.push(`static page ${sp.url()}: console.error: ${m.text()}`); });
    const app = await browser.newPage();
    await serve(app);
    await app.goto(SITE + '#/');
    await app.waitForSelector('#grid .card', { timeout: 10000 });
    expect(await app.$eval('link[rel="canonical"]', (l) => l.href).catch(() => '') === SITE, 'index.html: canonical link missing or wrong');
    const facts = (pg, scope) => pg.$$eval(`${scope} dl.facts dt`, (dts) => dts.map((dt) => [dt.textContent.trim(), dt.nextElementSibling.textContent.replace(/\s+/g, ' ').trim()]));
    const meta = (prop) => sp.$eval(`meta[property="${prop}"]`, (m) => m.content).catch(() => null);
    for (const c of cars) {
      const url = `${SITE}m/${c.id}/`;
      const res = await sp.goto(url);
      const bad = (msg) => problems.push(`static page m/${c.id}/: ${msg}`);
      if (!res || res.status() !== 200) { bad('not found'); continue; }
      if ((await sp.title()).indexOf(c.name) < 0) bad('title lacks the car name');
      if ((await sp.textContent('h1')) !== c.name) bad('h1 is not the car name');
      if (await sp.$eval('link[rel="canonical"]', (l) => l.href).catch(() => '') !== url || await meta('og:url') !== url) bad('canonical or og:url wrong');
      if (await sp.locator('script').count() !== 0) bad('holds a script element');
      if (await sp.$eval('meta[http-equiv="Content-Security-Policy"]', (m) => m.content).catch(() => '') !== PAGE_CSP) bad('CSP missing or changed');
      if (await sp.evaluate(() => getComputedStyle(document.body).backgroundColor) !== 'rgb(12, 11, 10)') bad('stylesheet not applied');
      if (await sp.locator('meta[name="robots"]').evaluateAll((ms) => ms.some((m) => /noindex/i.test(m.content)))) bad('noindex');
      const og = c.imgs.find((im) => OG_OK.test(im.l || '') && !im.t.startsWith('nonfree:'));
      const ogImg = await meta('og:image');
      const ogHost = ogImg ? new URL(ogImg).hostname : '';
      if (og ? !(ogImg && ['thumb.wikimedia.org', 'live.staticflickr.com'].includes(ogHost) && ogImg.includes(og.sz ? og.sz[og.sz.length - 1][1] : og.n)) : ogImg !== null) bad(`og:image ${ogImg} does not follow the licence rule`);
      const want = await facts(sp, 'main');
      await app.evaluate((h) => { location.hash = h; }, '#/m/' + c.id);
      await app.waitForFunction((n) => (document.querySelector('#d-title') || {}).textContent === n, c.name, { timeout: 5000 }).catch(() => bad('the app did not open the car'));
      const got = await facts(app, '#sheet-panel');
      if (JSON.stringify(want) !== JSON.stringify(got)) bad(`facts differ from the app: ${JSON.stringify(want)} vs ${JSON.stringify(got)}`);
      if (await sp.$eval('a.btn.primary', (a) => a.href).catch(() => '') !== `${SITE}#/m/${c.id}`) bad('link into the app wrong');
      if (JSON.stringify(await sp.$$eval('footer li', (els) => els.map((e) => e.textContent.trim()))) !== JSON.stringify(NOTES)) bad('footer notes missing or changed');
      if (!(await sp.$eval('img.px', (i) => i.getAttribute('src')).catch(() => '')).includes(`count?p=/m/${c.id}/&`)) bad('visit pixel missing or wrong');
    }
    const ids = new Set(cars.map((c) => c.id));
    const res = await sp.goto(SITE + 'm/');
    const listed = (await sp.$$eval('main a[href]', (as) => as.map((a) => a.getAttribute('href')))).filter((h) => /^[a-z0-9-]+\/$/.test(h)).map((h) => h.slice(0, -1));
    expect(res && res.status() === 200 && listed.length === ids.size && listed.every((id) => ids.has(id)), `static m/: lists ${listed.length} cars, expected ${ids.size}`);
    expect(await sp.locator('script').count() === 0 && await sp.$eval('link[rel="canonical"]', (l) => l.href).catch(() => '') === SITE + 'm/', 'static m/: script or canonical wrong');
    const onDisk = fs.readdirSync(path.join(ROOT, 'm')).filter((d) => fs.existsSync(path.join(ROOT, 'm', d, 'index.html')));
    expect(onDisk.length === ids.size && onDisk.every((d) => ids.has(d)), `static pages: ${onDisk.length} on disk under m/, expected ${ids.size} (stale pages?)`);
    const sitemap = fs.readFileSync(path.join(ROOT, 'sitemap.xml'), 'utf8');
    const locs = [...sitemap.matchAll(/<url><loc>([^<]+)<\/loc><lastmod>\d{4}-\d{2}-\d{2}<\/lastmod><\/url>/g)].map((m) => m[1]);
    expect(JSON.stringify(locs) === JSON.stringify([SITE, SITE + 'm/', ...cars.map((c) => `${SITE}m/${c.id}/`)]), `sitemap.xml: ${locs.length} URLs, expected home, m/ and ${cars.length} car pages`);
    const keys = fs.readdirSync(ROOT).filter((f) => /^[0-9a-f]{32}\.txt$/.test(f));
    expect(keys.length === 1 && fs.readFileSync(path.join(ROOT, keys[0]), 'utf8') === keys[0].slice(0, 32), 'IndexNow key file missing, doubled or wrong');
  } finally {
    await browser.close();
  }
  if (problems.length) {
    console.error('smoke FAILED:\n- ' + problems.join('\n- '));
    process.exit(1);
  }
  console.log(`smoke OK: ${cars.length} cars; browse, filter, search, car pages, timeline, fast 10, compare, old stats links, the hero, the footer, visit counting, no noindex and ${cars.length} static car pages work with no JavaScript errors`);
})().catch((e) => { console.error('smoke FAILED: ' + e.message); process.exit(1); });
