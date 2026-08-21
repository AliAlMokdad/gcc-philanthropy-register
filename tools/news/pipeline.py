# Normalise, gate, classify, match, deduplicate, cluster, rank.
#
# Deterministic throughout. No model is called anywhere in this file. That is the point:
# every classification a reader sees was produced by a rule that can be read, argued with
# and corrected, and the optional model enrichment described in the design sits AFTER this
# stage and can only ever propose, never decide.

import hashlib, re, unicodedata, urllib.parse
import datetime as dt

from registry import (GCC, REGIONAL_TERMS, DESTINATIONS, TOPICS, EVENT_TYPES,
                      PHILANTHROPY_TERMS, NEGATIVE_PHRASES, ECONOMY_ADMIT, ECONOMY_VETO,
                      MEDICAL_VETO, REGISTRY_VERSION, source_by_id,
                      publisher_type, PERIODIC_FORMATS, PERIODIC_TITLE_TERMS,
                      ADVOCACY_TITLE_TERMS, COMMEMORATIVE_TERMS)

UTC = dt.timezone.utc


def now_iso():
    return dt.datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s):
    if not s:
        return None
    try:
        return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except Exception:
        return None


# ------------------------------------------------------------------ text normalisation
_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_WS = re.compile(r"\s+")


def fold(s):
    """Lowercase, strip accents, punctuation to space. Used for every text comparison so
    that "Al-Maktoum" and "Al Maktoum" are the same string."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = _PUNCT.sub(" ", s.lower())
    return _WS.sub(" ", s).strip()


def tokens(s):
    return [t for t in fold(s).split() if t]


def detect_language(text, declared="en"):
    """A feed's declared language describes the feed, not the item. A UNHCR headline in
    Arabic arrived through an English feed and inherited "en", which would have set the
    wrong text direction on it. Script decides; the declaration is only a fallback."""
    if not text:
        return declared or "en"
    arabic = sum(1 for c in text if "\u0600" <= c <= "\u06FF" or "\u0750" <= c <= "\u077F")
    letters = sum(1 for c in text if c.isalpha())
    if letters and arabic / float(letters) > 0.35:
        return "ar"
    return declared or "en"


def has_phrase(hay_folded, phrase):
    """Whole-token phrase containment. Substring matching is what makes 'aid' match
    'said' and 'oman' match 'romania', so every check goes through token boundaries."""
    p = fold(phrase)
    if not p:
        return False
    return (" " + p + " ") in (" " + hay_folded + " ")


def any_phrase(hay_folded, phrases):
    return [p for p in phrases if has_phrase(hay_folded, p)]


# ------------------------------------------------------------------ URL normalisation
# EXACT NAMES, not prefixes. The prefix form stripped any parameter beginning "source" or
# "ref", so "?source=grant&id=42" and "?source=policy&id=42" canonicalised identically and
# two distinct articles were then deduplicated into one.
TRACKING_EXACT = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "utm_id",
    "utm_name", "utm_reader", "utm_brand", "utm_social", "utm_social_type",
    "gclid", "dclid", "gbraid", "wbraid", "gclsrc", "yclid", "msclkid", "fbclid",
    "igshid", "igsh", "mc_cid", "mc_eid", "s_kwcid", "ef_id", "spm", "scm",
    "vero_id", "vero_conv", "oly_anon_id", "oly_enc_id", "_hsenc", "_hsmi", "hsa_cam",
    "mkt_tok", "trk", "trkcampaign", "sc_channel", "sc_campaign", "cmpid", "ncid",
    "at_medium", "at_campaign", "ito", "cmp", "smid", "shared_from", "ref_src", "ref_url",
}
TRACKING_PREFIX = re.compile(r"^(utm_|ga_|_ga|piwik_|matomo_|pk_)", re.I)
AMP_TAIL = re.compile(r"(/amp|\.amp|/amp\.html|\?outputType=amp)$", re.I)


def normalise_url(u):
    """Returns (original, canonical) or (None, None) if the URL is not usable.

    Only http and https are permitted. Everything else, including javascript:, data: and
    a bare protocol-relative //host, is rejected here so that no unusable href can reach
    the page even if the renderer's own check were ever removed."""
    if not u or not isinstance(u, str):
        return None, None
    u = u.strip()
    if not u or len(u) > 2000:
        return None, None
    try:
        p = urllib.parse.urlsplit(u)
    except Exception:
        return None, None
    if p.scheme.lower() not in ("http", "https"):
        return None, None
    if not p.netloc:
        return None, None
    # A USERINFO HOST IS A DISGUISE. "https://trusted.example@evil.example/story" was
    # admitted and its publisher domain rendered as "trusted.example@evil.example", while
    # the link navigates to evil.example.
    if "@" in p.netloc:
        return None, None
    try:
        if p.port is not None and not (0 < p.port < 65536):
            return None, None
    except ValueError:
        return None, None      # a non-numeric port: Python tolerates it, browsers do not
    host = p.netloc.lower()
    if host.startswith("www."):
        host_c = host[4:]
    else:
        host_c = host
    # mobile hosts point at the same article
    for pre in ("m.", "amp."):
        if host_c.startswith(pre):
            host_c = host_c[len(pre):]
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=False)
         if k.lower() not in TRACKING_EXACT and not TRACKING_PREFIX.match(k)]
    path = p.path or "/"
    path_c = AMP_TAIL.sub("", path) or "/"
    if len(path_c) > 1 and path_c.endswith("/"):
        path_c = path_c[:-1]
    canonical = urllib.parse.urlunsplit((
        "https", host_c, path_c,
        urllib.parse.urlencode(sorted(q)) if q else "", ""))
    original = urllib.parse.urlunsplit((p.scheme.lower(), host, path, p.query, ""))
    return original, canonical


