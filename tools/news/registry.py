# The registries. Everything the pipeline classifies against lives here, in one versioned
# place, because the alternative is query strings scattered through adapter code where
# nobody can audit what the monitor is actually looking for.
#
# Four registries:
#   GEOGRAPHY   the six states, their cities and demonyms, and the destination countries
#   TAXONOMY    the controlled topic list, and the terms that assign a topic
#   EVENTS      what happened, as distinct from what field it is about
#   SOURCES     the feeds, with a type and an official flag per source
#
# Plus the two lists that decide whether a candidate is admitted at all: the philanthropy
# terms, and the NEGATIVE terms that stop "building foundation" and "strong financial
# foundation" from becoming philanthropy news.

REGISTRY_VERSION = "2026-08-20.1"

# --------------------------------------------------------------------------- geography
# related[] are the strings that identify the state in a headline. Demonyms are included
# because "Emirati donors" names the state without naming it. City names are here too but
# they are NOT decisive on their own: see score_country, where a city alone is worth less
# than a state name, because "Dubai-based fund gives to Kenya" is a UAE story and
# "conference in Dubai discusses African philanthropy" may not be.
GCC = {
    "Saudi Arabia": {
        "code": "sa",
        "names": ["saudi arabia", "ksa", "kingdom of saudi arabia"],
        "demonyms": ["saudi"],   # "saudi" is a demonym, not a state name. It was in both.
        "cities": ["riyadh", "jeddah", "mecca", "makkah", "medina", "madinah", "dammam",
                   "khobar", "dhahran", "taif", "abha", "tabuk", "neom", "diriyah"],
        # CURATED after two false organisation links reached the page. "prince sultan" was
        # matching Prince Sultan University and "king abdulaziz" matches a university, a
        # city, an airport and a foundation, so a fragment that opens many real names is not
        # usable as a name. Every entry here must be specific enough that it identifies one
        # institution on its own.
        "orgs": ["ksrelief", "king salman humanitarian aid and relief centre",
                 "king salman humanitarian aid", "king salman relief centre",
                 "king khalid foundation", "alwaleed philanthropies", "misk foundation",
                 "king abdulaziz foundation", "king abdulaziz and his companions foundation",
                 "king faisal foundation", "saudi fund for development",
                 "prince sultan bin abdulaziz foundation", "ehsan platform",
                 "ehsan foundation", "national platform for charitable work"],
    },
    "United Arab Emirates": {
        "code": "ae",
        "names": ["united arab emirates", "uae", "u.a.e.", "emirates"],
        "demonyms": ["emirati"],
        "cities": ["dubai", "abu dhabi", "sharjah", "ajman", "fujairah", "ras al khaimah",
                   "umm al quwain", "al ain", "masdar city"],
        # "zayed foundation" was adopting Ahmad Bin Zayed Foundation, and "erc" is three
        # letters. Generic city-plus-charity constructions removed: they are descriptions
        # rather than the names of single institutions.
        "orgs": ["dubai cares", "emirates red crescent",
                 "emirates red crescent authority", "abu dhabi fund for development",
                 "mohammed bin rashid al maktoum global initiatives",
                 "khalifa bin zayed al nahyan foundation", "zayed bin sultan al nahyan charitable",
                 "sharjah charity international", "the big heart foundation",
                 "big heart foundation", "dubai humanitarian city", "dubai humanitarian",
                 "emirates foundation", "al jalila foundation"],
    },
    "Qatar": {
        "code": "qa",
        "names": ["qatar", "state of qatar"],
        "demonyms": ["qatari"],  # "qatari" was in both lists, so one word scored 6 plus 4
        "cities": ["doha", "al rayyan", "lusail", "al wakrah", "education city"],
        "orgs": ["qatar charity", "qatar foundation", "qatar fund for development",
                 "education above all foundation", "education above all", "silatech",
                 "reach out to asia", "qatar red crescent society", "qatar red crescent",
                 "eaa foundation"],
    },
    "Kuwait": {
        "code": "kw",
        "names": ["kuwait", "state of kuwait"],
        "demonyms": ["kuwaiti"],
        "cities": ["kuwait city", "hawalli", "salmiya", "jahra"],
        # "direct aid" is the name of a real Kuwaiti charity AND an ordinary English phrase,
        # and it filed a UNHCR report about Sudan under Kuwait. Its registered name carries
        # more, so the longer forms stay and the bare phrase goes. "zakat house" likewise
        # collides with the ordinary noun, so it takes its full name.
        "orgs": ["kuwait fund for arab economic development", "kuwait fund",
                 "kuwait red crescent society", "kuwait red crescent",
                 "direct aid society", "africa muslims agency",
                 "kuwait zakat house", "zakat house of kuwait",
                 "international islamic charitable organization",
                 "abdullah al nouri charity society", "al najat charity",
                 "patient helping fund society"],
    },
    "Bahrain": {
        "code": "bh",
        "names": ["bahrain", "kingdom of bahrain"],
        "demonyms": ["bahraini"],
        "cities": ["manama", "riffa", "muharraq", "isa town", "hamad town", "sitra"],
        "orgs": ["royal humanitarian foundation", "bahrain red crescent society",
                 "bahrain red crescent",
                 "isa bin salman al khalifa charitable trust",
                 "isa bin salman al khalifa charitable",
                 "sheikh mohammed bin khalifa al khalifa charitable",
                 "ebdaa bank for microfinance", "bahrain charities fund"],
    },
    "Oman": {
        "code": "om",
        "names": ["oman", "sultanate of oman"],
        "demonyms": ["omani"],
        "cities": ["muscat", "salalah", "sohar", "nizwa", "sur", "duqm"],
        # "sultan qaboos" opens a university, a mosque, a port and a grand mosque. Removed
        # in favour of the forms that name one body.
        "orgs": ["oman charitable organization", "dar al atta a association",
                 "dar al atta", "sultan qaboos higher centre for culture and science",
                 "al noor association for the blind", "oman charitable fund"],
    },
}

