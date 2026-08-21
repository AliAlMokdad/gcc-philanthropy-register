# -*- coding: utf-8 -*-
# The three documents, with the contact address filled in and the search-retention
# question answered from the worker source rather than left as a placeholder.

CONTACT = "connect@gccphilanthropy.org"
DATED = "21 August 2026"

# The connect form posts here. gccphilanthropy.org is served by GitHub Pages, which cannot run
# a script, so the receiver lives on the cPanel that already holds the connect@ mailbox. Same
# arrangement, and the same proven pattern, as the Sector Debrief contact form.
RECEIVER = "https://alialmokdadleadership.com/gccp-connect.php"

# The one-line description under each part title. It lived in the Word builder AND in the web
# builder, which is two copies of the same sentence and therefore a drift waiting to happen.
# A partner review caught it. One home, both renderers read it from here.
NOTICE = ("This register is an independent reference work. It is not affiliated with, endorsed by, sponsored by or connected to the Cooperation Council for the Arab States of the Gulf, its General Secretariat or any of its member states, and it is not an official or governmental publication of any of them. Nothing published here is an official act, statement or record of any government, ministry, regulator or listed organisation, and it must not be relied upon as one.")

STANDFIRST = {
    "privacy": "How the register handles data, what it does not collect, and your rights.",
    "terms":   "The terms on which the register may be read, quoted, cited and reused.",
    "faq":     "",
}

# The page titles, for the same reason as the standfirsts. A second partner review pointed out
# that "Privacy Policy" and "Frequently Asked Questions" were also typed into both builders, so
# the claim that every word comes from here was true of the bodies and not of the headings.
# TITLE is the heading on the page, TAB is the short word on the page tab.
TITLE = {"privacy": "Privacy Policy",
         "terms":   "Terms of Use",
         "faq":     "Frequently Asked Questions",
         "connect": "Connect"}
TAB   = {"privacy": "Privacy Policy",
         "terms":   "Terms of Use",
         "faq":     "FAQ",
         "connect": "Connect"}

# The connect form's own strings. These are the ONLY words in the built pages that are not a
# statement from the notices, and they are here so the list is auditable rather than a claim in a
# comment. "Website" is the honeypot's label: the trap has to look like a real field to a bot, so
# it needs a real label, and a second partner review was right that leaving it undeclared made the
# stated exception list inaccurate.
CONNECT_ALT = ("Or connect by email, at " + CONTACT + ". Corrections, sources and errors are welcome, and a message that names the page and the problem gets dealt with fastest.")

FORM = {"name": "Name", "email": "Email", "message": "Message", "trap": "Website",
        "send": "Send", "human": "I am not a robot", "version": "Version",
        "sent":   "Sent. A copy is on its way to " + CONTACT + ".",
        "failed": "Not sent. Nothing was delivered, so please write to " + CONTACT + " instead."}