def domain_of(u):
    try:
        h = urllib.parse.urlsplit(u).netloc.lower()
        return h[4:] if h.startswith("www.") else h
    except Exception:
        return ""


# ------------------------------------------------------------------ the relevance gate
def gcc_signals(text_folded, feed_country=None, title_folded=None, feed_is_gulf=False):
    """Returns (primary, related[], regional_bool, evidence[]).

    Section 33: the event's geography is not the publisher's location. So a feed's own
    country is a WEAK hint used only to break a tie, never to assign a country on its own.
    """
    hits, kinds = {}, {}
    evidence = []
    for state, d in GCC.items():
        score = 0
        matched = set()          # per distinct STRING, so one word cannot score twice
        kind = set()
        for weight, key, label in ((9, "orgs", "organisation"), (6, "names", "name"),
                                   (4, "demonyms", "demonym"), (3, "cities", "city")):
            for term in d.get(key, []):
                ft = fold(term)
                if ft in matched or not has_phrase(text_folded, term):
                    continue
                matched.add(ft)
                score += weight
                kind.add(label)
                evidence.append("%s: %s %r" % (state, label, term))
        if score:
            hits[state] = score
            kinds[state] = kind

    regional = bool(any_phrase(text_folded, REGIONAL_TERMS))
    if not hits and not regional:
        return None, [], False, evidence

    if hits:
        ranked = sorted(hits.items(), key=lambda kv: (-kv[1], kv[0]))
        # A regional story that also names three or more states belongs to the region,
        # not to whichever one is mentioned first (section 34).
        if regional and len(ranked) >= 3:
            return "GCC / Regional", [s for s, _ in ranked], True, evidence
        # THE EVIDENCE FLOOR, second version. The first accepted a bare state NAME anywhere
        # in the text, and that let "Iran: Humanitarian crisis for children deepens after one
        # month of war" be filed under Bahrain on a single passing mention, the same class of
        # error as a UK aid announcement filed under Qatar.
        #
        # A state now qualifies on a NAMED GULF ORGANISATION anywhere, or on a state word in
        # the TITLE, or because the feed is that state's own outlet writing about itself.
        # Checked row by row against the real feed: the Iran report fails all three; the Ehsan
        # Royal Order has no Gulf word in its headline but arrives from the Saudi Gazette feed
        # and stays; the Qatar Charity analysis of Sudan names an organisation and stays.
        tf_title = title_folded or ""
        # A GULF STATE AFTER "to", "in" or "for" IS WHERE THE MONEY WENT, not who sent it.
        # "British Red Cross sends humanitarian aid to Bahrain" shipped as a Bahrain story.
        DEST_PREP = r"(?:to|in|into|for|across|within|reaching|reaches|towards?|bound for)"
        def only_as_destination(state):
            d = GCC.get(state, {})
            terms = list(d.get("names", [])) + list(d.get("cities", []))
            found_any, found_subject = False, False
            for term in terms:
                if not has_phrase(tf_title, term):
                    continue
                found_any = True
                # is there an occurrence NOT preceded by a destination preposition?
                for m in re.finditer(r"(?:^|\s)" + re.escape(fold(term)) + r"(?=\s|$)",
                                     tf_title):
                    before = tf_title[:m.start()].strip()
                    if not re.search(DEST_PREP + r"$", before):
                        found_subject = True
                        break
                if found_subject:
                    break
            return found_any and not found_subject

        def solid(s):
            k = kinds.get(s, set())
            if "organisation" in k:
                return True
            if feed_is_gulf and feed_country == s:
                return True
            d = GCC.get(s, {})
            for key in ("names", "demonyms", "cities"):
                for term in d.get(key, []):
                    if has_phrase(tf_title, term):
                        # the state is in the headline, but check it is the actor
                        return not only_as_destination(s)
            return False
        solid_states = [s for s, _ in ranked if solid(s)]
        if not solid_states:
            return None, [], regional, evidence + ["rejected: only a passing mention"]
        ranked = [(s, v) for s, v in ranked if s in solid_states]
        top, top_score = ranked[0]
        if len(ranked) > 1 and ranked[1][1] == top_score:
            # a genuine tie between states, with no regional framing, is regional
            if regional or len(ranked) >= 3:
                return "GCC / Regional", [s for s, _ in ranked], regional, evidence
            if feed_country in (top, ranked[1][0]):
                top = feed_country
                evidence.append("tie broken by the feed's own country: %s" % feed_country)
        return top, [s for s, _ in ranked if s != top], regional, evidence
    return "GCC / Regional", [], True, evidence