# a story about several states, a GCC-wide policy, a regional fund or a regional conference
REGIONAL_TERMS = [
    "gcc", "gulf cooperation council", "gulf states", "arab gulf", "khaleeji",
    "arabian gulf", "gulf region", "across the gulf", "gulf-wide",
]

# International destinations, kept short and deliberate: these are the places GCC funders
# actually appear in the reporting this monitor covers. A long gazetteer would match
# incidental mentions and produce false destinations, which is worse than missing one.
DESTINATIONS = [
    "Sudan", "Yemen", "Syria", "Palestine", "Gaza", "Lebanon", "Jordan", "Iraq",
    "Afghanistan", "Pakistan", "Bangladesh", "Somalia", "Ethiopia", "Kenya", "Egypt",
    "Morocco", "Tunisia", "Libya", "Chad", "Niger", "Mali", "Nigeria", "Uganda",
    "Tanzania", "Mozambique", "Myanmar", "Indonesia", "Malaysia", "Sri Lanka", "Nepal",
    "Turkiye", "Turkey", "Ukraine", "Albania", "Bosnia and Herzegovina", "Kosovo",
    "Djibouti", "Eritrea", "South Sudan", "Central African Republic", "Burkina Faso",
    "Philippines", "India", "Maldives", "Comoros", "Mauritania", "Senegal", "Gambia",
    "Sierra Leone", "Guinea", "Tajikistan", "Kyrgyzstan", "Kazakhstan", "Azerbaijan",
]

