/* Deterministic assertions against the engine sliced verbatim out of index.html.
   Word pass only: no network, no reranker, so every number here is repeatable.
   Run:  node tools/search-test/run.js
   First regenerate the engine slice after any edit to the search functions:
     "C:\Users\Ali Al Mokdad\AppData\Local\Python\bin\python.exe" tools/search-test/extract-engine.py */
const fs = require('fs');
const E = require('./engine.gen.js');
const path = require('path');
const REPO = path.resolve(__dirname, '..', '..');
const data = JSON.parse(fs.readFileSync(path.join(REPO, 'data.json'), 'utf8'));
const KEY = {}; data.keys.forEach((k, i) => KEY[k] = i);
const val = (r, k) => String(r[KEY[k]] == null ? '' : r[KEY[k]]).trim();

const SEARCH_FIELDS = ['name','type','country','city','area','focus','contact','title'];
const ROWS = data.rows;
const NORM = new Map();
ROWS.forEach(r => {
  const all = E.norm(SEARCH_FIELDS.map(k => val(r, k)).join(' '));
  const nm = E.norm(val(r, 'name'));
  NORM.set(r, { all, nm, pad: ' ' + all + ' ', npad: ' ' + nm + ' ',
    flen: E.norm(val(r, 'focus')).length });
});
E.setCorpus(ROWS, NORM);

/* the same policy computeFiltered uses: every word first, part of them only if none */
function search(q) {
  const P = E.plan(q);
  if (!P) return { rows: ROWS.slice(), partial: false, related: 0 };
  const strict = [], loose = [], SC = new Map();
  ROWS.forEach(r => {
    const sc = E.scoreRow(r, P);
    if (!sc) return;
    SC.set(r, sc);
    (sc.tier === 3 ? loose : strict).push(r);
  });
  const out = strict.length ? strict : loose;
  out.sort((a, b) => (SC.get(b).s - SC.get(a).s) ||
    val(a, 'name').localeCompare(val(b, 'name'), 'en', { sensitivity: 'base' }));
  return { rows: out, partial: !strict.length && loose.length > 0,
           related: out.filter(r => SC.get(r).viaSyn).length };
}
const n = q => search(q).rows.length;
const top = q => { const r = search(q).rows[0]; return r ? val(r, 'name') : ''; };
const oldNorm = s => String(s || '').toLowerCase()
  .replace(/[^a-z0-9]+/g, ' ').replace(/\s+/g, ' ').trim();

let pass = 0, fail = 0;
function ok(label, cond, detail) {
  if (cond) { pass++; console.log('  PASS  ' + label + (detail !== undefined ? '   [' + detail + ']' : '')); }
  else { fail++; console.log('  FAIL  ' + label + (detail !== undefined ? '   got: ' + detail : '')); }
}
const H = t => console.log('\n== ' + t + ' ==');

H('the defects that started this');
ok('multi-word no longer returns zero: "orphan education"', n('orphan education') >= 25, n('orphan education'));
ok('"Saudi orphans" finds rows', n('Saudi orphans') >= 3, n('Saudi orphans'));
ok('"entrepreneurship women" finds rows', n('entrepreneurship women') >= 6, n('entrepreneurship women'));
ok('"refugees education" finds rows', n('refugees education') >= 4, n('refugees education'));

H('matching inside words is gone');
ok('"men" no longer returns hundreds via development and management', n('men') < 60, n('men'));
ok('"ship" no longer returns hundreds via partnerships', n('ship') <= 10, n('ship'));
ok('"art" no longer matches partner', n('art') < 200, n('art'));

H('an Arabic query no longer returns the whole register');
ok('Arabic returns nothing rather than all 1,862', n('\u0627\u0644\u062e\u064a\u0631') === 0, n('\u0627\u0644\u062e\u064a\u0631'));
ok('Arabic survives normalisation instead of becoming empty', E.norm('\u0627\u0644\u062e\u064a\u0631').length > 0);
ok('all 1,862 row strings are unchanged by the new normaliser',
  ROWS.every(r => NORM.get(r).all === oldNorm(SEARCH_FIELDS.map(k => val(r, k)).join(' '))));