def destinations_in(text_folded, primary):
    out = []
    for c in DESTINATIONS:
        if has_phrase(text_folded, c):
            if c in ("Turkey", "Turkiye") and "Turkiye" in out:
                continue
            out.append(c)
    # a GCC state is never its own destination
    return [c for c in out if c != primary][:8]


def philanthropy_signals(text_folded):
    return any_phrase(text_folded, PHILANTHROPY_TERMS)


def relevance(text_folded, primary, regional, phil_hits):
    """Both gates must pass. Returns (admitted, reason)."""
    if not primary:
        return False, "no GCC signal"
    if not phil_hits:
        return False, "no philanthropy signal"

    med = any_phrase(text_folded, MEDICAL_VETO)
    if med:
        return False, "transplant or clinical reporting, not sector news (%r)" % med[0]

    neg = any_phrase(text_folded, NEGATIVE_PHRASES)
    if neg:
        # A negative phrase does not veto a story that has independent philanthropy
        # vocabulary. "The foundation stone was laid by the Qatar Charity chairman" is a real
        # story; "piling and foundation works tender" is not. So the veto only bites when
        # every philanthropy hit is accounted for by the cancelled words.
        cancelled = set()
        for n in neg:
            for h in phil_hits:
                if fold(h) in fold(n):
                    cancelled.add(h)
        if len(cancelled) >= len(set(phil_hits)):
            return False, "philanthropy signal cancelled by %r" % neg[0]

    econ_veto = any_phrase(text_folded, ECONOMY_VETO)
    if econ_veto and not any_phrase(text_folded, ECONOMY_ADMIT):
        # Applied BEFORE the strong-signal test, not after. A sovereign debt story that
        # happens to use the word "programme" or "allocates" was passing on strength alone.
        return False, "capital markets or sovereign finance (%r)" % econ_veto[0]

    strong = [h for h in phil_hits
              if h in ("philanthropy", "philanthropic", "waqf", "zakat", "awqaf",
                       "endowment", "grantmaking", "humanitarian", "sadaqah",
                       "charitable", "nonprofit", "civil society", "impact investment",
                       "corporate social responsibility", "development assistance")]
    if not strong:
        # only weak, ambiguous vocabulary. Admit it only if an economy-adjacent term makes
        # it genuinely about the philanthropy ecosystem, and never if an economy veto fires.
        if any_phrase(text_folded, ECONOMY_VETO):
            return False, "reads as a market or corporate-results story"
        if not any_phrase(text_folded, ECONOMY_ADMIT) and len(set(phil_hits)) < 2:
            return False, "single weak signal %r only" % phil_hits[0]
    return True, "ok"


# ------------------------------------------------------------------ classification
def topic_of(text_folded):
    for name, terms in TOPICS:
        if terms and any_phrase(text_folded, terms):
            return name
    return "General"


def related_topics(text_folded, primary):
    out = []
    for name, terms in TOPICS:
        if name == primary or not terms:
            continue
        if any_phrase(text_folded, terms):
            out.append(name)
    return out[:3]


def event_of(text_folded):
    for name, terms in EVENT_TYPES:
        if terms and any_phrase(text_folded, terms):
            return name
    return "general_news"


# ------------------------------------------------------------------ amounts
CUR_WORDS = {
    "riyal": None, "riyals": None,          # ambiguous: SAR or QAR, resolved by country
    "dirham": "AED", "dirhams": "AED",
    "dinar": None, "dinars": None,          # KWD or BHD
    "rial": "OMR", "rials": "OMR",
    "dollar": "USD", "dollars": "USD",
    "euro": "EUR", "euros": "EUR", "pound": "GBP", "pounds": "GBP",
}
CUR_CODES = ["SAR", "AED", "QAR", "KWD", "BHD", "OMR", "USD", "EUR", "GBP"]
SCALE = {"thousand": 1e3, "million": 1e6, "m": 1e6, "billion": 1e9, "bn": 1e9,
         "trillion": 1e12, "k": 1e3}
AMOUNT_RE = re.compile(
    r"(?P<code>SAR|AED|QAR|KWD|BHD|OMR|USD|EUR|GBP|US\$|\$|€|£)?\s*"
    r"(?P<num>\d[\d,\.]*)\s*"
    r"(?P<scale>thousand|million|billion|trillion|bn|m\b|k\b)?\s*"
    r"(?P<word>riyals?|dirhams?|dinars?|rials?|dollars?|euros?|pounds?)?",
    re.I)