# --------------------------------------------------------------------------- taxonomy
# The public topic list. Order matters: the first topic whose terms hit wins, so the
# specific sit above the general and "General" is the floor.
TOPICS = [
    ("Zakat & Waqf", ["zakat", "waqf", "awqaf", "endowment", "endowments", "sadaqah",
                      "sadaqa", "islamic social finance", "islamic philanthropy",
                      "qard hasan", "islamic finance for development"]),
    ("Funding & Grants", ["grant", "grants", "grantmaking", "funding", "funded", "pledge",
                          "pledged", "pledges", "commits", "committed", "donation",
                          "donations", "donated", "allocates", "allocated", "disburse",
                          "disbursed", "contribution", "awards", "awarded", "financing"]),
    ("Foundations", ["foundation", "foundations", "philanthropic institution",
                     "charitable foundation", "endowed foundation"]),
    ("Family Philanthropy & Family Offices", ["family office", "family offices",
                                              "family philanthropy", "family foundation",
                                              "next generation giving", "wealth transfer",
                                              "family business philanthropy"]),
    ("Corporate Philanthropy & CSR", ["csr", "corporate social responsibility",
                                      "corporate giving", "corporate philanthropy",
                                      "corporate foundation", "employee volunteering",
                                      "corporate donation", "esg and community"]),
    ("Impact Investment", ["impact investment", "impact investing", "impact fund",
                           "blended finance", "social investment", "social impact bond",
                           "outcome fund", "catalytic capital", "venture philanthropy"]),
    ("Humanitarian & Development", ["humanitarian", "relief", "emergency response",
                                    "appeal", "famine", "displaced", "refugee",
                                    "refugees", "aid convoy", "development assistance",
                                    "official development assistance", "oda", "flash appeal",
                                    "humanitarian financing", "food security", "shelter"]),
    ("Policy & Regulation", ["regulation", "regulator", "regulatory", "law", "decree",
                             "licence", "license", "licensing", "compliance",
                             "governance framework", "authority issued", "new rules",
                             "bylaw", "by-law", "legislation", "supervision"]),
    ("People & Leadership", ["appointed", "appointment", "names as chief executive",
                             "steps down", "resigns", "succeeds", "new chair",
                             "board member", "trustee", "secretary-general",
                             "director general", "chief executive"]),
    ("Nonprofit Sector", ["nonprofit", "non-profit", "ngo", "ngos", "civil society",
                          "third sector", "voluntary sector", "association",
                          "social enterprise", "charity sector"]),
    ("Giving & Donations", ["charity", "charitable", "giving", "donors", "donor",
                            "fundraising", "fundraiser", "volunteer", "volunteers",
                            "alms", "generosity"]),
    ("Economy & Wealth", ["private wealth", "high net worth", "wealth management",
                          "sovereign wealth", "philanthropic capital", "wealth report"]),
    ("Philanthropy", ["philanthropy", "philanthropic", "philanthropist", "philanthropists"]),
    ("General", []),
]

# What HAPPENED, as opposed to what field it is about. Internal in v1: not a public filter.
EVENT_TYPES = [
    ("funding_announcement", ["announces funding", "announced funding", "pledge", "pledged",
                              "commits", "committed", "allocates", "allocated", "earmarked"]),
    ("grant", ["grant", "grants", "grantmaking", "awarded a grant", "grant programme"]),
    ("donation", ["donation", "donated", "donates", "gift of", "contributes", "contributed"]),
    ("partnership", ["partnership", "partners with", "signs", "signed", "memorandum",
                     "mou", "agreement with", "joint initiative", "collaboration"]),
    ("new_foundation", ["launches foundation", "new foundation", "establishes foundation",
                        "founds", "sets up a foundation"]),
    ("new_organisation", ["establishes", "established", "launches a new", "inaugurates",
                          "opens a new", "sets up"]),
    ("new_programme", ["launches", "launched", "unveils", "rolls out", "new programme",
                       "new program", "initiative launched"]),
    ("leadership_change", ["appointed", "appointment", "steps down", "resigns", "succeeds",
                           "new chief executive", "new chair", "named as"]),
    # A LEGAL TRANSFORMATION IS AN EVENT. "Royal Order transforms charity platform Ehsan into
    # independent non-profit foundation" matched nothing here and was filed as general news at
    # weight 4, which kept the clearest institutional development on the page out of the top
    # selection entirely.
    ("policy_change", ["royal order", "royal decree", "cabinet decision",
                       "council of ministers", "transforms", "transformed into",
                       "converted into", "restructured as", "incorporated as",
                       "established as", "granted independent status", "becomes independent",
                       "policy", "strategy published", "framework", "new rules", "reform"]),
    ("regulation", ["regulation", "regulator", "decree", "law", "licensing", "bylaw",
                    "legislation", "issued a circular", "licensed as", "registered as"]),
    ("fund_launch", ["fund launch", "launches fund", "new fund", "closes fund",
                     "first close", "fund of"]),
    ("impact_investment", ["impact investment", "impact investing", "invests in"]),
    ("humanitarian_response", ["relief", "emergency", "response to", "appeal", "airlift",
                               "aid convoy", "flood response", "earthquake response"]),
    ("development_agreement", ["development agreement", "loan agreement", "concessional",
                               "soft loan", "financing agreement"]),
    ("research_publication", ["report", "study", "research", "survey", "publishes",
                              "published a report", "white paper", "index"]),
    ("conference", ["conference", "summit", "forum", "convening", "symposium"]),
    ("corporate_giving", ["csr", "corporate social responsibility", "corporate giving"]),
    ("zakat_initiative", ["zakat"]),
    ("waqf_endowment", ["waqf", "awqaf", "endowment"]),
    ("general_news", []),
]