PRIVACY = [
 ("h2", "1", "Who is responsible"),
 ("p", "I, Ali Al Mokdad, operate this site, and I am the data controller for it within the "
       "meaning of the General Data Protection Regulation (EU) 2016/679 (GDPR)."),
 ("kv", "Contact for any question or request under this policy", CONTACT),

 ("h2", "2", "What this policy covers"),
 ("p", "This policy covers gccphilanthropy.org and its sections, including the register, the "
       "funding intelligence, the news desk, the toolkit and the member states pages. It does "
       "not cover any external website you reach by following a link from here."),

 ("h2", "3", "What the site does not do"),
 ("p", "The site sets no cookies. It runs no analytics, no tag manager, no advertising, no "
       "tracking pixels and no social plug-ins. It stores nothing in your browser: no cookies, "
       "no local storage, no session storage. There are no user accounts, no logins and no "
       "newsletter."),
 ("p", "Nothing on the site asks you for personal data except the connect form, which is "
       "used only if you choose to write. The technical processing that occurs on an ordinary "
       "visit is set out in section 4, and none of it is used to identify you or to build a "
       "profile of you."),

 ("h2", "4", "What is processed, and why"),
 ("p", "Four kinds of processing occur."),
 ("lead", "4.1 Hosting records.",
       " The site is served by GitHub Pages, a service of GitHub, Inc. (a Microsoft company). "
       "To deliver a page, GitHub receives and may log your IP address, the requested address, "
       "the time of the request and the identifying string your browser sends. This is "
       "technically necessary to serve the site and to protect it from abuse, and is carried "
       "out on the basis of legitimate interests under Article 6(1)(f) GDPR. I do not receive "
       "these records and cannot link them to you."),
 ("lead", "4.2 Fonts.",
       " The typefaces used by the site are requested from Google Fonts, a service of Google "
       "Ireland Limited. Your browser therefore contacts Google servers, and Google receives "
       "your IP address as part of that request. The basis is legitimate interests under "
       "Article 6(1)(f): presenting the register in the typefaces it is designed in. If you "
       "prefer that Google not receive the request, blocking "
       "third-party fonts in your browser prevents it, and the site remains fully readable in "
       "a substitute typeface."),
 ("lead", "4.3 Search.",
       " The register carries a search that understands a description rather than only "
       "keywords. If, and only if, you run a search, the words you type are sent to a search "
       "service I operate, which runs on Cloudflare Workers, a service of Cloudflare, Inc. "
       "Cloudflare receives your IP address in order to route that request. The basis is legitimate interests under Article 6(1)(f): you asked "
       "for a search, and it cannot be performed without sending the words you typed."),
 ("p", "That service keeps nothing. It has no database and no key-value store, it writes no "
       "record of the words you type, and it passes them to no company other than Cloudflare, "
       "on whose platform it runs. Three models process a search there: two that measure how "
       "closely your description matches an organisation's published mandate, and one that "
       "writes the short explanation of why a result was returned."),
 ("p", "Do not type personal data, confidential information or anything you would not wish "
       "to leave your own machine. The field is for describing what an organisation funds, "
       "and nothing more is needed from you."),

 ("lead", "4.4 The connect form.",
       " If you write through the connect page, the name, the email address and the message "
       "you enter are sent to a script on my own hosting at Namecheap, which forwards them "
       "to two mailboxes I read. The basis is Article 6(1)(f): you asked to be put in "
       "contact, and the message cannot reach me otherwise. The check that you are a person "
       "runs on the page itself and involves no other company. Your message is kept in "
       "those mailboxes as correspondence and nowhere else. It is not written to a database, "
       "it is not published, it is used only to answer you, and it is deleted on request."),

 ("p", "No automated decision-making or profiling within the meaning of Article 22 GDPR "
       "takes place. The search ranks published mandates against the words you type. It "
       "reaches no decision about you and builds no profile of you."),

 ("h2", "5", "Transfers outside the European Economic Area"),
 ("p", "GitHub, Google, Cloudflare and Namecheap are established in, or transfer data to, "
       "the United States. Where a provider is certified under the EU-US Data Privacy Framework, the "
       "transfer relies on the European Commission adequacy decision for that framework. "
       "Where it is not, the transfer relies on that provider's standard contractual "
       "clauses. Their own privacy notices govern what they do with data they receive:"),
 ("bul", "GitHub: docs.github.com/site-policy"),
 ("bul", "Google: policies.google.com/privacy"),
 ("bul", "Cloudflare: cloudflare.com/privacypolicy"),
 ("bul", "Namecheap: namecheap.com/legal/general/privacy-policy"),

 ("h2", "6", "Retention"),
 ("p", "I keep no records of visitors, so there is nothing about your use of this site to "
       "retain, delete or disclose. Records held by the providers named in section 4 are kept "
       "under their own policies and are outside my control."),
 ("p", "Personal data appearing in a listed contact route is a separate matter. It is kept "
       "only for as long as the organisation itself still publishes it and it remains "
       "relevant to the entry, and it is removed sooner on request under section 8."),

 ("h2", "7", "Your rights"),
 ("p", "Where personal data concerning you is processed, the GDPR gives you the right to "
       "obtain access to it, to have it corrected or erased, to have its processing "
       "restricted, and to object to processing based on legitimate interests. Where Article 20 "
       "applies, you may also receive the data in a portable form. To exercise any of these, "
       "write to the address in section 1."),
 ("p", "Because I hold no visitor data, a request about your use of this site will usually be "
       "answered by telling you so and directing you to the provider that holds the record. I "
       "will answer within one month."),

 ("h2", "8", "Organisations listed in the register"),
 ("p", "The register describes organisations, not individuals. Entries carry an organisation "
       "name, country, city, mandate and its own published contact routes, compiled from "
       "public sources."),
 ("p", "Where a listed contact route identifies a person, for example a named officer or a "
       "personal mailbox published by the organisation itself, that is personal data and the "
       "following applies. It is processed on the basis of legitimate interests under Article "
       "6(1)(f), for a public-interest reference work on philanthropic funding in the Gulf. If "
       "you are that person, you may ask for the detail to be corrected or removed, and you do "
       "not need to give a reason. Write to the address in section 1 and it will be dealt with "
       "promptly. Section 8 of the Terms of Use sets out the same route for organisations."),

 ("h2", "9", "Children"),
 ("p", "The site is a reference work for researchers, journalists and non-profit "
       "organisations. It is not directed at children and collects nothing from anyone."),

 ("h2", "10", "Changes"),
 ("p", "If the site starts to process anything it does not process today, this policy will be "
       "amended before that change goes live, and the date at the top will be updated. "
       "Material changes will be described at the top of this policy so a returning reader can "
       "see what moved."),
]