COUNTRY_CURRENCY = {"Saudi Arabia": "SAR", "United Arab Emirates": "AED", "Qatar": "QAR",
                    "Kuwait": "KWD", "Bahrain": "BHD", "Oman": "OMR"}


def extract_amount(text, primary_country):
    """Only an explicit currency plus an explicit number becomes an amount. A bare number
    is never money. If the currency is ambiguous (riyal, dinar) it is resolved from the
    story's own state, and if that cannot be done the amount is dropped rather than
    guessed, because a wrong currency is a wrong figure."""
    if not text:
        return None
    for m in AMOUNT_RE.finditer(text):
        code, num, scale, word = (m.group("code"), m.group("num"),
                                  m.group("scale"), m.group("word"))
        if not num or not (code or word):
            continue
        raw = num.replace(",", "")
        if raw.count(".") > 1:
            continue
        try:
            value = float(raw)
        except ValueError:
            continue
        if scale:
            value *= SCALE.get(scale.lower().strip(), 1)
        elif value < 1000:
            # "$5" is almost always a fragment, not a philanthropic commitment
            continue
        cur = None
        if code:
            c = code.upper().replace("US$", "USD")
            cur = {"$": "USD", "€": "EUR", "£": "GBP"}.get(code, c)
            if cur not in CUR_CODES:
                cur = None
        if not cur and word:
            w = word.lower().rstrip("s")
            cur = CUR_WORDS.get(w) or CUR_WORDS.get(w + "s")
            if cur is None:
                cur = COUNTRY_CURRENCY.get(primary_country)
                if cur is None:
                    continue            # ambiguous and unresolvable: drop it
        if not cur:
            continue
        return {"value": value, "currency": cur,
                "text": m.group(0).strip(),
                # no conversion is published: section 59 requires a defined methodology and
                # a known conversion date before a USD equivalent may be shown, and this
                # pipeline has neither, so the announced amount stands alone.
                "usd_equivalent": None, "conversion_date": None}
    return None


# ------------------------------------------------------------------ register matching
GENERIC_NAMES = {
    "charity", "foundation", "society", "association", "trust", "fund", "council",
    "committee", "centre", "center", "institute", "organisation", "organization",
    "ministry", "authority", "group", "company", "bank", "office", "endowment",
    "red crescent", "charitable society", "charity organisation", "welfare society",
    "the big heart", "human appeal", "world vision",
}


def _entity_id(name, country):
    """The register's own identity rule, imported rather than restated.

    register_id used to be "r%d" % n, the row's POSITION in data.json. The exporter reads the
    workbook in sheet order and the workbook is edited by hand, so sorting it or inserting a row
    moved every id. That id is also the key for drop_orgs in news-decisions.json, so an editorial
    suppression of a false match would have begun suppressing a real one. Nothing had been
    suppressed yet, which is the only reason this was still free to change."""
    import os as _os
    import sys as _sys
    _root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    if _root not in _sys.path:
        _sys.path.insert(0, _root)
    from identity import entity_id
    return entity_id(name, country)


def build_register_index(register):
    """From data.json to a matching index. Only names that can carry a match are indexed:
    a name must fold to at least two tokens and eleven characters and must not be a
    generic sector noun, because a false organisation link is the one error that would
    cost this product its credibility."""
    keys = register["keys"]
    ki = {k: i for i, k in enumerate(keys)}
    idx = {}
    skipped = 0
    for row in register["rows"]:
        name = (row[ki["name"]] or "").strip()
        if not name:
            continue
        f = fold(name)
        if len(f) < 11 or len(f.split()) < 2 or f in GENERIC_NAMES:
            skipped += 1
            continue
        country = (row[ki["country"]] or "").strip()
        rec = {"register_id": _entity_id(name, country), "name": name,
               "country": country,
               "type": (row[ki["type"]] or "").strip()}
        # last one wins on a duplicate folded name; they are the same institution
        idx[f] = rec
    return idx, skipped