# ------------------------------------------------------------------ the relevance gate
# A candidate must show BOTH a GCC signal AND a philanthropy signal. These are the
# philanthropy signals. Deliberately broader than the topic terms, because the topic
# assignment can afford to be strict while the gate should not throw away a real story
# whose vocabulary is unusual.
PHILANTHROPY_TERMS = sorted({t for _, terms in TOPICS for t in terms} | {
    "philanthropy", "philanthropic", "charity", "charitable", "donor", "donation",
    "grant", "endowment", "waqf", "zakat", "sadaqah", "humanitarian", "relief",
    "nonprofit", "ngo", "civil society", "foundation", "giving", "fundraising",
    "social investment", "impact investment", "development assistance", "aid",
    "volunteer", "csr", "corporate social responsibility", "community fund",
})

# THE NEGATIVE LIST. These are the phrases that make "foundation", "grant", "charity" and
# "impact" produce false positives, and every one of them is a real observed pattern
# rather than a hypothetical. A candidate whose ONLY philanthropy signal is cancelled by
# one of these is rejected.
NEGATIVE_PHRASES = [
    "building foundation", "foundation repair", "foundation stone", "foundation of the building",
    "concrete foundation", "foundation work", "laid the foundation stone", "piling and foundation",
    "strong financial foundation", "financial foundation for", "economic foundation",
    "legal foundation", "solid foundation for growth", "foundation for future growth",
    "lays the foundation for", "foundational model", "foundation model",
    "charity match", "charity game", "charity shield", "charity football", "charity run",
    "charity cup", "charity golf", "charity fashion",
    # Saudi Arabia's TAX AGENCY is named the Zakat, Tax and Customs Authority (formerly the
    # General Authority of Zakat and Tax). Its name put the word "zakat" into a story about
    # 90-day limits on GCC-registered vehicles, which then shipped as a top development on
    # the live desk (item 1659acfb4d8c112b, 2026-08-22). An agency name is not a
    # philanthropy signal; a real zakat-distribution story still carries its own vocabulary.
    "zakat, tax and customs", "general authority of zakat and tax",
    "research grant for", "phd grant", "study grant", "travel grant", "visa grant",
    "granted permission", "granted approval", "granted a licence to operate",
    "impact of the", "impact on the economy", "environmental impact assessment",
    "impact crater", "high impact plastic",
    "aid station", "first aid", "hearing aid", "aid to navigation",
    "endowment policy insurance", "endowment mortgage",
]

