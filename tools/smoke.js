#!/usr/bin/env node
// Smoke test for the built page. Run after `python3 tools/build.py`:  node tools/smoke.js [page.html]
// Opens index.html in headless Chromium with the network blocked (photos and fonts are remote, so
// the page must work without them), visits every view, and fails on any JavaScript error or on a
// count that disagrees with data/cars.json. Uses the Playwright pre-installed in cloud sessions.
'use strict';
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

    await go('#/stats');
    expect(await page.isVisible('#view-stats') && await n('#stats .chart-wrap svg') > 0, 'stats: view or power chart missing');

    await go('#/compare?ids=' + cars.slice(0, 2).map((c) => c.id).join(','));
    expect(await n('#compare table.cmp thead td') === 2, 'compare: expected 2 cars side by side');

    await go('#/');   // car-of-the-day hero: preview only, in place of the family strip
    expect(!(await page.isVisible('#masthead')) && await page.isVisible('#strip'), 'browse: the hero shows without the preview flag, or the family strip is gone');
    await go('#/?hero=1');
    expect(await page.isVisible('#masthead') && !(await page.isVisible('#strip')) && await n('#hero a.hero-tag[href^="#/m/"]') === 1,
      'hero preview #/?hero=1: hero, its car link, or the hidden family strip is wrong');
    await go('#/?family=Countach');
    expect(!(await page.isVisible('#masthead')) && page.url().includes('hero=1'), 'hero preview: should step aside while filtering and keep its flag');
    await go('#/');
    expect(await page.isVisible('#masthead'), 'hero preview: lost after filtering');
    await go('#/?hero=0');
    expect(!(await page.isVisible('#masthead')) && await page.isVisible('#strip'), 'hero preview: hero=0 does not turn it off');
  } finally {
    await browser.close();
  }
  if (problems.length) {
    console.error('smoke FAILED:\n- ' + problems.join('\n- '));
    process.exit(1);
  }
  console.log(`smoke OK: ${cars.length} cars; browse, filter, search, car pages, timeline, fast 10, stats, compare and the hero preview work with no JavaScript errors`);
})().catch((e) => { console.error('smoke FAILED: ' + e.message); process.exit(1); });