H('stemming is two-way and does not maul words');
ok('"woman" now reaches the women rows', n('woman') > 90, n('woman'));
ok('"business" is not stemmed', E.stems('business').length === 0);
ok('"press" is not stemmed', E.stems('press').length === 0);
ok('"diabetes" is not stemmed and returns only diabetes rows',
  E.stems('diabetes').length === 0 && n('diabetes') === 8, n('diabetes'));
ok('"analysis" is not stemmed', E.stems('analysis').length === 0);
ok('"orphans" and "orphan" agree', n('orphans') === n('orphan'), n('orphans') + ' vs ' + n('orphan'));
ok('"houses" reaches "house", not the dead root "hous"',
  E.stems('houses').indexOf('house') > -1 && Math.abs(n('houses') - n('house')) <= 2,
  n('houses') + ' vs ' + n('house'));
ok('"diseases" reaches "disease"', Math.abs(n('diseases') - n('disease')) <= 1,
  n('diseases') + ' vs ' + n('disease'));
ok('"news" is not stemmed to "new"', E.stems('news').length === 0, JSON.stringify(E.stems('news')));

H('a narrow word never inherits a broad group');
ok('"autism" stays specific', n('autism') <= 20, n('autism'));
ok('"girl" does not return every women organisation', n('girl') <= 12, n('girl'));
ok('"infant" does not return every children organisation', n('infant') <= 6, n('infant'));
ok('"solar" does not return every energy row', n('solar') <= 12, n('solar'));
ok('"asylum" stays literal while "refugee" still reaches it',
  n('asylum') <= 3 && n('refugee') > 20, n('asylum') + ' / ' + n('refugee'));
ok('the broad word still reaches the narrow one',
  n('disability') > n('autism') && n('women') > n('girl') &&
  n('child') > n('infant') && n('energy') > n('solar'));
ok('"zakat" does not pull in every Islamic body', n('zakat') <= 30, n('zakat'));
ok('"livelihoods" answers with real livelihood work, not low-income descriptions',
  search('livelihoods').rows.slice(0, 6).every(r =>
    /livelihood|vocation|employ|job|train|skill|farmer|agricultur/i.test(val(r, 'focus'))),
  search('livelihoods').rows.slice(0, 3).map(r => val(r, 'name')).join(' | '));

H('the same question in the plural gets the same answer');
ok('livelihood and livelihoods agree', n('livelihood') === n('livelihoods'),
  n('livelihood') + ' vs ' + n('livelihoods'));
ok('mosque and mosques agree', n('mosque') === n('mosques'));
ok('school and schools agree', n('school') === n('schools'));

H('the corpus vocabulary gap is bridged');
ok('"waqf" also reaches the endowments', n('waqf') > 150, n('waqf'));
ok('"IDP" reaches displacement work', n('IDP') > 5, n('IDP'));
ok('"press" reaches the media bodies', n('press') > 5, n('press'));

H('relevance, not the alphabet');
ok('"cancer research" leads with a cancer body', /Cancer/i.test(top('cancer research')), top('cancer research'));
ok('"sports for disabled" leads with Special Olympics', /Special Olympics/i.test(top('sports for disabled')), top('sports for disabled'));
ok('"clean water" leads with a water provider', /Bondh|Water/i.test(top('clean water')), top('clean water'));
/* A substring test here was too weak: it passed on any name containing the phrase. There is
   no row named exactly "Qatar Foundation" in this register, so what a name lookup owes the
   reader is that entries carrying BOTH words in their own NAME come first. */
ok('a name lookup puts the names carrying both words first',
  search('Qatar Foundation').rows.slice(0, 3).every(r =>
    /qatar/i.test(val(r, 'name')) && /foundation/i.test(val(r, 'name'))),
  search('Qatar Foundation').rows.slice(0, 2).map(r => val(r, 'name')).join(' | '));