# Terms that make an Economy & Wealth story admissible. Section 24: the product must not
# become a generic Gulf economy feed, so an economy story needs one of these AND a
# philanthropy signal, and the exclusions below veto it outright.
ECONOMY_ADMIT = [
    "private wealth", "family office", "wealth transfer", "high net worth", "philanthropic",
    "philanthropy", "csr", "impact investment", "social investment", "foundation finance",
    "charitable regulation", "social finance", "development fund", "endowment",
]
ECONOMY_VETO = [
    "share price", "shares closed", "index closed", "stock exchange", "earnings per share",
    "quarterly profit", "net profit rose", "oil price", "brent crude", "opec output",
    "gdp growth", "inflation rate", "real estate launch", "off-plan", "property prices",
    "ipo priced", "bond yield", "dividend",
    # SOVEREIGN DEBT AND CAPITAL MARKETS. Added after a real false positive: "Saudi Arabia
    # allocates SR9.5 billion in August sukuk issuance" ranked as the second Top
    # Development. It is the National Debt Management Center borrowing money, and it passed
    # because "allocates" is a weak philanthropy signal. A government raising debt is not
    # giving, however large the figure and however much the verb resembles a grant.
    "sukuk", "debt management", "debt issuance", "bond issuance", "issuance under",
    "treasury bill", "treasury bond", "tranche", "coupon rate", "maturity in",
    "refinancing", "syndicated loan", "credit rating", "rating affirmed", "bourse",
    "capital increase", "rights issue", "money market", "repo rate", "yield curve",
    "national debt management",
]

# ADVOCACY AND COMMEMORATION ARE NOT DEVELOPMENTS. Two of the three items the ranking chose
# as Top Developments were, on an editor's reading, neither: an advocacy essay arguing what a
# response "must" do, and a World Humanitarian Day retrospective totalling giving since 1975.
# Both are legitimate feed material. Neither is something that happened. They won because
# freshness was worth a quarter of the score and both were published that morning.
ADVOCACY_TITLE_TERMS = [
    "why", "must", "opinion", "op-ed", "commentary", "analysis", "viewpoint",
    "reflections", "lessons", "what next", "the case for", "rethinking", "towards",
    "it is time", "we need", "how to",
]
COMMEMORATIVE_TERMS = [
    "world humanitarian day", "international day", "world day", "anniversary", "marks the",
    "recalls", "in review", "year in", "looking back", "milestone", "celebrates",
    "world refugee day", "ramadan campaign",
]

# Medical transplant reporting scores on "donor" and "donation" and is not sector news.
# From a real false positive: "Four brain-dead donors save lives of 14 patients".
MEDICAL_VETO = [
    "brain-dead", "brain dead", "organ donation", "organ donor", "organ donors",
    "organ transplant", "kidney transplant", "liver transplant", "cornea",
    "transplant operation", "deceased donor",
]