def match_organisations(text, index, primary_country):
    """Longest-first whole-phrase matching against the register, plus the curated alias
    table. Only exact, alias and normalised matches are published; anything weaker is kept
    with its method and confidence and is never rendered."""
    tf = fold(text)
    found, seen = [], set()

    # curated aliases first: these are hand-verified in registry.py
    for state, d in GCC.items():
        for alias in d["orgs"]:
            if not has_phrase(tf, alias):
                continue
            fa = fold(alias)
            hit = index.get(fa)
            if not hit:
                # A SUBSTRING IS NOT AN IDENTITY. This previously accepted any single register
                # name containing the alias within 22 characters, which is how the alias
                # "prince sultan" adopted PRINCE SULTAN UNIVERSITY and "zayed foundation"
                # adopted AHMAD BIN ZAYED FOUNDATION, both at confidence 0.95 and both
                # published as register links.
                #
                # A register row is now accepted only where the difference is an abbreviation
                # or a parenthetical, so "Qatar Fund for Development (QFFD)" still resolves
                # from "qatar fund for development" while a different institution cannot.
                hit = None
                for k, v in index.items():
                    if not k.startswith(fa):
                        continue
                    tail = k[len(fa):].strip()
                    if tail and not re.fullmatch(r"[a-z0-9 ]{0,12}", tail):
                        continue
                    if tail and len(tail.split()) > 2:
                        continue
                    if hit is not None:
                        hit = None          # ambiguous between two rows, so neither
                        break
                    hit = v
            key = (hit["register_id"] if hit else "alias:" + fa)
            if key in seen:
                continue
            seen.add(key)
            found.append({
                "name": hit["name"] if hit else alias.title(),
                "register_id": hit["register_id"] if hit else None,
                "match_method": "verified_alias", "confidence": 0.95 if hit else 0.9,
                "country": hit["country"] if hit else state,
            })

    # then register names, longest first so "Qatar Charity Bosnia" cannot beat the longer
    # correct name when both are present
    for f in sorted(index.keys(), key=len, reverse=True):
        if not has_phrase(tf, f):
            continue
        rec = index[f]
        if rec["register_id"] in seen:
            continue
        # a name already covered by a longer accepted match is the same institution
        if any(f in fold(x["name"]) for x in found if x.get("name")):
            continue
        seen.add(rec["register_id"])
        found.append({"name": rec["name"], "register_id": rec["register_id"],
                      "match_method": "exact_name", "confidence": 1.0,
                      "country": rec["country"]})
        if len(found) >= 4:
            break

    for o in found:
        o["publishable"] = bool(o["register_id"]) and o["confidence"] >= 0.9
    return found[:4]


# ------------------------------------------------------------------ identity and dedup
def stable_id(canonical_url, title):
    """The canonical URL ALONE. Hashing the title as well meant that correcting a headline
    produced a NEW id, so every editorial decision recorded against that item, a rejection, a
    correction, a pinned Top Development, silently stopped applying and the article came back
    as unreviewed. The URL is the article's identity; the title is its content."""
    h = hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()
    return h[:16]


def strip_repeated_title(desc, title):
    """Remove the headline where a feed has repeated it at the head of its own description.

    THE BUG THIS REPLACES compared FOLDED text, which has had its punctuation removed, and
    then cut the RAW string by len(title). Those two lengths are not the same, so the cut
    landed in the wrong place and left the difference behind: a real item rendered as
    "s. Funded by KSrelief, UNOPS started equipping three hospitals in Hama", where the stray
    "s." is the tail of "Syria:" from the headline.

    This walks word by word and then converts the match back to a RAW offset, so the cut is
    made at a position that exists in the string being cut.
    """
    if not desc or not title:
        return desc
    dt, tt = tokens(desc), tokens(title)
    if len(tt) < 4:
        return desc
    # SEARCH THE ALIGNMENT rather than assuming word zero. A provider whose tag block ended
    # with the country resumed its description one word into the headline, so aligning only
    # at zero found a run of 0 out of 18 while starting one word in found 17.
    best_start, best_run = 0, 0
    for start in range(0, 5):
        run = 0
        while start + run < len(tt) and run < len(dt) and dt[run] == tt[start + run]:
            run += 1
        if run > best_run:
            best_start, best_run = start, run
    if best_run < max(4, int((len(tt) - best_start) * 0.6)):
        return desc                      # not a repetition, so leave it alone
    pos, seen = 0, 0
    for m in re.finditer(r"[^\W_]+", desc, re.UNICODE):
        seen += 1
        pos = m.end()
        if seen >= best_run:
            break
    return desc[pos:].lstrip(" -\u2013\u2014:.,;\u00b7)]")


def title_key(title):
    t = [w for w in tokens(title) if len(w) > 2]
    return " ".join(sorted(set(t)))


def title_key_letters(title):
    """Letters only, digits and punctuation discarded. "USD 2,500,000" and "USD2,500,000"
    from the same publisher on the same day survived as two separate rows because
    tokenising the digits pushed the two keys below the similarity threshold. Stripping
    every digit makes the twin identical, and no spacing or punctuation can defeat it."""
    t = [re.sub(r"\d+", "", w) for w in tokens(title)]
    return " ".join(sorted({w for w in t if len(w) > 2}))


def jaccard(a, b):
    A, B = set(a.split()), set(b.split())
    if not A or not B:
        return 0.0
    return len(A & B) / float(len(A | B))


def different_event(a, b):
    """True when two records cannot be the same announcement, whatever their wording.

    Title similarity is a good signal and a poor decision. Two grants from one funder on one
    day to two countries read almost identically, and merging them destroys a real
    announcement, which section 51 forbids outright."""
    da = tuple(sorted(a.get("destination_countries") or []))
    db = tuple(sorted(b.get("destination_countries") or []))
    if da and db and da != db:
        return True
    aa = (a.get("amount") or {}).get("value")
    bb = (b.get("amount") or {}).get("value")
    if aa and bb and aa != bb:
        return True
    return False