TERMS = [
 ("h2", "1", "Agreement"),
 ("p", "These terms govern your use of gccphilanthropy.org. By using the site you accept them. "
       "If you do not accept them, do not use the site."),
 ("p", "Ali Al Mokdad publishes and maintains the site (the compiler). The register means "
       "everything published here: the organisations, the figures, the written commentary and "
       "the reference pages."),

 ("h2", "2", "What the register is, and what it is not"),
 ("p", "The register is an independent reference work compiled from publicly available "
       "sources. It is not affiliated with, endorsed by, sponsored by or connected to the "
       "Cooperation Council for the Arab States of the Gulf, its General Secretariat, any of "
       "its member states, or any organisation listed in it. Nothing on the site should be "
       "read as speaking for any of them."),
 ("p", "Inclusion in the register is not an endorsement of an organisation, and exclusion is "
       "not a judgement about one."),

 ("h2", "3", "Accuracy"),
 ("p", "The register is compiled with care and is offered without any warranty as to accuracy, "
       "completeness or fitness for a particular purpose. Laws, regulators, mandates, tax "
       "treatment, funding windows and contact details change, and public sources are "
       "sometimes wrong or out of date."),
 ("p", "Where an entry or a figure matters to a decision, verify it against the primary "
       "authority before acting. Each source is named on the site so that this is possible."),

 ("h2", "4", "Not advice"),
 ("p", "The site is information, not advice. It is not legal, tax, financial, accounting, "
       "regulatory or investment advice, and it is not a solicitation, offer or recommendation "
       "to give, receive or seek funding. No relationship of adviser and client arises from "
       "using it. Obtain qualified advice on your own facts."),

 ("h2", "5", "Two records that cannot be added together"),
 ("p", "The funding intelligence draws on two distinct records: the United Nations Office for "
       "the Coordination of Humanitarian Affairs Financial Tracking Service, which reports "
       "humanitarian contributions, and the OECD Development Assistance Committee, which "
       "reports official development assistance by states. They use different definitions, "
       "boundaries and reporting rules."),
 ("p", "The site keeps them apart, and so must you. Presenting a sum of the two, or either as "
       "a total of Gulf giving, misstates both."),

 ("h2", "6", "What you may do"),
 ("p", "You may read the site, quote from it and cite it, including in research, journalism "
       "and funding applications, provided the register is credited as the source and any "
       "figure is attributed to the record it came from."),

 ("h2", "7", "What you may not do"),
 ("p", "You may not:"),
 ("let", "a.", "copy or extract the dataset in bulk, by automated means or otherwise, or "
       "republish it as your own or as part of another product or database;"),
 ("let", "b.", "use the contact details published here to send unsolicited marketing, bulk "
       "solicitations or automated messages, or supply them to anyone else for that purpose;"),
 ("let", "c.", "present the register, or any part of it, as an official or endorsed "
       "publication of the Cooperation Council, of a member state, or of a listed "
       "organisation;"),
 ("let", "d.", "interfere with the site or the services it depends on, or attempt to gain "
       "access to any part of it that is not published; or"),
 ("let", "e.", "use the site in breach of any law that applies to you, including sanctions and "
       "data protection law."),

 ("h2", "8", "Corrections and removal"),
 ("p", "If you are an organisation listed here, or a person named in an entry, and something "
       "is wrong, out of date or should not be published, write to " + CONTACT + ". Say what "
       "the entry says and what it should say."),
 ("p", "Corrections are made on the merits. Requests about personal details are handled under "
       "section 8 of the privacy policy. A request to remove an entire organisation from a "
       "public-interest reference work is weighed on its merits, and you will be told the "
       "outcome either way."),

 ("h2", "9", "Rights in the content"),
 ("p", "The selection, arrangement, verification and written commentary in the register are "
       "the work of the compiler and are protected by copyright."),
 ("p", "Facts are not owned by anyone. Names, flags, emblems, trade marks and quoted text "
       "belong to their respective owners, and are used here for identification and "
       "reference. Where text is reproduced from a source, it is attributed and linked to that "
       "source, and the rights in it remain with the source."),
 ("p", "Nothing in these terms transfers any right in third-party material."),

 ("h2", "10", "Third-party sites"),
 ("p", "Links point to sources so that a reader can check them. The compiler does not control "
       "those sites, does not adopt their content and is not responsible for it."),

 ("h2", "11", "Availability"),
 ("p", "The site is published free of charge and is offered as it is and as available. It may "
       "be changed, interrupted or withdrawn at any time, and no undertaking is given that it "
       "will remain online or that any part of it will be maintained."),

 ("h2", "12", "Limitation of liability"),
 ("p", "To the fullest extent permitted by law, the compiler is not liable for any loss "
       "arising from use of the site or reliance on its content, including lost funding, lost "
       "profit, lost opportunity, lost data or indirect or consequential loss."),
 ("p", "Nothing in these terms limits liability that cannot lawfully be limited, including "
       "liability for death or personal injury caused by negligence, or for fraud."),

 ("h2", "13", "Governing law"),
 ("p", "These terms and any dispute arising from them are governed by Danish law, and the "
       "Danish courts have jurisdiction. If you are a consumer, this does not deprive you of "
       "the protection of the mandatory law of your country of residence."),

 ("h2", "14", "Changes to these terms"),
 ("p", "These terms may be amended. The version in force is the one published on this page, "
       "with the date shown at the top, and an amended version takes effect when it is "
       "published."),
]