# ------------------------------------------------------------------- source registry
# type is one of: independent_media, official_government, official_organisation,
# un_multilateral, trade_publication, academic_research, other.
#
# enabled=False means the adapter exists and the source is documented but it is not
# fetched. Every disabled row carries the reason, measured, not guessed.
SOURCES = [
    {"id": "reliefweb_rss", "name": "ReliefWeb", "provider": "rss",
     "url": "https://reliefweb.int/updates/rss.xml",
     "type": "un_multilateral", "official": True, "enabled": True,
     # THE FLAG THAT STOPS A BYLINE BECOMING A PUBLISHER. On an aggregator, RSS <author> is
     # the credited source organisation and IS the publisher, which is what section 17
     # requires. On a newspaper it is a reporter's name. Taking author unconditionally put
     # "Ali Al Shouk", a journalist at The National, in the publisher slot on a real item.
     "publisher_from_author": True,
     "country": None, "lang": "en", "tier": 1,
     "note": "Publisher is the RSS <author>, the credited source organisation, NOT ReliefWeb. "
             "Supports ?search=. Needs no appname, unlike the v2 JSON API. "
             "MEASURED 2026-08-20 FROM A GITHUB RUNNER: HTTP 202, zero bytes, "
             "server awselb/2.0, on every query through four retries with backoff, while the "
             "identical requests return 200 and twenty items from a residential address. This "
             "is a deliberate block of datacentre traffic, so a scheduled job cannot use it. "
             "It stays enabled because it works when the build is run by hand, and because the "
             "supported route for automation is the v2 API row below, which needs an appname.",
     # BALANCED ACROSS THE SIX STATES, two queries each, after a measurement showed the
     # feed was 64 per cent Qatar with Bahrain and Oman at zero. The cause was this list:
     # three of the nine queries named Qatari bodies and not one named anything in Bahrain or
     # Oman. Nothing was looking for them. Two per state plus the two thematic queries, so
     # the shape of the feed reflects the Gulf rather than the shape of this list.
     "queries": [
         # Saudi Arabia
         "KSrelief", "Saudi Arabia humanitarian",
         # United Arab Emirates
         "Emirates Red Crescent", "United Arab Emirates humanitarian",
         # Qatar
         "Qatar Fund for Development", "Qatar Charity",
         # Kuwait
         "Kuwait Fund", "Kuwait humanitarian",
         # Bahrain, which had no query at all
         "Bahrain humanitarian", "Royal Humanitarian Foundation Bahrain",
         # Oman, which had no query at all
         "Oman humanitarian", "Oman Charitable Organization",
         # and the thematic ones, which belong to no single state
         "zakat", "waqf endowment"]},

    {"id": "thenational_ae", "name": "The National", "provider": "rss",
     "url": "https://www.thenationalnews.com/arc/outboundfeeds/rss/?outputType=xml",
     "type": "independent_media", "official": False, "enabled": True,
     "country": "United Arab Emirates", "lang": "en", "tier": 1, "note": "", "queries": []},

    {"id": "saudigazette", "name": "Saudi Gazette", "provider": "rss",
     "url": "https://saudigazette.com.sa/rssFeed/74",
     "type": "independent_media", "official": False, "enabled": True,
     "country": "Saudi Arabia", "lang": "en", "tier": 2, "note": "", "queries": []},

    {"id": "unocha", "name": "UN OCHA", "provider": "rss",
     "url": "https://www.unocha.org/rss.xml",
     "type": "un_multilateral", "official": True, "enabled": True,
     "country": None, "lang": "en", "tier": 1, "note": "", "queries": []},

    # VERIFIED FROM A GITHUB RUNNER: 200, 50 items. A Qatari daily a scheduled job can
    # actually read, which matters because the source that carried most of Qatar's coverage
    # cannot be read from there at all.
    {"id": "gulftimes_qa", "name": "Gulf Times", "provider": "rss",
     "url": "https://www.gulf-times.com/rssFeed/1",
     "type": "independent_media", "official": False, "enabled": True,
     "country": "Qatar", "lang": "en", "tier": 1, "note": "", "queries": []},

    # VERIFIED FROM A GITHUB RUNNER: 200, 10 items. Sector trade press, global, so most items
    # fail the Gulf gate; kept because when it covers the Gulf it covers it properly.
    {"id": "chronicle_phil", "name": "The Chronicle of Philanthropy", "provider": "rss",
     "url": "https://www.philanthropy.com/feed",
     "type": "trade_publication", "official": False, "enabled": True,
     "country": None, "lang": "en", "tier": 2, "note": "", "queries": []},

    {"id": "alliance_mag", "name": "Alliance magazine", "provider": "rss",
     "url": "https://www.alliancemagazine.org/feed/",
     "type": "trade_publication", "official": False, "enabled": True,
     "country": None, "lang": "en", "tier": 2,
     "note": "Sector trade press. Global, so most items fail the GCC gate. Kept because "
             "when it does write about the Gulf it is the most specific reporting there is.",
     "queries": []},

    {"id": "arabianbusiness", "name": "Arabian Business", "provider": "rss",
     "url": "https://www.arabianbusiness.com/feed",
     "type": "independent_media", "official": False, "enabled": False,
     "country": None, "lang": "en", "tier": 1,
     "note": "MEASURED 2026-08-20: HTTP 403 to a declared research user agent. Respected "
             "rather than worked around with a browser UA. Re-test before enabling.",
     "queries": []},

    {"id": "gdelt_doc", "name": "GDELT DOC 2.0", "provider": "gdelt_doc",
     "url": "https://api.gdeltproject.org/api/v2/doc/doc",
     "type": "other", "official": False, "enabled": False,
     "country": None, "lang": "en,ar", "tier": 3,
     "note": "MEASURED 2026-08-20: HTTP 429 on 4 of 4 attempts spaced 7s apart, from this "
             "egress. Body asks for one request every 5 seconds and points high-traffic "
             "users at the ngrams dataset. Adapter is written and unit-tested against a "
             "recorded payload. Enable only after a live 200 is observed from the host "
             "that will actually run it.",
     "queries": []},

    {"id": "reliefweb_api", "name": "ReliefWeb v2 API", "provider": "reliefweb_api",
     "url": "https://api.reliefweb.int/v2/reports",
     "type": "un_multilateral", "official": True, "enabled": False,
     "country": None, "lang": "en", "tier": 1,
     "note": "MEASURED 2026-08-20: no appname gives HTTP 400 'Missing appname parameter'; an "
             "unapproved appname gives HTTP 403 'You are not using an approved appname'. "
             "Needs an appname requested from ReliefWeb. The RSS row above covers this "
             "source meanwhile with fewer fields.",
     "queries": []},

    {"id": "newsdata", "name": "NewsData", "provider": "newsdata",
     "url": "https://newsdata.io/api/1/latest",
     "type": "other", "official": False, "enabled": False,
     "country": None, "lang": "en,ar", "tier": 3,
     "note": "Needs NEWSDATA_KEY. Free feed is delayed, so it must never be used to claim "
             "the page is live. Untested: no key on this machine, so nothing about its "
             "behaviour is claimed here.",
     "queries": []},

    {"id": "currents", "name": "Currents", "provider": "currents",
     "url": "https://api.currentsapi.services/v2/search",
     "type": "other", "official": False, "enabled": False,
     "country": None, "lang": "en", "tier": 3,
     "note": "Needs CURRENTS_KEY. Free tier is for prototyping; redistribution terms need "
             "review before public use. Untested: no key on this machine.",
     "queries": []},

    # DISQUALIFIED, kept so the decision is not silently re-made by someone who notices
    # that Google News RSS is keyless and returns a hundred items.
    {"id": "google_news_rss", "name": "Google News RSS", "provider": "rss",
     "url": "https://news.google.com/rss/search",
     "type": "other", "official": False, "enabled": False,
     "country": None, "lang": "en,ar", "tier": 9,
     "note": "DISQUALIFIED, do not enable. MEASURED 2026-08-20: item <link> is a "
             "news.google.com/rss/articles/CBMi... redirect wrapper and <guid> carries "
             "isPermaLink=false, so the publisher's own article URL is not in the feed. "
             "'Read original' would send readers to a Google redirect, and resolving it "
             "server-side is exactly the arbitrary-URL fetch that is out of scope. Its "
             "<source url=> does name the real publisher, which is not enough.",
     "queries": []},
]