def deduplicate(items):
    """Five layers, in order of certainty. Returns (kept, dropped_count, notes)."""
    kept, notes = [], []
    by_canon, by_guid = {}, {}
    dropped = 0

    for it in sorted(items, key=lambda x: (x["published_at"] or "", x["id"]), reverse=True):
        # 1. exact canonical URL
        c = it["canonical_url"]
        if c in by_canon:
            by_canon[c]["_dupes"] += 1
            dropped += 1
            continue
        # 2. provider record identity
        # A GUID IS FEED-LOCAL, not global. Two feeds both using "123" dropped an unrelated
        # article, so the key carries the source it came from.
        g = it["provenance"].get("provider_record_id")
        if g:
            g = str(it.get("discovered_via") or "") + "|" + str(g)
        if g and g in by_guid:
            by_guid[g]["_dupes"] += 1
            dropped += 1
            continue
        # 3 and 4. title similarity against what is already kept, inside a window
        tk = it["_title_key"]
        t0 = parse_iso(it["published_at"])
        hit = None
        for other in kept:
            t1 = parse_iso(other["published_at"])
            if t0 and t1 and abs((t0 - t1).total_seconds()) > 5 * 86400:
                continue
            same_pub = other["publisher_domain"] == it["publisher_domain"]
            j = jaccard(tk, other["_title_key"])
            # TITLE SIMILARITY ALONE MUST NOT MERGE TWO ANNOUNCEMENTS. Measured: "Qatar
            # Charity launches new water project for rural families in Sudan" against the
            # same sentence ending "in Somalia", same publisher, scores 0.818 against a 0.72
            # threshold, and one of the two was deleted. A differing destination or a
            # differing amount is a different event whatever the wording.
            if same_pub and j >= 0.72 and not different_event(it, other):
                hit = other
                break
            # the number-format twin: same publisher, identical once digits are removed
            if same_pub and it["_title_letters"] and \
                    it["_title_letters"] == other["_title_letters"]:
                hit = other
                break
            if j >= 0.84 and not different_event(it, other):
                hit = other
                break
        if hit:
            hit["_dupes"] += 1
            # a second independent publisher on the same story is a real corroboration
            if hit["publisher_domain"] != it["publisher_domain"]:
                hit["_also"].add(it["publisher"])
            dropped += 1
            continue
        it["_dupes"] = 0
        it["_also"] = set()
        kept.append(it)
        by_canon[c] = it
        if g:
            by_guid[g] = it

    # 5. event clustering. Deliberately conservative: two announcements that merely name
    # the same organisation are NOT the same event, so a cluster needs the organisation set,
    # the country, the event type AND a seven-day window to agree.
    clusters = {}
    for it in kept:
        orgs = tuple(sorted(o["name"] for o in it["organisations"]))
        amt = it["amount"]["value"] if it.get("amount") else None
        # the DESTINATION is part of the identity of an event. Without it, two grants of the
        # same size from the same funder to different countries were the same event.
        dest = tuple(sorted(it.get("destination_countries") or []))
        sig = (orgs, it["primary_gcc_country"], it["event_type"], amt, dest)
        if not orgs:
            continue                    # no named actor means no reliable cluster
        t0 = parse_iso(it["published_at"])
        placed = False
        for cid, members in clusters.items():
            m0 = members[0]
            if m0["_sig"] != sig:
                continue
            t1 = parse_iso(m0["published_at"])
            if t0 and t1 and abs((t0 - t1).total_seconds()) > 7 * 86400:
                continue
            members.append(it)
            it["cluster_id"] = cid
            placed = True
            break
        if not placed:
            cid = "c" + it["id"][:10]
            it["_sig"] = sig
            it["cluster_id"] = cid
            clusters[cid] = [it]

    for cid, members in clusters.items():
        for m in members:
            m["cluster_size"] = len(members) + m["_dupes"]
    for it in kept:
        it.setdefault("cluster_size", 1 + it["_dupes"])
        it["also_reported_by"] = sorted(it["_also"])[:4]
    notes.append("%d dropped as duplicates, %d clusters formed" % (dropped, len(clusters)))
    return kept, dropped, notes


# ------------------------------------------------------------------ ranking
SOURCE_QUALITY = {"un_multilateral": 20, "official_government": 18,
                  "official_organisation": 16, "independent_media": 15,
                  "trade_publication": 12, "academic_research": 14, "other": 6}
EVENT_WEIGHT = {"funding_announcement": 20, "grant": 18, "donation": 15, "fund_launch": 18,
                "new_foundation": 18, "development_agreement": 17, "policy_change": 16,
                "regulation": 16, "partnership": 13, "new_programme": 13,
                "new_organisation": 13, "impact_investment": 15, "leadership_change": 11,
                "humanitarian_response": 14, "waqf_endowment": 14, "zakat_initiative": 13,
                "research_publication": 9, "corporate_giving": 10, "conference": 6,
                "general_news": 4}