H('the filler words of this domain do not gate the answer');
ok('"support for widows" returns the widow rows, not widow-and-support rows',
  n('support for widows') >= 5, n('support for widows'));
ok('"mental health services" leads with a mental health body',
  /Mental Health/i.test(top('mental health services')), top('mental health services'));
/* only 6 rows in the whole register mention girls, so 6 is the ceiling here, not a
   shortfall. The earlier threshold of 10 was written while "girls" wrongly inherited
   every women's organisation. */
ok('"who funds girls schooling" finds the girls education work that exists',
  n('who funds girls schooling') >= 4 &&
  search('who funds girls schooling').rows.slice(0, 4).every(r =>
    /girl|school|educat|scholar|read/i.test(val(r, 'name') + ' ' + val(r, 'focus'))),
  n('who funds girls schooling') + ': ' +
  search('who funds girls schooling').rows.slice(0, 3).map(r => val(r, 'name')).join(' | '));
ok('filler words do not constrain the query', n('sports for disabled') > 0, n('sports for disabled'));

H('the related-wording label means what it says');
ok('a row that matched the real word outright is not called related wording',
  search('cancer services').related === 0,
  search('cancer services').related + ' of ' + n('cancer services'));
ok('a row reached through an alternative IS called related wording',
  search('woman').related > 90, search('woman').related);

H('part of the words is a last resort, and is labelled');
ok('"clean water" keeps its real answers instead of falling back',
  search('clean water').partial === false && n('clean water') <= 6, n('clean water'));
ok('"food security Yemen" is marked as partial', search('food security Yemen').partial === true);
ok('a rare word counts for more than a common one inside a partial answer',
  /Yemen/i.test(search('food security Yemen').rows.slice(0, 6)
    .map(r => val(r, 'name') + ' ' + val(r, 'focus')).join(' ')));

H('intent is not silently reversed');
ok('"no cancer" is not answered as a confident list of cancer bodies',
  search('no cancer').partial === true);
ok('"cancer or diabetes" behaves as the or it reads like',
  search('cancer or diabetes').partial === true);

H('junk queries and pasted text');
const scriptQ = '<scr' + 'ipt>alert(1)</scr' + 'ipt>';
ok('a pasted script tag returns almost nothing', n(scriptQ) <= 3, n(scriptQ));
ok('punctuation only is treated as no query', n('!!! ???') === 1862, n('!!! ???'));
ok('a single character is dropped rather than filtering', n('a') === 1862, n('a'));
{
  const big = new Array(120).fill('education').join(' ');
  const t0 = Date.now(); search(big); const ms = Date.now() - t0;
  ok('120 repeated words stay under 300ms', ms < 300, ms + 'ms');
  ok('the query is capped at 24 words', E.plan(big).toks.length <= 24, E.plan(big).toks.length);
}

H('precision against the data itself');
{
  const expect = ROWS.filter(r => val(r, 'country') === 'Kuwait' &&
    /orphan/i.test([val(r, 'name'), val(r, 'focus')].join(' ')));
  const found = search('orphan').rows.filter(r => val(r, 'country') === 'Kuwait');
  ok('Kuwait plus "orphan" returns exactly the Kuwaiti orphan rows',
    found.length === expect.length, found.length + ' vs ' + expect.length);
}
{
  const expect = ROWS.filter(r => /\bcancer\b/i.test(
    [val(r,'name'), val(r,'focus'), val(r,'type')].join(' ')));
  const missed = expect.filter(r => search('cancer').rows.indexOf(r) === -1);
  ok('"cancer" finds every row whose text says cancer', missed.length === 0, missed.length + ' missed');
}
{
  const expect = ROWS.filter(r => /\bwidow/i.test(val(r, 'focus')));
  const missed = expect.filter(r => search('widows').rows.indexOf(r) === -1);
  ok('"widows" finds every row whose mandate says widow', missed.length === 0, missed.length + ' missed');
}

console.log('');
console.log(fail ? 'FAILED ' + fail + ' of ' + (pass + fail) : 'ALL ' + pass + ' ASSERTIONS PASS');
process.exit(fail ? 1 : 0);