# ------------------------------------------------------------- publisher type
# Source type must describe the PUBLISHER, not the feed that carried the item. Taking it
# from the feed labelled twenty Qatar Charity press releases "un_multilateral", which
# destroys the one distinction this product exists to make.
#
# Ordered, first match wins. Patterns are matched against the folded publisher name, so
# they generalise past the eighteen publishers observed in the first runs.
PUBLISHER_TYPES = [
    ("un_multilateral", [
        "united nations", "un high commissioner", "un office for the coordination",
        "un development programme", "un children", "unicef", "unhcr", "unrwa", "unops",
        "undp", "unfpa", "unesco", "unido", "uncdf", "ocha", "world food programme",
        "world health organization", "world health organisation",
        "international organization for migration", "international organisation for migration",
        "food and agriculture organization", "international labour organization",
        "global polio eradication", "world bank", "international monetary fund",
        "international committee of the red cross",
        "international federation of red cross", "gavi", "global fund",
        "islamic development bank", "asian development bank", "african development bank",
    ]),
    ("official_government", [
        "government of", "ministry of", "ministry for", "state of", "royal embassy",
        "embassy of", "national debt management", "general authority", "central bank of",
        "presidency of", "office of the prime minister", "european commission",
        "european union", "foreign commonwealth", "usaid", "european civil protection",
    ]),
    ("official_organisation", [
        "charity", "charitable", "foundation", "red crescent", "red cross society",
        "fund for development", "relief centre", "relief center", "ksrelief",
        "humanitarian aid and relief", "endowment", "awqaf", "zakat",
        "philanthropies", "trust", "aid agency", "development fund", "waqf",
    ]),
    ("trade_publication", [
        "alliance magazine", "devex", "philanthropy news", "chronicle of philanthropy",
        "third sector", "civil society media", "arab news business",
    ]),
    ("academic_research", [
        "university", "school of", "institute for", "research centre", "research center",
        "college", "academy of",
    ]),
    ("independent_media", [
        "the national", "saudi gazette", "arab news", "gulf news", "gulf times",
        "arabian business", "khaleej times", "reuters", "associated press",
        "bloomberg", "financial times", "agence france", "the guardian", "bbc",
        "al jazeera", "asharq", "zawya", "kuwait times", "oman observer",
        "gulf daily news", "times of oman", "muscat daily", "emirates news agency",
        "saudi press agency", "qatar news agency", "kuwait news agency", "gazette",
        "daily", "post", "herald", "tribune", "news agency",
    ]),
]