def score(it, now):
    """Transparent, deterministic, and never shown to a reader (section 31)."""
    parts = {}
    t = parse_iso(it["published_at"])
    age_h = ((now - t).total_seconds() / 3600.0) if t else 999
    # FRESHNESS WAS WORTH A QUARTER OF THE SCORE and it dominated significance: the two
    # highest-ranked items were both published that morning and neither was a development.
    # Reduced so that what happened outweighs when it was posted.
    #
    # AND CLAMPED AT ZERO AGE. A negative age had no floor, so a 2099 timestamp scored 67,985
    # on freshness alone and was guaranteed the lead position. Nothing is fresher than now.
    if age_h < 0:
        age_h = 0
    parts["freshness"] = max(0, 18 - (age_h / 168.0) * 18) if age_h < 168 else 0
    parts["source"] = SOURCE_QUALITY.get(it["source_type"], 6)
    parts["event"] = EVENT_WEIGHT.get(it["event_type"], 4)

    mag = 0
    a = it.get("amount")
    if a and a.get("value"):
        v = a["value"]
        mag = 5 if v >= 1e6 else 2
        if v >= 1e7:
            mag = 9
        if v >= 1e8:
            mag = 13
        if v >= 1e9:
            mag = 15
    parts["magnitude"] = mag

    rel = 0
    if it["primary_gcc_country"] != "GCC / Regional":
        rel += 5
    if any(o.get("publishable") for o in it["organisations"]):
        rel += 5                        # a named register organisation is the sharpest signal
    elif it["organisations"]:
        rel += 2
    parts["relevance"] = rel

    parts["corroboration"] = min(10, 4 * len(it.get("also_reported_by") or []))

    pen = 0
    if not it.get("description"):
        pen += 3
    if it["primary_topic"] == "General":
        pen += 5
    if it["event_type"] == "general_news":
        pen += 4
    if it["source_type"] == "other":
        pen += 4
    if age_h > 168:
        pen += 10
    if it.get("_periodic"):
        # heavy, because a monthly dispatch is otherwise indistinguishable from an
        # announcement on freshness and source quality alone, and it outranked real news
        pen += 22
    if it.get("_advocacy"):
        pen += 14        # an argument about what should happen is not a thing that happened
    if it.get("_commemorative"):
        pen += 12        # nor is a total of giving since 1975, published on an awareness day
    parts["penalty"] = -pen

    return sum(parts.values()), parts


def pick_top(items, now, limit=4, floor=42.0):
    """One story per cluster, at most two from one state unless the news genuinely forces
    it, and a weak slot is left empty rather than filled (section 31)."""
    scored = []
    for it in items:
        s, parts = score(it, now)
        it["_score"] = round(s, 2)
        it["_score_parts"] = parts
        scored.append(it)
    scored.sort(key=lambda x: (-x["_score"], x["published_at"] or "", x["id"]))

    chosen, seen_clusters, per_country = [], set(), {}
    for it in scored:
        if it["editorial"]["status"] != "published":
            continue
        if it["_score"] < floor:
            continue
        cid = it.get("cluster_id")
        if cid and cid in seen_clusters:
            continue
        c = it["primary_gcc_country"]
        if per_country.get(c, 0) >= 2:
            # allowed past two only if it clearly outranks the field
            if it["_score"] < 70:
                continue
        chosen.append(it)
        if cid:
            seen_clusters.add(cid)
        per_country[c] = per_country.get(c, 0) + 1
        if len(chosen) >= limit:
            break

    # a manual selection always wins, and never counts against the caps
    pinned = [it for it in scored if it["editorial"].get("is_top")
              and it["editorial"]["status"] == "published"]
    for p in reversed(pinned):
        if p in chosen:
            chosen.remove(p)
        chosen.insert(0, p)
    return chosen[:limit]