FAQ = [
 ("grp", "The register"),
 ("q", "What is this?"),
 ("a", "A free, public register of philanthropic funders across the six states of the Gulf "
       "Cooperation Council: 1,862 organisations with their country, city, type, mandate and "
       "published contact routes, and a funding intelligence layer built on two official "
       "records. Of those entries, 1,467 carry a website, 1,169 a telephone number and 946 an "
       "email address."),
 ("q", "Who is behind it?"),
 ("a", "One person. It is compiled and maintained independently by Ali Al Mokdad, and it is "
       "not affiliated with the Cooperation Council, any member state, or any organisation "
       "listed in it."),
 ("q", "Who is Ali Al Mokdad?"),
 ("a", "Senior Strategic Leader in Global Impact Operations, Governance Reform, and Humanitarian "
       "Diplomacy."),
 ("more", "more", "../alialmokdad/"),

 ("q", "Why does it exist?"),
 ("a", "Because the information existed and was scattered. A researcher who wanted to know who "
       "funds what in the Gulf had to assemble it from ministry pages, annual reports and news "
       "archives, one organisation at a time. This is that work, done once and published."),
 ("q", "What does it cost, and who pays for it?"),
 ("a", "It is free to use and there is no funder behind it. No sponsor, no advertising and "
       "no paid placement. The site runs on free hosting."),

 ("grp", "The data"),
 ("q", "Where does it come from?"),
 ("a", "Public sources: the websites and reports of the organisations themselves, national "
       "registers and regulators, and the two funding records named below. Every figure on the "
       "intelligence pages names the record it came from."),
 ("q", "How current is it?"),
 ("a", "Entries are added and corrected in rounds rather than continuously. Contact routes and "
       "mandates drift, so treat the register as a starting point and confirm anything that "
       "matters against the organisation itself."),
 ("q", "Why are some fields blank?"),
 ("a", "Because the source left them blank. A field is shown empty rather than filled from a "
       "guess or a different source, so an empty field means the underlying record is silent, "
       "not that the entry is unfinished."),
 ("q", "Can I download the whole dataset?"),
 ("a", "Not as a bulk export. You are welcome to read, quote and cite it, and the terms of use "
       "prohibit bulk extraction and republication of the dataset. If you have a research use "
       "that needs "
       "more than the site allows, write to " + CONTACT + "."),

 ("grp", "The numbers"),
 ("q", "What are the two records, and why are they kept apart?"),
 ("a", "The UN OCHA Financial Tracking Service records humanitarian contributions. The OECD "
       "Development Assistance Committee records official development assistance, meaning aid "
       "reported by states. They count different things by different rules."),
 ("q", "So can I add them together for a total?"),
 ("a", "No. Adding them double-counts in places, misses private giving that neither record "
       "captures, and mixes state-reported aid with humanitarian contributions as though they "
       "were one flow. Cite each on its own and say which it is."),
 ("q", "Is private philanthropy included in those figures?"),
 ("a", "Largely not. Most private Gulf giving is not reported to either record. The "
       "intelligence layer describes what the two official records show, which is a part of "
       "the picture and not the whole of it."),

 ("grp", "Using the site"),
 ("q", "How does the search work?"),
 ("a", "Describe what you are looking for in ordinary words, such as scholarships for refugees "
       "or eye care, rather than guessing the name of an organisation. The search reads the "
       "meaning of the description and ranks mandates against it, and it will return nothing "
       "rather than offer a poor match."),
 ("q", "Where do the search words go?"),
 ("a", "To a search service the register operates, so that the ranking can be computed. They "
       "are not stored there, nothing is kept in your browser and no profile is built. The "
       "privacy policy sets this out, and the practical guidance is short: do not type "
       "anything into the box that you would not want to leave your own machine."),
 ("q", "Does the site track me?"),
 ("a", "No. No cookies, no analytics, no advertising, no accounts. The one third party your "
       "browser contacts on a normal visit is Google Fonts, which serves the typefaces."),
 ("q", "Can I use the contact details to approach a funder?"),
 ("a", "Yes, for a genuine, individual approach about your work. Not for bulk mail, mailing "
       "lists or automated outreach, which the terms of use prohibit and which would put the "
       "publication of these addresses at risk."),

 ("grp", "Corrections and use in your own work"),
 ("q", "An entry about my organisation is wrong. How do I fix it?"),
 ("a", "Write to " + CONTACT + ", saying what the entry says now and what it should say. "
       "Corrections from the organisation itself are taken as authoritative."),
 ("q", "I want my name or my personal email removed."),
 ("a", "It will be removed on request. Section 8 of the privacy policy sets out that right and "
       "how it is handled."),
 ("q", "How should I cite the register?"),
 ("a", "Name the register, the page, and the date you consulted it, and attribute any figure "
       "to the record it came from rather than to the register. Example: GCC Philanthropy "
       "Register, Saudi Arabia, consulted 21 August 2026; contribution figure from UN OCHA "
       "FTS."),
 ("q", "Can I reuse a chart or a table in a report?"),
 ("a", "Yes, with the register credited and the underlying record named. Do not present it as "
       "an official publication of the Cooperation Council or of a member state, because it is "
       "not one."),
 ("q", "Is the toolkit legal advice?"),
 ("a", "No. The toolkit is a set of practice-oriented research syntheses, not peer-reviewed "
       "studies and not advice. Laws and regulator services change, so check the current "
       "primary authority before acting on anything in it."),

 ("grp", "Getting in touch"),
 ("q", "How do I reach you?"),
 ("a", "By email, at " + CONTACT + ". Corrections, sources and errors are welcome, and a "
       "message that names the page and the problem gets dealt with fastest."),
 ("q", "Will you add my organisation?"),
 ("a", "Possibly. Send the published description the organisation gives of what it funds and "
       "where, and it will be assessed against the same sources as everything else already in "
       "the register."),
]