# THE ALIAS FLOOR. An alias is only usable as evidence that a particular institution is in
# the story if it is specific enough to be a name. Two tokens and ten characters, and not a
# phrase that occurs in ordinary sector English. Checked at import so a careless future
# addition fails loudly rather than quietly filing someone else's news under the wrong state.
ALIAS_STOPWORDS = {
    "direct aid", "zakat house", "charity organisation", "charity organization",
    "red crescent", "red cross", "humanitarian aid", "relief centre", "relief center",
    "charitable trust", "charitable society", "development fund", "aid agency",
    "prince sultan", "king abdulaziz", "sultan qaboos", "zayed foundation",
    "dubai charity", "bahrain charity", "sharjah charity", "oman charitable",
}


# Single-token aliases that have been checked one at a time. Each is a coined name with no
# ordinary-English meaning and no other institution sharing its opening, so it can identify a
# body on its own. Anything not on this list must be at least two tokens: that is what stopped
# "prince sultan" from adopting Prince Sultan University.
ALIAS_SINGLE_TOKEN_OK = {"ksrelief", "silatech", "mbrgi", "sanabil", "misk"}


def _audit_aliases():
    """Fails the import if an alias is too short or too generic to identify one institution."""
    bad = []
    for state, d in GCC.items():
        for a in d.get("orgs", []):
            f = a.lower().strip()
            if f in ALIAS_STOPWORDS:
                bad.append((state, a, "in the stoplist of ordinary phrases"))
            elif len(f) < 6:
                bad.append((state, a, "shorter than 6 characters"))
            elif len(f.split()) < 2 and f not in ALIAS_SINGLE_TOKEN_OK:
                bad.append((state, a,
                            "a single token not on the vetted single-token list"))
    if bad:
        raise AssertionError(
            "unusable organisation aliases, each would misattribute a story:\n" +
            "\n".join("  %s: %r, %s" % b for b in bad))


_audit_aliases()


def publisher_type(publisher, fallback="other"):
    """Folded, whole-substring matching on the publisher name. Substring is correct here,
    unlike in the relevance gate, because these are institution-name fragments matched
    against an institution name rather than words matched against prose."""
    p = (publisher or "").lower()
    if not p:
        return fallback
    for t, pats in PUBLISHER_TYPES:
        for pat in pats:
            if pat in p:
                return t
    return fallback


# Document formats that mean periodic reporting rather than a development. ReliefWeb
# declares the format in its RSS categories, which is more reliable than reading the title.
PERIODIC_FORMATS = {"situation report", "infographic", "map", "assessment",
                    "manual and guideline", "evaluation and lessons learned",
                    "other", "appeal", "ugc"}
PERIODIC_TITLE_TERMS = [
    "factsheet", "fact sheet", "dispatch", "situation report", "sitrep", "flash update",
    "snapshot", "bulletin", "country brief", "operational update", "monthly report",
    "quarterly report", "annual report", "who is doing what", "3w", "dashboard",
    "funding update", "statistical report", "weekly update", "periodic report",
]


def enabled_sources():
    return [s for s in SOURCES if s.get("enabled")]


def source_by_id(sid):
    for s in SOURCES:
        if s["id"] == sid:
            return s
    return None