# ------------------------------------------------------------------ normalise one record
def normalise(raw, register_index, source_lookup):
    """One provider candidate to one feed item, or None with a reason."""
    from providers import rfc822, iso8601, gdelt_stamp

    title = (raw.get("title") or "").strip()
    if not title or len(title) < 12:
        return None, "title too short"
    original, canonical = normalise_url(raw.get("url"))
    if not canonical:
        return None, "unusable URL"

    stamp = raw.get("_stamp")
    if stamp == "gdelt":
        pub_at, prec = gdelt_stamp(raw.get("published_raw"))
    elif stamp == "iso":
        pub_at, prec = iso8601(raw.get("published_raw"))
    else:
        pub_at, prec = rfc822(raw.get("published_raw"))
        if not pub_at:
            pub_at, prec = iso8601(raw.get("published_raw"))
    if not pub_at:
        return None, "no parseable publication date"

    src = source_lookup(raw.get("discovered_via")) or {}
    publisher = (raw.get("publisher_hint") or "").strip() or domain_of(canonical)
    # a domain is a poor publisher name, so tidy it rather than print "thenationalnews.com"
    if publisher == domain_of(canonical) and "." in publisher:
        publisher = publisher.split(".")[0].replace("-", " ").title()

    desc = (raw.get("description") or "").strip()
    # Section 57: strip the duplicated headline, and never invent a summary.
    if desc:
        desc = strip_repeated_title(desc, title)
        if jaccard(title_key(desc), title_key(title)) > 0.9:
            desc = ""
    if desc:
        desc = _WS.sub(" ", desc)
        if len(desc) > 280:
            cut = desc[:280]
            sp = cut.rfind(" ")
            desc = (cut[:sp] if sp > 200 else cut).rstrip(" ,;:") + "…"
        if len(desc) < 40:
            desc = ""          # a fragment is worse than nothing

    hay = title + " · " + desc + " · " + " ".join(raw.get("categories") or [])
    tf = fold(hay)

    feed_country = raw.get("feed_country")
    primary, related, regional, evidence = gcc_signals(
        tf, feed_country, fold(title), bool(feed_country and feed_country in GCC))
    phil = philanthropy_signals(tf)
    ok, why = relevance(tf, primary, regional, phil)
    if not ok:
        return None, why

    topic = topic_of(tf)
    if topic == "Economy & Wealth" and not any_phrase(tf, ECONOMY_ADMIT):
        return None, "economy story with no philanthropy connection"

    orgs = match_organisations(hay, register_index, primary)

    # A PERIODIC REPORT WITH NO NAMED GULF ACTOR IS NOT A DEVELOPMENT. Observed failure:
    # "IOM Yemen Dispatch July 2026" reached the page as philanthropy news, its Gulf
    # connection being a line about arms transfers inside a monthly situation report. The
    # test is deliberately not conflict vocabulary, because humanitarian reporting discusses
    # wars legitimately; it is whether a Gulf organisation is the actor. The Qatar Charity
    # analysis of Sudan names one and stays. This names none and goes.
    periodic = bool(
        {fold(c) for c in (raw.get("categories") or [])} & {fold(f) for f in PERIODIC_FORMATS}
        or any_phrase(fold(title), PERIODIC_TITLE_TERMS))
    named_gulf_actor = bool(orgs) or any(": organisation " in e for e in evidence)
    if periodic and not named_gulf_actor:
        return None, "periodic report with no named Gulf actor"
    # An organisation whose register country contradicts the story's state is a strong sign
    # the geography was read from the wrong actor, so the organisation's own state wins.
    pub_orgs = [o for o in orgs if o.get("publishable")]
    if pub_orgs and primary == "GCC / Regional":
        cs = {o["country"] for o in pub_orgs if o.get("country")}
        if len(cs) == 1:
            primary = list(cs)[0]

    item = {
        "id": stable_id(canonical, title),
        "title": title,
        "description": desc or None,
        "original_url": original,
        "canonical_url": canonical,
        "publisher": publisher,
        "publisher_domain": domain_of(canonical),
        # THE PUBLISHER decides the type, not the feed that carried it. See publisher_type.
        "source_type": publisher_type(publisher, raw.get("source_type_hint") or "other"),
        "published_at": pub_at,
        "published_precision": prec,
        "discovered_at": now_iso(),
        "language": detect_language(title, raw.get("language")),
        "original_language": detect_language(title, raw.get("language")),
        # No translation is performed. Section 58: machine-translated reporting must never
        # be presented as original English journalism, so an Arabic headline ships in
        # Arabic with its own text direction and says nothing it cannot support.
        "translation": None,
        "primary_gcc_country": primary,
        "related_gcc_countries": related[:5],
        "destination_countries": destinations_in(tf, primary),
        "primary_topic": topic,
        "related_topics": related_topics(tf, topic),
        "event_type": event_of(tf),
        "organisations": orgs,
        "amount": extract_amount(title + " " + desc, primary),
        "image_url": None,
        # No image is carried in v1. The layout is built for none, and section 20 requires
        # licensing review before a provider thumbnail may be shown.
        "image_usage_status": "not_reviewed",
        "discovered_via": raw.get("discovered_via"),
        "cluster_id": None,
        "cluster_size": 1,
        "editorial": {"status": "published", "is_top": False, "priority": None,
                      "reviewed": False, "editor_note": None},
        "provenance": {"ingestion_run_id": None,
                       "query_id": raw.get("query_id"),
                       "provider_record_id": raw.get("guid") or None,
                       "registry_version": REGISTRY_VERSION,
                       "gcc_evidence": evidence[:6]},
        "_title_key": title_key(title),
        "_title_letters": title_key_letters(title),
        # Periodic reporting is real material and is not a TOP development. Computed above,
        # where it also decides admission for a report with no named Gulf actor.
        "_periodic": periodic,
        # Neither is an argument about what should happen, nor a retrospective on a
        # commemorative day. Both stay in the feed and neither leads it.
        "_advocacy": bool(any_phrase(fold(title), ADVOCACY_TITLE_TERMS)),
        "_commemorative": bool(any_phrase(fold(hay), COMMEMORATIVE_TERMS)),
    }
    return item, None