# ---------------------------------------------------------------------------------------------
# THE ABOUT PAGE. The substance below came from alialmokdad.com/about-me, fetched and parsed rather
# than retyped. It is no longer verbatim: Ali asked for the page to speak ABOUT him rather than as
# him, so the first person has been carried into the third throughout. Every fact, every country,
# every institution and every figure is his own and unchanged; only the person and the pronouns
# moved. Apostrophes are normalised to the straight mark, the convention the rest of this module
# uses.
#
# The eyebrow and the closing line are deliberately empty. He asked for "Strategic Leader ·
# Advisor" and "Cross-functional experience across different organisations" to go, and for one
# descriptor to carry the role instead, which is the subtitle. The template skips an empty string
# rather than printing an empty element.
ABOUT = {
    "eyebrow":  "",
    "name":     "Ali Al Mokdad",
    "subtitle": "Senior Strategic Leader in Global Impact Operations, Governance Reform, "
                "and Humanitarian Diplomacy.",
    "journey_h": "The Journey",
    "journey": [
        "From the earliest days of his career as a volunteer in local nonprofit initiatives, one conviction shaped everything: that purpose-driven work, executed with discipline and heart, can transform communities.",
        "That conviction carried him across the Middle East, Asia, and Africa, managing programs and leading operations in some of the world's most demanding environments. Through every challenge, he rose from field roles into regional leadership and, ultimately, to strategic positions at the highest organisational levels.",
        "Hard work and a relentless commitment to those in need have defined his path. The resilience forged in those early years became the foundation for everything he now brings to leaders, teams, and institutions seeking to make a lasting difference.",
    ],
    "about_label": "About",
    "about_h":     "Ali Al Mokdad",
    "about": [
        "Ali Al Mokdad is a strategic senior leader with a career built in the most complex and consequential arenas on the planet. He has led programs and operations within International NGOs, United Nations agencies, the International Federation of Red Cross and Red Crescent Societies, and global donor institutions, earning recognition for operational excellence, strategic planning, and transformational leadership.",
        "His work spans operations in the Middle East, Africa, and Asia, across countries including Syria, Iraq, Jordan, Lebanon, Turkey, Nigeria, Kenya, South Sudan, Afghanistan, and Bangladesh. He has led cross-border regional operations and overseen global networks spanning more than 40 countries.",
        "Diversity, inclusive leadership, and employee well-being are not checkboxes for him. They are principles he has embedded into every team and institution he has served. Today he brings that same standard, and the added dimension of AI and technology integration, to the leaders and organisations he works with.",
    ],
    "expertise_h": "Areas of Expertise",
    "expertise": [
        ("Strategic Leadership",
         "Senior program and operations leadership in international NGOs, working alongside UN agencies and donor systems across conflict, displacement, and multi-mandate settings. Responsible for delivery, budgets, and accountability where the operating conditions are hardest."),
        ("Organisational Psychology",
         "Diagnosing why institutions underperform, then redesigning structure, roles, and culture so teams function. The work is organisational design and team rebuilding under real constraints, not theory: locating the dysfunction, naming it, and fixing how the place actually operates."),
        ("Organisational Transformation",
         "Leading structural and cultural change across multiple countries and regions, including governance redesign and cross-border operational realignment. Focused on the mechanics of change: reshaping how authority, reporting, and operations fit together so the new design holds."),
        ("AI and Technology Integration",
         "Building and deploying practical AI tools for program and operational work, and leading public AI-literacy efforts through the nonprofit foundation he founded. The proof is the tools shipped and the organisation built, not a promise of innovation."),
        ("Global Reach and Operations",
         "Direct, on-the-ground operational responsibility across the Middle East, Africa, and Asia: Syria, Iraq, Jordan, Lebanon, Turkey, Nigeria, Kenya, South Sudan, Afghanistan, and Bangladesh, with cross-border regional operations spanning more than 40 countries."),
        ("Executive Coaching",
         "Advising senior leaders one-on-one through complex decisions and organisational pressure. The work is judgment under load: helping experienced people think clearly, choose well, and hold their footing when the stakes and the noise are both high."),
        ("Program Design and Governance",
         "Designing accountability structures and performance measurement systems for programs and grants. The focus is oversight and design: building the controls, reporting lines, and metrics that let leadership see what is working and act on what is not."),
        ("Inclusive Leadership",
         "Building diverse, equitable teams and embedding staff well-being into how organisations actually run. Inclusion shows up in the practice: who gets hired, who gets heard, and how decisions and workloads are shared day to day."),
        ("Vision and Strategy",
         "Setting long-range institutional direction and converting it into funded, executable strategy. The discipline is closing the gap between intent and delivery: defining where an organisation is going and securing the resources and plan to actually get there."),
    ],
    "closing": "",
}

# His own links, taken from his own sites and each one checked: the YouTube channel resolves to
# "Ali Al Mokdad | Vision, Leadership & Global Impact" and the X account to "Ali Al Mokdad
# (@AlMokdadAli1)". Two variants of each exist across his properties; these are the live ones.
SOCIAL = [
    ("LinkedIn", "https://www.linkedin.com/in/ali-al-mokdad/"),
    ("YouTube",  "https://www.youtube.com/@AliAlMokdadInsights"),
    ("X",        "https://x.com/AlMokdadAli1"),
]
