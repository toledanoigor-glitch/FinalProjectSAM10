#!/usr/bin/env python3
"""Builds the Northbridge IT Desk project website (static HTML) into docs/ (GitHub Pages). Run: python scripts/build_site.py (needs docs/diagram.svg, style.css, site.js, img/)"""
import json
import pathlib
OUT = pathlib.Path(__file__).resolve().parent.parent / "docs"  # GitHub Pages serves main:/docs

PAGES = [
    ("index.html", "Summary"),
    ("infrastructure.html", "AWS design"),
    ("system.html", "System card"),
    ("baseline.html", "Baseline"),
    ("well-architected.html", "Well-Architected"),
    ("operations.html", "Operations"),
    ("incident.html", "Incident"),
    ("results.html", "Results"),
    ("next.html", "Next steps"),
    ("declaration.html", "Declaration"),
]

def fig(img, cap, alt=None):
    return f'<figure><img src="img/{img}" alt="{alt or cap}" loading="lazy"><figcaption>{cap}</figcaption></figure>'

def page(fname, title, body):
    nav = "".join(f'<a href="{f}"{" class=on" if f == fname else ""}>{t}</a>' for f, t in PAGES)
    i = [f for f, _ in PAGES].index(fname)
    prev = f'<a class="pv" href="{PAGES[i-1][0]}"><small>← Previous</small>{PAGES[i-1][1]}</a>' if i > 0 else '<span></span>'
    nxt = f'<a class="nx" href="{PAGES[i+1][0]}"><small>Next →</small>{PAGES[i+1][1]}</a>' if i < len(PAGES) - 1 else '<span></span>'
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · Northbridge University IT Desk (Mabi)</title>
<meta name="description" content="SAM10 final project: Mabi, an AI IT help desk built on LibreChat and run on AWS.">
<link rel="icon" href="logo.svg"><link rel="stylesheet" href="style.css?v=5"></head>
<body><div id="progress"></div>
<header><div class="bar"><a class="brand" href="index.html"><img src="logo.svg" alt=""><span>Northbridge University IT Desk<small>Mabi · SAM10 final project · Igor Toledano</small></span></a><a class="cta" href="https://d2f1g5u307k6aa.cloudfront.net">Open Mabi ↗</a></div>
<nav class="tabs"><div class="tabin">{nav}</div></nav></header>
<div class="layout"><main>{body}
<div class="pager">{prev}{nxt}</div></main>
<aside class="toc"><b>On this page</b><div class="toclist"></div><div class="tocbar"><i></i></div><a class="toctop" href="#">↑ Back to top</a></aside></div>
<footer>SAM10 Systems Administration and Maintenance · Final Project · Igor Toledano · Built on <a href="https://github.com/danny-avila/LibreChat">LibreChat</a> (MIT) · Northbridge University is fictional; all data is invented.</footer>
<button id="top" aria-label="Back to top">↑</button>
<div class="zoom" id="z"><button class="zx" aria-label="Close">✕</button><button class="zp" aria-label="Previous">‹</button><img alt=""><p></p><button class="zn" aria-label="Next">›</button></div>
<script src="site.js?v=7"></script>
</body></html>"""
    if "DIAGRAM_SVG" in html:
        svg = (OUT / "diagram.svg").read_text(encoding="utf-8")
        svg = svg[svg.index("<svg"):]
        html = html.replace("DIAGRAM_SVG", svg).replace("STEPTEXT", json.dumps(STEP_TEXT))
    (OUT / fname).write_text(html, encoding="utf-8")

STEP_TEXT = [
 "<b>The whole system.</b> Everything in the dashed box runs in one AWS account in Singapore. Only the AI model (Google Gemini) is outside AWS. Pick a step or press <b>Play</b> to follow one question.",
 "<b>1 · Browser → CloudFront (HTTPS).</b> The student opens the Mabi address. CloudFront answers with its free certificate and redirects plain HTTP to HTTPS, so passwords and chats are encrypted on the internet.",
 "<b>2 · CloudFront → EC2 on port 80.</b> CloudFront forwards the request to the server. The security group only accepts the CloudFront prefix list, so nobody can reach the server directly by its IP. No SSH port exists.",
 "<b>3 · LibreChat ↔ MongoDB.</b> The app checks the login, loads the conversation and saves the new question in MongoDB, a second container that has no port open to the network.",
 "<b>4 · LibreChat ↔ Google Gemini.</b> The question, recent messages and Mabi's instructions (rules + IT Desk documents, rebuilt from S3 at start-up with the key from Parameter Store) go to gemini-3.5-flash-lite. This is the only hop outside AWS.",
 "<b>5 · Answer back, and logged.</b> The answer streams back through CloudFront and is saved in MongoDB. Within a minute the request logger (a systemd timer) writes the question, time, outcome, model and version to CloudWatch.",
]

SITE = "https://d2f1g5u307k6aa.cloudfront.net"
REPO = "https://github.com/toledanoigor-glitch/FinalProjectSAM10"
VIDEO_ID = "OhcbW68HYYs"

# ---------------------------------------------------------------- index
page("index.html", "Summary", f"""
<div class="hero">
<h1>Mabi: the Northbridge University IT Desk assistant</h1>
<p>An AI help-desk chat for a (fictional) university, built on open-source LibreChat, running on AWS, and run like a real service: watched, backed up, locked down and able to fix itself.</p>
<div class="tags"><span>LibreChat v0.8.9 (MIT)</span><span>Google Gemini</span><span>EC2 + Docker</span><span>CloudFront HTTPS</span><span>S3 · Parameter Store</span><span>CloudWatch · SNS · Lambda</span></div>
<div class="btns"><a class="btn1" href="{SITE}">Open Mabi ↗</a><a class="btn2" href="infrastructure.html">See how it works</a><a class="btn2" href="{REPO}">Code on GitHub ↗</a></div>
</div>

<div class="video"><iframe src="https://www.youtube.com/embed/{VIDEO_ID}" title="Project presentation" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>
<p style="font-size:14px;color:var(--muted)">Recorded presentation (6 min 42 s): the reskin, the running system in AWS, the dashboard and alarms, the restore and the fault. <a href="https://youtu.be/{VIDEO_ID}">Watch on YouTube ↗</a></p>

<h2>What the system does</h2>
<p>Students and staff of Northbridge University open <a href="{SITE}">{SITE}</a>, log in and ask <b>Mabi</b> everyday IT questions: <i>"I forgot my password"</i>, <i>"How do I connect my phone to the Wi-Fi?"</i>, <i>"How much is a colour print?"</i>. Mabi answers in English, Filipino or Taglish, using only the IT Desk's own information. It refuses things it must not do: it never repeats a password, cannot reset accounts, and sends grade questions to the Registrar.</p>

<h2>What was wrong with how it was run</h2>
<p>The starting point was LibreChat as it comes out of the box, on a laptop. It only worked while the laptop was on. Anyone who could reach it could create an account. The AI key sat in a plain text file. Nothing recorded whether it was working, nobody would be told if it broke, and if the laptop died every conversation was gone. The first copy on AWS was no better: it was reachable over plain HTTP at a raw IP address, with the web port open to the whole internet.</p>

<h2>What I changed</h2>
<ul>
<li><b>Made it ours:</b> new name, logo, colours, wording and safety rules; six invented IT Desk documents kept in Amazon S3.</li>
<li><b>Put it on AWS properly:</b> one small server behind Amazon CloudFront (HTTPS), the server only accepts traffic from CloudFront, no SSH, sign-up closed, the AI key in Parameter Store.</li>
<li><b>Watched it:</b> every question logged with its time, outcome and version; a dashboard; 9 alarms that email a real inbox.</li>
<li><b>Backed it up:</b> nightly database backup to S3, and a restore test that brought the chats back in 43 seconds.</li>
<li><b>Broke it on purpose and fixed it:</b> stopped the app, timed how long the alarm took to notice, wrote a runbook, then added an auto-heal job so the same fault now fixes itself.</li>
</ul>

<h2>What improved</h2>
<div class="cards">
<div class="card"><b>13 min 29 s → 1 min 38 s</b><span>outage when the app stops (same fault, before and after auto-heal, 2026-11-17)</span></div>
<div class="card"><b>never → 10 min</b><span>time for someone to find out the site is down (no monitoring before; alarm email after)</span></div>
<div class="card"><b>none → 43 s</b><span>backups: none before; nightly to S3 now, restore tested 2026-11-17</span></div>
<div class="card"><b>10 / 10</b><span>test questions correct on the live system, 18 Nov (first run on the laptop: 9 / 10, one honest failure)</span></div>
</div>
<p>The trade-off I chose: <b>reliability and operations over cost of redundancy.</b> Everything runs on one t3.small in one zone to stay on the AWS Free plan, so a whole-server failure would still take Mabi down. I accepted that and made recovery fast and tested instead. See the <a href="well-architected.html">Well-Architected review</a>.</p>

<h2>Explore the project</h2>
<div class="tiles">
<a class="tile" href="infrastructure.html"><i>🗺️</i><b>AWS design</b><span>Interactive diagram: follow one question from the browser to the model and back.</span></a>
<a class="tile" href="system.html"><i>🪪</i><b>System card</b><span>Before/after slider, what changed, the data, limits and who must not use it.</span></a>
<a class="tile" href="baseline.html"><i>📍</i><b>Baseline</b><span>How it was run before: a laptop, open sign-up, no monitoring, no backups.</span></a>
<a class="tile" href="well-architected.html"><i>🏛️</i><b>Well-Architected</b><span>Six pillars, honest verdicts, and the first gap to fix.</span></a>
<a class="tile" href="operations.html"><i>📈</i><b>Operations: monitoring, backup, security</b><span>Dashboard, 9 alarms, a real alert, the 43-second restore, every control explained.</span></a>
<a class="tile" href="incident.html"><i>🚨</i><b>Incident &amp; automation</b><span>Four automations, the outage timeline, root cause, auto-heal and the runbook.</span></a>
<a class="tile" href="results.html"><i>📊</i><b>Results</b><span>Test questions (19/20), before vs after, a day of metrics, and cost.</span></a>
<a class="tile" href="next.html"><i>🧭</i><b>Next steps</b><span>Five improvements in priority order.</span></a>
</div>

<h2>Quick links</h2>
<table>
<tr><th>Live system</th><td><a href="{SITE}">{SITE}</a> (sign-up is closed; demo login on request)</td></tr>
<tr><th>Repository</th><td><a href="{REPO}">{REPO}</a></td></tr>
<tr><th>Base system</th><td><a href="https://github.com/danny-avila/LibreChat">LibreChat</a> v0.8.9-rc1 by Danny Avila and contributors, MIT licence</td></tr>
<tr><th>Author</th><td>Igor Toledano (individual project)</td></tr>
</table>
""")

# ---------------------------------------------------------------- infrastructure
page("infrastructure.html", "AWS design", f"""
<h1>AWS infrastructure design</h1>
<p class="lead">Where every part of Mabi runs, and how one question travels from a student to the model and back.</p>
<div class="diagram">DIAGRAM_SVG</div>
<div class="steps"><button class="play">▶ Play the question</button><button data-step="0" class="on">Whole system</button><button data-step="1">1 Browser → CloudFront</button><button data-step="2">2 CloudFront → EC2</button><button data-step="3">3 App ↔ database</button><button data-step="4">4 App ↔ Gemini</button><button data-step="5">5 Answer back + logged</button></div>
<div class="stepinfo"></div>
<script type="application/json" id="steptext">STEPTEXT</script>
<p style="font-size:14px;color:var(--muted)">Mabi in AWS, ap-southeast-1 (Singapore). Solid lines are the path of a question; dashed lines are operations. Click a step or press Play. <a href="img/diagram.png">PNG version</a>.</p>

<h2>How a question travels</h2>
<ol>
<li><b>Browser → CloudFront (HTTPS).</b> The student opens <code>{SITE}</code>. CloudFront ends the TLS connection with its free certificate and redirects any plain-HTTP request to HTTPS. Caching is off, because every answer is personal.</li>
<li><b>CloudFront → EC2, port 80.</b> CloudFront forwards the request to the server. The server's security group accepts port 80 <i>only</i> from the AWS-managed CloudFront prefix list (<code>pl-31a34658</code>), so the server cannot be reached directly.</li>
<li><b>LibreChat ↔ MongoDB.</b> The LibreChat container checks the login, loads the conversation and saves the new question in MongoDB (a second container on the same server, not exposed to the network).</li>
<li><b>LibreChat ↔ Google Gemini API.</b> LibreChat sends the question, the recent conversation and Mabi's instructions (rules + the IT Desk documents built from S3 at start-up) to <code>gemini-3.5-flash-lite</code>. This is the only part outside AWS.</li>
<li><b>The answer comes back</b> the same way, streamed word by word, and is saved in MongoDB. Within a minute the request logger records the question, duration, outcome, model and version in CloudWatch.</li>
</ol>

<h2>Every service and what it is for</h2>
<table>
<tr><th>Layer</th><th>Service</th><th>What it does for Mabi</th></tr>
<tr><td>Edge / network</td><td>Amazon CloudFront</td><td>HTTPS front door with a free certificate; hides the server; the only allowed way in</td></tr>
<tr><td>Network</td><td>VPC default, security group</td><td>Port 80 from CloudFront only; no SSH, no database port</td></tr>
<tr><td>Compute</td><td>EC2 t3.small, Ubuntu 24.04, 2 GB swap</td><td>Runs Docker with the LibreChat (Mabi) and MongoDB containers</td></tr>
<tr><td>Database</td><td>MongoDB 8.0 in Docker, on the EC2 EBS disk</td><td>Users, conversations, messages</td></tr>
<tr><td>Storage</td><td>Amazon S3 (versioning on)</td><td><code>content/</code>: the IT Desk documents Mabi answers from (the AWS integration). <code>backups/mongodb/</code>: nightly database backups, deleted after 14 days</td></tr>
<tr><td>Secrets</td><td>SSM Parameter Store (SecureString)</td><td>The Gemini API key; read at start-up, never in git</td></tr>
<tr><td>Admin access</td><td>SSM Session Manager</td><td>Browser shell on the server without SSH keys or an open port; every session is logged by CloudTrail</td></tr>
<tr><td>Monitoring</td><td>CloudWatch Logs, Metrics, Alarms, Dashboard</td><td>App and database logs (awslogs driver), request log, custom metrics <code>NBU/Mabi</code>, 9 alarms, dashboard <code>Mabi-Operations</code></td></tr>
<tr><td>Alerting</td><td>Amazon SNS</td><td>Emails ALARM and OK messages to the admin</td></tr>
<tr><td>Health check</td><td>AWS Lambda + EventBridge</td><td>Visits <code>/health</code> through CloudFront every 5 minutes, like a real user would</td></tr>
<tr><td>Identity</td><td>IAM user + role, MFA; EC2 instance role</td><td>Humans switch into <code>NBU-Admin</code>; the server uses <code>NBU-EC2-Role</code> to read S3 and the key and to write logs</td></tr>
<tr><td>Audit / cost</td><td>CloudTrail, AWS Budgets</td><td>Records every API call in all regions; emails if spend goes above $0.01 of a $1 budget</td></tr>
<tr><td>Model</td><td>Google Gemini API (outside AWS)</td><td>The language model; free tier on a personal account; invented data only</td></tr>
</table>
<div class="grid2">
{fig("ec2-running.png","EC2 instance nbu-itdesk-server: running, t3.small, 3/3 status checks passed.")}
{fig("cloudfront-config.png","CloudFront distribution: HTTP redirected to HTTPS, CachingDisabled, AllViewer origin request policy.")}
</div>
""")

# ---------------------------------------------------------------- system card
page("system.html", "System card", f"""
<h1>Your system: the reskin and the system card</h1>
<p class="lead">Drag the slider: stock LibreChat on the left, Mabi on the right.</p>
<div class="compare"><img src="img/mabi-reskin-local.png" alt="Mabi after the reskin"><div class="before"><img src="img/original-librechat.png" alt="Original LibreChat"></div><span class="lab l1">BEFORE · LibreChat</span><span class="lab l2">AFTER · Mabi</span><span class="knob">⇔</span><input type="range" min="0" max="100" value="50" aria-label="Compare before and after"></div>
<div class="grid2">
{fig("original-librechat.png","BEFORE (E-05): stock LibreChat on the laptop. Generic name, grey theme, any model, any question (2026-11-16).")}
{fig("mabi-reskin-local.png","AFTER (E-01): Mabi. Northbridge name and logo, navy/teal theme, one fixed assistant, IT Desk answers (2026-11-16).")}
</div>
{fig("mabi-https.png","The deployed system at its HTTPS address on AWS (E-02): " + SITE)}

<h2>SYSTEM CARD: Mabi, Northbridge University IT Desk assistant</h2>

<h3>1. What it does</h3>
<p>Mabi is a chat assistant that answers everyday IT questions for students and staff of Northbridge University (a fictional university): passwords, MFA, Wi-Fi, email, NBU Drive, software, printing and the computer labs. It answers only from the IT Desk's own documents, and tells people where to go when it cannot help.</p>

<h3>2. Who uses it, and who must not</h3>
<ul>
<li><b>Intended users:</b> NBU students and staff with a self-service IT question; IT Desk staff checking what the standard answer is.</li>
<li><b>Explicitly NOT for:</b> resetting passwords or unlocking accounts; anything about grades, enrolment, fees, scholarships or discipline; any decision about an identifiable person; security incidents in progress (call the IT Desk); anyone who needs a guaranteed-correct answer without checking.</li>
</ul>

<h3>3. Base system</h3>
<table>
<tr><th>Name and version</th><td>LibreChat v0.8.9-rc1 (dev image <code>registry.librechat.ai/librechat-ai/librechat-dev</code>, first run 2026-11-16)</td></tr>
<tr><th>Source URL</th><td><a href="https://github.com/danny-avila/LibreChat">https://github.com/danny-avila/LibreChat</a></td></tr>
<tr><th>Author</th><td>Danny Avila and the LibreChat contributors</td></tr>
<tr><th>Licence</th><td>MIT: <a href="https://github.com/danny-avila/LibreChat/blob/main/LICENSE">LICENSE</a> (copyright notice kept; we may modify and rename)</td></tr>
<tr><th>What it did originally</th><td>A general ChatGPT-style web app: anyone can sign up, pick from many AI providers and models, and chat about anything.</td></tr>
</table>

<h3>4. What I changed (the reskin)</h3>
<table>
<tr><th>Part</th><th>Original</th><th>Mine</th><th>Why</th></tr>
<tr><td>Name / branding</td><td>"LibreChat", LibreChat logo, grey/green</td><td>"Northbridge University IT Desk", assistant "Mabi", bridge-and-star logo, navy/teal/gold theme, own favicon and footer</td><td>A stranger should not recognise the original; it should look like a university service</td></tr>
<tr><td>Data / content</td><td>None</td><td>Six invented IT Desk documents (about, accounts &amp; passwords, Wi-Fi &amp; network, email &amp; software, printing &amp; labs, policies &amp; FAQ)</td><td>Answers must come from the IT Desk, not from the model's general knowledge</td></tr>
<tr><td>Wording / prompts</td><td>General assistant, no rules</td><td>Mabi's 9 rules: use only the documents; never repeat a password; cannot reset accounts; no grades/fees; ask for no personal details; numbered steps; reply in English/Filipino/Taglish; greeting "Hi, I'm Mabi from the Northbridge University IT Desk…"</td><td>Domain language, and safety for an IT help desk</td></tr>
<tr><td>Interface</td><td>Model picker, all endpoints, open sign-up</td><td>One fixed assistant (model specs enforced), Google endpoint only, sign-up closed on AWS, social login and password reset off, conversation titles off (saves model quota)</td><td>Fewer choices, smaller attack surface, predictable behaviour</td></tr>
<tr><td>AWS services</td><td>None (runs anywhere)</td><td>Content in S3, rebuilt into the config at every start; key in Parameter Store; logs and metrics in CloudWatch; backups to S3; SNS alerts</td><td>Required AWS integration beyond hosting; content can be updated without touching the server image</td></tr>
</table>

<h3>5. Data</h3>
<ul>
<li><b>Where it came from:</b> written for this project (with AI help, see the <a href="declaration.html">declaration</a>), stored in <code>content/*.md</code> in the repository and in <code>s3://nbu-itdesk-content-842624819932/content/</code>. No licence issues; it is our own work.</li>
<li><b>Size and format:</b> 6 Markdown files, about 15 KB in total.</li>
<li><b>Anything personal in it:</b> <b>No. All invented.</b> Northbridge University, its rooms, prices, addresses and domains (<code>*.northbridge.example</code>) do not exist.</li>
<li><b>Sent to a third-party AI service:</b> Yes. Every question, the recent conversation and the IT Desk documents are sent to Google's Gemini API (free tier, which Google may use to improve its products). Everything sent is invented. Test users must not type real personal data.</li>
</ul>

<h3>6. How good it is</h3>
<ul>
<li><b>The one number:</b> <b>10 out of 10</b> test questions correct on the live AWS system (2026-11-18, <code>gemini-3.5-flash-lite</code>). The first run, on the laptop with <code>gemini-3.5-flash</code> (2026-11-17), scored <b>9 out of 10</b>. Together: 19 of 20.</li>
<li><b>How measured:</b> the same 10 hand-written questions, each in a new chat, answers compared by hand with the content documents; a pass needs every fact right and no rule broken. Full table on the <a href="results.html">Results</a> page. Ten questions is a small sample, so one question is worth 10 points.</li>
<li><b>What they covered:</b> simple facts, how-to steps, troubleshooting, prices, a Filipino question, and three limit tests (a typed password, a grade change, a question the documents do not answer).</li>
<li><b>An example it gets wrong:</b> <i>"Does NBU give students a free laptop?"</i> In the first run the documents' silence became a confident "No", and it implied CAD software is free for everyone (it is only for Engineering and Architecture). In the second run, with the newer model, it correctly said it does not know and pointed to ServiceHub. The risk has not gone away: with a different question or model it can still turn missing information into a confident answer.</li>
</ul>

<h3>7. How it is served</h3>
<ul>
<li><b>Where it runs:</b> Amazon EC2 t3.small (Ubuntu 24.04), Docker, region ap-southeast-1 (Singapore), behind Amazon CloudFront.</li>
<li><b>What calls it:</b> web browsers at <a href="{SITE}">{SITE}</a>; LibreChat's API under <code>/api/</code>; health check at <code>/health</code>.</li>
<li><b>The model:</b> Google <code>gemini-3.5-flash-lite</code> via the Gemini API, <b>free tier</b>, personal account. (Switched from <code>gemini-3.5-flash</code>, which returned 429/503 errors on the free tier.)</li>
<li><b>If the model is unavailable:</b> the user sees a red error in the chat (for example HTTP 429 "rate limit"). Nothing is lost; they can retry. Failed and empty answers are counted, and the alarms <code>nbu-answers-failed</code> and <code>nbu-empty-answer</code> email the admin.</li>
</ul>
{fig("error-429.png","A real model failure: Gemini's free tier answered HTTP 429 (rate limit) during testing, shown to the user as a red error.")}

<h3>8. Limitations and risks</h3>
<ul>
<li><b>What it cannot do:</b> see or change any account, ticket or setting; know anything not in the six documents; know about events after the documents were written.</li>
<li><b>What could go wrong with the data:</b> users may type secrets or personal data anyway. Mabi will not repeat a password, but the text is still stored in MongoDB, sent to Google, and copied into the CloudWatch request log for 30 days. Answers can be confidently wrong when the documents are silent (see Q10).</li>
<li><b>How it could be misused:</b> to use up the free model quota (anyone with an account can send many questions); to try to make it ignore its rules (prompt injection). Sign-up is closed to limit both.</li>
<li><b>What a user must always check themselves:</b> links, prices and opening hours before acting on them; anything to do with their password must be done only on the official password site, never in the chat.</li>
</ul>

<h3>9. Operational summary</h3>
<ul>
<li><b>Where the code lives:</b> <a href="{REPO}">{REPO}</a> (branding, content, config builder, deployment and ops scripts).</li>
<li><b>How often it is backed up:</b> database every night at 02:00 Manila to S3 (kept 14 days); content versioned in S3 and in git; key in Parameter Store.</li>
<li><b>How we know it is healthy:</b> 9 CloudWatch alarms (site down, server status, CPU, memory, disk, failed answers, empty answers, slow answers, backup missing) emailing the admin; dashboard <code>Mabi-Operations</code>; auto-heal restarts the app if <code>/health</code> fails twice.</li>
<li><b>Who to contact:</b> Igor Toledano (operator). Test question for a quick check: <i>"What time is the IT Desk open on Saturday?"</i> → 8:00 AM to 12:00 NN.</li>
</ul>
""")

# ---------------------------------------------------------------- baseline
page("baseline.html", "Baseline", f"""
<h1>Baseline: the environment before I touched it</h1>
<p class="lead">What "running LibreChat" looked like at the start, so the improvements have something honest to be measured against.</p>

<h2>Stage 0: stock LibreChat on a laptop (2026-11-16)</h2>
{fig("original-librechat.png","Stock LibreChat on http://localhost:3080, any model, any topic.")}
<table>
<tr><th>Area</th><th>Baseline</th></tr>
<tr><td>Availability</td><td>Only while the laptop was on and Docker Desktop running; only reachable from that laptop</td></tr>
<tr><td>Access</td><td>Anyone who reached it could <b>create an account</b>; email login, no MFA</td></tr>
<tr><td>Secrets</td><td>Gemini API key in plain text in <code>.env</code>, next to the code</td></tr>
<tr><td>Transport</td><td>Plain HTTP</td></tr>
<tr><td>Monitoring</td><td>None. No request log, no metrics, no alarms. A failure was found only by trying it</td></tr>
<tr><td>Logs</td><td>Container logs on the laptop only, no retention policy</td></tr>
<tr><td>Backups</td><td>None. Conversations lived only in a Docker folder on one laptop disk</td></tr>
<tr><td>Data and wording</td><td>No content of its own; a general assistant with no rules</td></tr>
<tr><td>Cost</td><td>$0 (own laptop, free model tier)</td></tr>
</table>

<h2>Stage 1: first copy on AWS (2026-11-17, before hardening)</h2>
<p>The first deployment worked, but it copied the laptop's habits onto the internet:</p>
<div class="grid2">
{fig("mabi-on-aws.png","First AWS version: <b>&quot;Not secure&quot;</b>, plain HTTP to the raw public IP of the server.")}
{fig("sg-before-open-to-internet.png","Security group before: port 80 open to <code>0.0.0.0/0</code>, the whole internet.")}
</div>
<ul>
<li>HTTP only, at a raw IP address. Passwords crossed the internet unencrypted.</li>
<li>Web port open to every address on the internet, so CloudFront could be bypassed.</li>
<li>Sign-up still open: anyone finding the IP could make an account and spend the model quota.</li>
<li>Still no monitoring, alarms, backups or request log.</li>
</ul>
<p>The <a href="operations.html">Monitoring, backup and security</a> page shows what replaced each of these, and the <a href="results.html">Results</a> page puts the numbers side by side.</p>
""")

# ---------------------------------------------------------------- well-architected
page("well-architected.html", "Well-Architected", """
<h1>Well-Architected review</h1>
<p class="lead">The six pillars of the AWS Well-Architected Framework, applied to Mabi as it runs now (after the incident fix, 2026-11-17). For each: what the framework asks, what Mabi does, and a verdict.</p>
<div class="pillars">
<a class="pillar good" href="#p-ops"><b>Operational excellence</b><span>Good</span><small>All in git, runbook, request log, learned from the incident</small></a>
<a class="pillar adequate" href="#p-sec"><b>Security</b><span>Adequate</span><small>MFA, roles, no SSH, CloudFront-only; no WAF yet</small></a>
<a class="pillar adequate" href="#p-rel"><b>Reliability</b><span>Adequate</span><small>Alarms, auto-heal, tested restore; one server, one AZ</small></a>
<a class="pillar adequate" href="#p-perf"><b>Performance</b><span>Adequate</span><small>1.4 s average answer; model rate limit is the bottleneck</small></a>
<a class="pillar good" href="#p-cost"><b>Cost optimization</b><span>Good</span><small>$0 billed, $1 budget, free-tier limits respected</small></a>
<a class="pillar adequate" href="#p-sus"><b>Sustainability</b><span>Adequate</span><small>One small instance, but on 24/7</small></a>
</div>

<h2 id="p-ops">Operational excellence <span class="good">Good</span></h2>
<p><b>Asks for:</b> operations as code, small reversible changes, observability, learning from failure.</p>
<p><b>Mabi does:</b> everything is in git (branding, content, config builder, compose file, start script, ops scripts, systemd timers, the CloudShell script that creates all monitoring). One script (<code>start-mabi.sh</code>) rebuilds the config from S3 and restarts the stack. Every request is logged with outcome, duration and version. A tested runbook exists, and the one incident led to a real change (auto-heal).</p>
<p><b>Weak spot:</b> deployment is still a manual <code>git pull</code> in Session Manager; no CI/CD.</p>

<h2 id="p-sec">Security <span class="adequate">Adequate</span></h2>
<p><b>Asks for:</b> strong identity, least privilege, traceability, protection at every layer, data protection in transit and at rest.</p>
<p><b>Mabi does:</b> root has MFA and is not used; daily work is an IAM user with MFA that switches into an admin role; the server has its own narrow role; the API key is a SecureString; CloudTrail logs all regions; no SSH; the server only accepts CloudFront; HTTPS for users; sign-up closed.</p>
<p><b>Gaps:</b> no AWS WAF, so the login page and model quota have no rate limit; CloudFront to server is plain HTTP inside AWS; MongoDB has no password (it is reachable only from the Docker network); EBS encryption not confirmed.</p>

<h2 id="p-rel">Reliability <span class="adequate">Adequate</span></h2>
<p><b>Asks for:</b> automatic recovery, tested recovery, scaling, knowing when something fails.</p>
<p><b>Mabi does:</b> 9 alarms to email; external health check every 5 minutes; auto-heal every minute; Docker <code>restart: always</code>; nightly backups to S3 with a 14-day lifecycle; restore tested (RTO 43 s); faults written up.</p>
<p><b>Gaps:</b> a single instance in a single Availability Zone is a single point of failure; RPO is 24 hours; rebuilding a whole lost server is written down but not rehearsed; the free model tier rate-limits (HTTP 429) under steady use.</p>

<h2 id="p-perf">Performance efficiency <span class="adequate">Adequate</span></h2>
<p><b>Asks for:</b> right-sized resources, measuring performance, using managed services where they help.</p>
<p><b>Mabi does:</b> t3.small (2 vCPU, 2 GiB) with 2 GB swap. On 2026-11-17 memory was about 52% and disk about 56% used, with CPU low. Logged answers took 1.1 to 7.7 seconds on day 1 and averaged 1.37 s over the 10 re-test questions. CloudFront serves the static files from the edge. An alarm fires if average answer time exceeds 20 s.</p>
<p><b>Gap:</b> the bottleneck is the external model's free-tier rate limit, not AWS; there is no load test, so the safe number of users is unknown.</p>

<h2 id="p-cost">Cost optimization <span class="good">Good</span></h2>
<p><b>Asks for:</b> pay only for what you use, measure spend, set guardrails.</p>
<p><b>Mabi does:</b> AWS Free plan; one small instance; a $1 monthly budget that emails above $0.01; CloudWatch kept inside its free allowance on purpose (10 custom metrics, 9 alarms, 1 dashboard); log retention 14–30 days instead of "never expire"; S3 backups expire after 14 days; the model is free.</p>
<p><b>Gap:</b> resources are not consistently tagged for cost allocation, and the server runs at night when nobody uses it.</p>

<h2 id="p-sus">Sustainability <span class="adequate">Adequate</span></h2>
<p><b>Asks for:</b> the smallest footprint that meets the need.</p>
<p><b>Mabi does:</b> one small burstable instance, no idle extras, old backups and logs deleted automatically, caching static files at the edge.</p>
<p><b>Gap:</b> it runs 24/7; a schedule that stops it overnight would cut its energy use by about a third.</p>

<h2>Trade-off and the gap I would fix first</h2>
<p><b>Optimised for:</b> operational excellence and reliability-through-recovery (watch it, back it up, fix fast). <b>Deliberately accepted as weaker:</b> reliability-through-redundancy, because a second server or a managed database would leave the Free plan for a help desk with a handful of test users.</p>
<p><b>Gap ranked first: no AWS WAF in front of CloudFront (Security).</b> The login page and the chat API are open to the whole internet with no rate limit. One script could guess passwords or burn the free Gemini quota, which would take Mabi down for everyone (we already saw 429 errors with one human tester). A WAF web ACL with the AWS managed common rules and a rate-based rule on <code>/api/auth/login</code> and <code>/api/ask</code> is a few clicks on the existing distribution, costs a few dollars a month, and protects security <i>and</i> availability at once. That beats the alternatives on value: Multi-AZ would cost far more, and the other security gaps (internal HTTP, Mongo without password) can only be reached by someone already inside the server.</p>
""")

# ---------------------------------------------------------------- operations
alarms = [
 ("nbu-site-down","HealthCheckOK &lt; 1, 2 of 2 × 5 min; missing data = breaching","Users cannot reach Mabi; the most important alarm"),
 ("nbu-status-check-failed","EC2 StatusCheckFailed &gt; 0, 2 × 1 min","The server itself is broken (hardware/OS); reboot needed"),
 ("nbu-cpu-high","CPUUtilization &gt; 85%, 2 × 5 min","t3 credits run out under sustained load; answers slow down"),
 ("nbu-memory-high","MemoryUsedPercent &gt; 90%, 5 min","Node + MongoDB on 2 GiB; above 90% the kernel may kill one"),
 ("nbu-disk-high","DiskUsedPercent &gt; 85%, 5 min","A full disk stops MongoDB writing; leaves time to clean up"),
 ("nbu-answers-failed","AnswersFailed ≥ 3 in 15 min","The model is failing (429/503, bad key), not just one blip"),
 ("nbu-empty-answer","EmptyAnswers &gt; 0 in 30 min","An empty reply means something broke silently"),
 ("nbu-slow-answers","ResponseTimeMs average &gt; 20,000 over 10 min","Normal answers take 1–8 s; 20 s means users give up"),
 ("nbu-backup-missing","BackupSuccess &lt; 1 in 1 day; missing = breaching","The nightly backup did not run or failed"),
]
alarm_rows = "".join(f"<tr><td><code>{a}</code></td><td>{b}</td><td>{c}</td></tr>" for a,b,c in alarms)

page("operations.html", "Monitoring, backup, security", f"""
<h1>Monitoring, backup and restore, and security</h1>

<h2>Monitoring</h2>
<p>Three sources feed one CloudWatch dashboard, <code>Mabi-Operations</code>: EC2's own metrics (CPU, status), the container logs (shipped by Docker's <code>awslogs</code> driver), and my own metrics in the namespace <code>NBU/Mabi</code>. A small job (<code>request_metrics.py</code>, every minute) reads new answers from MongoDB and publishes requests, successes, failures, empty answers, response time, disk and memory use. A Lambda function checks the public site every 5 minutes.</p>
{fig("dashboard.png","Dashboard Mabi-Operations with real data, 2026-11-17 (E-06): requests, answers OK/failed, response time, CPU, disk, memory, health check, backups, alarm status.")}

<h3>Every request is logged</h3>
<p>Each question is written as one JSON line to the log group <code>/nbu/mabi/requests</code>: the question, when it was asked, how long the answer took, whether it succeeded, the model and the exact version (<code>librechat-v0.8.9-rc1+nbu-&lt;git commit&gt;</code>).</p>
{fig("request-log.png","Request log sample (E-09): three questions, all ok, 1.1 to 7.7 seconds, model gemini-3.5-flash-lite, version librechat-v0.8.9-rc1+nbu-4b2eea4.")}
<table>
<tr><th>Log group</th><th>What</th><th>Retention</th></tr>
<tr><td><code>/nbu/mabi/app</code></td><td>LibreChat container output</td><td>14 days</td></tr>
<tr><td><code>/nbu/mabi/database</code></td><td>MongoDB container output</td><td>14 days</td></tr>
<tr><td><code>/nbu/mabi/requests</code></td><td>One line per question (above)</td><td>30 days</td></tr>
<tr><td><code>/nbu/ops/backups</code></td><td>One line per backup</td><td>30 days</td></tr>
<tr><td><code>/aws/lambda/nbu-healthcheck</code></td><td>Health check runs</td><td>14 days</td></tr>
</table>

<h3>Nine alarms, all emailing a real inbox</h3>
<table><tr><th>Alarm</th><th>Fires when</th><th>Why this threshold</th></tr>{alarm_rows}</table>
<p>Every alarm sends both ALARM and OK to the SNS topic <code>nbu-alerts</code>, so the admin also learns when a problem has cleared.</p>
<div class="grid2">
{fig("alarms.png","All 9 alarms, actions enabled, with their conditions (E-07).")}
{fig("fault-alarm-email.png","A real alert received (E-08): ALARM nbu-site-down, Tuesday 17 November 2026 09:39:26 UTC, during incident 001.")}
</div>
{fig("monitoring-created.png","All log groups, the SNS topic, the Lambda and the alarms were created by one script from the repository (create-aws-monitoring.sh), run in CloudShell. Email address blacked out.")}

<h2>Backup and restore</h2>
<h3>What would be lost, and how each part is protected</h3>
<table>
<tr><th>What</th><th>Where it lives</th><th>Protection</th><th>Restored by</th></tr>
<tr><td>Chats, users, settings (MongoDB)</td><td>EC2 disk</td><td><code>mongodump</code> every night 02:00 Manila → S3 <code>backups/mongodb/</code> (3 copies kept on the server, 14 days in S3)</td><td><code>restore-mongo.sh</code></td></tr>
<tr><td>IT Desk knowledge</td><td>S3 <code>content/</code> + git</td><td>S3 versioning; copy in git</td><td>Re-upload, or an older S3 version</td></tr>
<tr><td>Config and scripts</td><td>git (GitHub)</td><td>Full history; the live config is regenerated from S3 at every start</td><td><code>git clone</code> + <code>start-mabi.sh</code></td></tr>
<tr><td>Gemini API key</td><td>Parameter Store</td><td>Managed by AWS, never on the laptop or in git</td><td>Read again at start</td></tr>
<tr><td>Session secrets</td><td>Server, <code>secrets.env</code> (mode 600)</td><td>Not backed up on purpose: if lost, new ones are made and users just log in again</td><td><code>start-mabi.sh</code></td></tr>
<tr><td>Uploaded files</td><td>Server <code>uploads/</code></td><td><b>Not backed up</b>: Mabi does not use file uploads (known gap)</td><td>n/a</td></tr>
</table>
<div class="grid2">
{fig("timers-installed.png","Backup settings (E-10): the backup and request-logger timers installed; first backup ok, 25,150 bytes.")}
{fig("backup-manual.png","A backup run: mongodump → S3, status ok, 27,192 bytes in 1.0 s (09:18:18 UTC).")}
</div>
{fig("backup-nightly.png","The backup log: install run, manual run, and the first scheduled night run at 18:00:08 UTC (02:00 Manila), all ok.")}

<h3>Restore test, 2026-11-17 (E-11)</h3>
<p>To prove the backup is real, I took a backup at 09:18, then asked Mabi a <b>new</b> question (the Wi-Fi question) so the live database had one chat the backup did not. Then I ran <code>restore-mongo.sh</code>: it downloads the newest backup from S3, counts records, stops the stack, moves the live database aside (not deleted), restores into an empty MongoDB, counts again and restarts Mabi.</p>
<table>
<tr><th></th><th>Users</th><th>Conversations</th><th>Messages</th></tr>
<tr><td>Before restore (live)</td><td>1</td><td>7</td><td>18</td></tr>
<tr><td>After restore (09:18 backup)</td><td>1</td><td>6</td><td>16</td></tr>
</table>
<p>93 documents restored, 0 failed; the site answered <code>HTTP/1.1 200 OK</code>; <b>restore finished in 43 seconds</b>. In the browser the old chats were back and the Wi-Fi chat was gone, which is exactly the one conversation (2 messages) created after the backup.</p>
<div class="grid2">
{fig("restore-counts-before.png","Restore step 1–4: backup downloaded from S3, counts before (7 conversations, 18 messages), live data moved aside.")}
{fig("restore-output.png","Restore step 5–6: 93 documents restored, counts after (6 / 16), Mabi started, 200 OK, finished in 43 seconds.")}
</div>
{fig("restore-chats-back.png","Check that the data came back: logged in after the restore, six chats present, an old chat opens with its answer.")}
<table>
<tr><th></th><th>Target</th><th>Measured</th></tr>
<tr><td><b>RPO</b> (data we can lose)</td><td>24 hours: one backup a night is enough for an FAQ chat; nobody's work depends on chat history</td><td>Lost exactly the chats made after the last backup (1 conversation)</td></tr>
<tr><td><b>RTO</b> (time to get it back)</td><td>15 minutes</td><td><b>43 seconds</b> for the database, plus logging in</td></tr>
</table>
<p>Not yet rehearsed: rebuilding a completely lost server (new EC2 → clone repo → <code>setup-server.sh</code> → <code>start-mabi.sh</code> → restore), estimated 20–30 minutes. Full procedure: <a href="{REPO}/blob/main/docs/backup-restore.md">docs/backup-restore.md</a>.</p>

<h2>Security</h2>
<h3>Each control in one sentence</h3>
<table>
<tr><th>Control</th><th>What it does</th></tr>
<tr><td>MFA on root, root not used</td><td>The account owner login needs a phone code and is kept for emergencies, so a stolen password alone cannot take the account.</td></tr>
<tr><td>IAM user <code>igor</code> + MFA → role <code>NBU-Admin</code></td><td>Daily work uses a personal read-only login that must deliberately switch into the admin role, so there is no shared admin login and every admin action is attributable.</td></tr>
<tr><td>Instance role <code>NBU-EC2-Role</code></td><td>The server gets short-lived credentials for only what it needs (S3 bucket, one parameter, logs, Session Manager), so no access keys are stored on it.</td></tr>
<tr><td>Parameter Store SecureString</td><td>The Gemini key is encrypted in AWS and read at start-up, so it is not in the code, the image, git history or a screenshot.</td></tr>
<tr><td>Security group: CloudFront prefix list only</td><td>The server refuses any connection that does not come through CloudFront, so it cannot be attacked directly by IP.</td></tr>
<tr><td>HTTPS via CloudFront</td><td>Passwords and chats are encrypted between the user and AWS, and plain HTTP is redirected.</td></tr>
<tr><td>No SSH; Session Manager</td><td>There is no port 22 and no key file to lose; admin shells go through IAM and are logged.</td></tr>
<tr><td>Database not exposed</td><td>MongoDB has no published port, so it is reachable only by the app container on the same Docker network.</td></tr>
<tr><td>Sign-up closed, social login and password reset off</td><td>Only accounts the admin creates exist, which protects the free model quota and limits who can reach the chat.</td></tr>
<tr><td>CloudTrail <code>nbu-trail</code> (all regions)</td><td>Every API call in the account is recorded, so changes can be traced to a person and a time.</td></tr>
<tr><td><code>.gitignore</code> + <code>.env</code> mode 600</td><td>Secrets files never enter git and only root can read them on the server.</td></tr>
<tr><td>Budget alert</td><td>An email arrives if anything starts costing money, which also catches a hijacked account.</td></tr>
</table>
<div class="grid2">
{fig("mfa.png","MFA on the root user (E-12).")}
{fig("iam-user-igor.png","IAM user igor: console access enabled with MFA; only ReadOnlyAccess, change-own-password and permission to switch to the admin role (E-12).")}
{fig("parameter-store.png","The Gemini key as a SecureString in Parameter Store; its value is never shown (E-13).")}
{fig("ec2-role.png","The server's own role: Session Manager, CloudWatch agent and one inline policy for its bucket and parameter.")}
{fig("sg-after-cloudfront-only.png","Security group after: port 80 only from the CloudFront prefix list pl-31a34658.")}
{fig("cloudtrail-logging.png","CloudTrail nbu-trail: multi-region, logging.")}
</div>

<h3>Security problems found and fixed: before and after</h3>
<table>
<tr><th>Problem found</th><th>Before</th><th>After</th></tr>
<tr><td>Plain HTTP</td><td>http://18.138.237.86 "Not secure"</td><td>HTTPS at CloudFront, HTTP redirected</td></tr>
<tr><td>Server open to the internet</td><td>Port 80 from 0.0.0.0/0</td><td>Port 80 from CloudFront prefix list only</td></tr>
<tr><td>Anyone could register</td><td>Sign-up open</td><td>Sign-up closed (<code>ALLOW_REGISTRATION=false</code>)</td></tr>
<tr><td>Key in a text file</td><td>Laptop <code>.env</code></td><td>Parameter Store SecureString, read at start</td></tr>
<tr><td>Admin logins</td><td>Root account for everything</td><td>Root with MFA, unused; personal user + MFA + role</td></tr>
<tr><td>Remote access</td><td>SSH would need port 22 and a key file</td><td>No SSH; Session Manager</td></tr>
<tr><td>No audit trail</td><td>Nothing recorded</td><td>CloudTrail in all regions</td></tr>
</table>
{fig("login-signup-closed.png","The login page on AWS: no sign-up link, no social login.")}

<h3>Personal data check</h3>
<ul>
<li>Content: all invented (fictional university, <code>.example</code> domains). No real names, IDs, phone numbers or addresses.</li>
<li>Users: only test accounts created by me. The password in test question 8 ("Summer2026!") is invented for the test.</li>
<li>Screenshots on this site: checked for keys, tokens and passwords; my personal email was blacked out in three of them.</li>
<li>Git history: no <code>.env</code>, key or password has ever been committed (<code>.gitignore</code> from the first commit).</li>
<li><b>Finding (2026-11-18):</b> my own request log copies each question into CloudWatch, so when a user types a password (test Q8, "Summer2026!", invented) it is kept in <code>/nbu/mabi/requests</code> for 30 days. Mabi refuses to repeat it, but the operations tooling still stores it. Fix planned: mask anything that looks like a password or code before logging (see <a href="next.html">next steps</a>).</li>
<li>Sent outside AWS: only invented questions and content, to Google Gemini.</li>
</ul>
""")

# ---------------------------------------------------------------- incident
page("incident.html", "Automation & incident", f"""
<h1>Automation, and the incident</h1>

<h2>Automations that run on their own</h2>
<table>
<tr><th>Automation</th><th>Runs</th><th>What it does</th><th>Code</th></tr>
<tr><td><b>Health check</b> (Lambda <code>nbu-healthcheck</code>)</td><td>Every 5 min, EventBridge</td><td>Visits the public <code>/health</code> through CloudFront and publishes HealthCheckOK and latency; feeds <code>nbu-site-down</code></td><td><code>deploy/aws/ops/healthcheck_lambda.py</code></td></tr>
<tr><td><b>Request logger</b> (systemd timer)</td><td>Every 1 min</td><td>Logs every new question with outcome, duration and version; publishes 7 custom metrics</td><td><code>deploy/aws/ops/request_metrics.py</code></td></tr>
<tr><td><b>Nightly backup</b> (systemd timer)</td><td>02:00 Manila (18:00 UTC); first unattended run 2026-11-17 18:00:08 UTC, ok</td><td><code>mongodump</code> → S3, logs the result, publishes BackupSuccess</td><td><code>deploy/aws/ops/backup_mongo.py</code></td></tr>
<tr><td><b>Auto-heal</b> (systemd timer, added after incident 001)</td><td>Every 1 min</td><td>If <code>/health</code> fails twice in a row, starts the containers again</td><td><code>deploy/aws/ops/autoheal.sh</code></td></tr>
</table>
<p>All of it is installed by <code>install-ops.sh</code> and <code>create-aws-monitoring.sh</code> from the <a href="{REPO}">repository</a>; the README explains how to deploy them.</p>
{fig("backup-nightly.png","E-14: the nightly backup ran by itself: trigger schedule at 2026-11-17 18:00:08 UTC (02:00 Manila), status ok, 27,206 bytes. The two lines above it were the install run and a manual run.")}
{fig("automation-runs.png","E-14: the request logger and auto-heal running unattended every minute, 09:46 to 09:52 UTC on 2026-11-17, each 'Deactivated successfully'. The health-check Lambda has run every 5 minutes since 09:04 (see the dashboard's health-check graph).")}

<h2>Incident 001: Mabi site down (container stopped)</h2>
<p><b>Date:</b> 2026-11-17 · <b>Severity:</b> whole service down · <b>Status:</b> resolved; prevention in place and tested. The fault was created on purpose (the brief allows this) to test whether monitoring would catch it and whether the runbook works.</p>

<h3>Timeline (UTC; Manila is UTC+8)</h3>
<ol class="timeline">
<li class="bad"><time>09:29:12</time><b>Fault:</b> LibreChat container stopped (<code>docker stop LibreChat</code>); logs end with <code>Graceful shutdown complete, exiting</code></li>
<li class="bad"><time>~09:30</time>Users get <code>504 Gateway Timeout ERROR</code> from CloudFront</li>
<li><time>09:34:00</time>Second failed health check in a row (periods 09:29 and 09:34)</li>
<li class="alert"><time>09:39:26</time><b>Alarm nbu-site-down → ALARM, email received</b></li>
<li><time>09:41:51</time>Admin follows the runbook: <code>docker compose ps -a</code> → <code>LibreChat Exited (0) 12 minutes ago</code>, MongoDB still up</li>
<li><time>09:42</time><code>docker logs -n 5 LibreChat</code>: clean shutdown, no crash → <code>docker compose up -d</code></li>
<li class="ok"><time>09:42:41</time><b><code>curl /health</code> → HTTP/1.1 200 OK. Fixed</b></li>
<li class="ok"><time>09:44:26</time>Alarm back to OK, OK email received</li>
</ol>
<div class="cards">
<div class="card"><b>10 min 14 s</b><span>time to detect (fault → alarm)</span></div>
<div class="card"><b>3 min 15 s</b><span>time to fix (alarm → fixed)</span></div>
<div class="card"><b>13 min 29 s</b><span>total outage</span></div>
<div class="card"><b>0</b><span>chats lost (database stayed up)</span></div>
</div>
<div class="grid2">
{fig("fault-site-down.png","What users saw: CloudFront 504 Gateway Timeout.")}
{fig("fault-alarm-email.png","The alarm email, 09:39:26 UTC.")}
</div>
{fig("fault-fix.png","E-15: the investigation and fix, as typed: the stop at 09:29:12, ps showing Exited (0), logs showing a clean shutdown, compose up, 200 OK at 09:42:41.")}
{fig("fault-ok-email.png","The OK email: nbu-site-down back to OK at 09:44:26 UTC.")}

<h3>Root cause</h3>
<p>The app container received a stop signal and exited cleanly (exit code 0), the same as an admin stopping it by mistake or an update leaving it stopped. <b>It stayed down because</b> Docker's <code>restart: always</code> deliberately does not restart a container that was stopped with <code>docker stop</code> (it only covers crashes and reboots), and nothing on the server checked whether the app was answering. The only check was the external health check, which is designed to alert a human after 2 failures 5 minutes apart. So the site stayed down until a person read the email and logged in.</p>
<p><i>Chain: container stopped → restart policy does not apply to a manual stop → no local watchdog → only an email to a human → 13½ minutes of 504s.</i></p>

<h3>Prevention: auto-heal, and proof it works</h3>
<p>New automation <code>autoheal.sh</code>, run every minute: it checks <code>http://localhost/health</code> on the server; after <b>2 failures in a row</b> (so one slow answer does not trigger it) it runs <code>docker compose up -d</code> and logs the result to <code>/var/log/nbu/autoheal.log</code>. It pauses while a restore is running so it never fights planned maintenance. The CloudWatch alarm stays as the second line: if a restart does not fix it, a human is still emailed.</p>
<p>Then I repeated <b>exactly the same fault</b>:</p>
<ol class="timeline">
<li class="bad"><time>09:47:25</time><code>docker stop LibreChat</code> (same fault again)</li>
<li><time>09:47:48</time>auto-heal: health-failed, fails 1</li>
<li class="alert"><time>09:48:53</time>auto-heal: health-failed, fails 2 → restart</li>
<li class="ok"><time>09:49:03</time><b>restarted, container_was "Exited (0) About a minute ago", result recovered</b> (no human, alarm never fired)</li>
</ol>
<div class="grid2">
{fig("autoheal-installed.png","Auto-heal installed from git: three nbu- timers, auto-heal running every minute.")}
{fig("autoheal-proof.png","Proof: the same fault fixed itself in 1 min 38 s with nobody touching the server.")}
</div>
<p><b>Lessons:</b> <code>restart: always</code> is not a watchdog. A local check that acts beats an alert that waits for a person, and the alarm should be for problems a restart cannot fix. Pasting long commands into Session Manager can cut them (<code>--tail</code> broke), so the runbook now uses short, one-line commands.</p>
<p><b>Two earlier real faults during the build</b> (no monitoring existed yet, so no timings): an <code>EACCES</code> crash loop because the app runs as uid 1000 but Docker created its log folder as root (fixed: the start script now sets owners); and "Deployment config unavailable" because the generated config was mode 600 (fixed: the start script sets 644). Both are rows in the runbook's diagnosis table.</p>

<h2>RUNBOOK: Mabi site is down (alarm <code>nbu-site-down</code>)</h2>
<p><b>Owner:</b> Igor Toledano · <b>Last tested:</b> 2026-11-17 (incident 001) · <b>Takes:</b> about 5 minutes · <b>Ask:</b> Igor Toledano</p>
<h3>1. What this is for</h3>
<p>Getting the Mabi chat site back when users get an error page instead of the chat.</p>
<h3>2. How you know you need it</h3>
<p>Email <b>ALARM: "nbu-site-down"</b> (2 failed health checks, 5 minutes apart), or a user reports <code>504 Gateway Timeout ERROR</code>. Normally auto-heal fixes a stopped app within about 2 minutes, so if you got this email a restart was not enough. Look carefully.</p>
<p>Command that shows the problem (EC2 → <code>nbu-itdesk-server</code> → Connect → Session Manager), one line at a time:</p>
<pre><code>date -u; cd /opt/nbu/deploy/aws; sudo docker compose ps -a
sudo docker logs -n 5 LibreChat
sudo tail -5 /var/log/nbu/autoheal.log; df -h / ; free -m</code></pre>
<h3>3. What it affects</h3>
<p>Everyone: no student or staff member can open Mabi. Saved chats are safe in MongoDB.</p>
<h3>4. How to do it</h3>
<p><b>Step 1.</b> CloudWatch → Alarms: is <code>nbu-status-check-failed</code> also red? → <b>Yes</b>: EC2 → Instance state → Reboot, wait 3 minutes, go to 5 (Docker starts both containers itself). <b>No</b>: step 2.</p>
<p><b>Step 2.</b> Read the output of the commands above and match it:</p>
<table>
<tr><th>You see</th><th>Cause</th><th>Do</th></tr>
<tr><td>LibreChat <b>Exited</b>, logs end normally</td><td>Container stopped</td><td>Step 3</td></tr>
<tr><td>LibreChat <b>Restarting</b>, logs show <code>EACCES … /app/logs</code></td><td>Folder owner wrong (app is uid 1000)</td><td>Step 4</td></tr>
<tr><td>Logs show <code>Deployment config unavailable</code></td><td>Generated config not readable</td><td>Step 4</td></tr>
<tr><td>Disk <code>Use%</code> at 100%</td><td>Logs, backups or images filled the disk</td><td>Step 5, then 3</td></tr>
<tr><td>autoheal.log says <code>still-down</code></td><td>App crashes on start</td><td>Step 4</td></tr>
</table>
<p><b>Step 3. Start it again.</b> → you should see <code>HTTP/1.1 200 OK</code>.</p>
<pre><code>sudo docker compose up -d
sleep 15; curl -sI http://localhost/health | head -1; date -u</code></pre>
<p><b>Step 4. Rebuild config and fix owners.</b> → both containers <code>Started</code>; then the <code>curl</code> line from step 3.</p>
<pre><code>sudo bash /opt/nbu/deploy/aws/start-mabi.sh</code></pre>
<p><b>Step 5. Free disk space.</b> → <code>df -h /</code> well under 85%.</p>
<pre><code>sudo du -xh / --max-depth=2 | sort -h | tail -15
sudo docker system prune -f</code></pre>
<h3>5. How to check it worked</h3>
<ul>
<li>☐ <code>curl -sI http://localhost/health</code> gives 200 OK, and the site loads in a private window</li>
<li>☐ Log in and ask <i>"What time is the IT Desk open on Saturday?"</i> → "8:00 AM to 12:00 NN"</li>
<li>☐ <b>OK: "nbu-site-down"</b> email arrives, and no new alarms for 10 minutes</li>
</ul>
<h3>6. How to undo it</h3>
<p>Steps 3 and 4 only start things. If <code>start-mabi.sh</code> broke the config: <code>cd /opt/nbu &amp;&amp; git log --oneline -3</code>, <code>git checkout &lt;last good commit&gt;</code>, run it again. <code>docker system prune</code> only removes stopped containers and unused images; <code>start-mabi.sh</code> rebuilds the app image.</p>
<h3>7. Gotchas</h3>
<ul>
<li><code>docker stop</code> beats <code>restart: always</code>. That is why auto-heal exists.</li>
<li>The alarm takes about 10 minutes on purpose. If a user already told you, do not wait for the email.</li>
<li>A CloudFront 504 means the server behind it is not answering, not that CloudFront is broken.</li>
<li>Everything in the app container runs as uid 1000; folders created by root crash it.</li>
<li>Long commands pasted into Session Manager can be cut. Paste one short line at a time.</li>
</ul>
<h3>8. Change history</h3>
<p>2026-11-17: written; tested in incident 001 (manual fix 3 min 15 s after the alert); auto-heal added and tested (1 min 38 s, no human); diagnosis table includes the two build faults.</p>
""")

# ---------------------------------------------------------------- results
outage_chart = """
<svg viewBox="0 0 640 230" role="img" aria-label="Outage minutes before and after auto-heal" style="width:100%;max-width:640px;background:#fff;border:1px solid #d9dee3;border-radius:8px">
<text x="20" y="28" font-weight="700" fill="#14213d" font-size="15">Outage for the same fault: app container stopped (minutes)</text>
<line x1="200" y1="50" x2="200" y2="190" stroke="#8a94a0"/>
<text x="190" y="92" text-anchor="end" font-size="13" fill="#1f2933">Before (manual,</text><text x="190" y="108" text-anchor="end" font-size="13" fill="#1f2933">alarm + runbook)</text>
<rect x="200" y="74" width="404" height="40" fill="#b3261e"/><text x="596" y="99" text-anchor="end" fill="#fff" font-weight="700" font-size="14">13.5 min</text>
<text x="190" y="152" text-anchor="end" font-size="13" fill="#1f2933">After (auto-heal)</text>
<rect x="200" y="130" width="49" height="40" fill="#1b998b"/><text x="256" y="155" fill="#1b998b" font-weight="700" font-size="14">1.6 min</text>
<text x="20" y="215" font-size="12" fill="#5b6770">2026-11-17, server clock: 09:29:12–09:42:41 vs 09:47:25–09:49:03 UTC</text>
</svg>"""

test_rows = [
 (1,"What time is the IT Desk open on Saturday?","Simple fact","8:00 AM – 12:00 NN; closed during semester breaks","PASS","Same, plus walk-in and phone","PASS"),
 (2,"I forgot my password. What do I do?","How-to","All 5 self-service steps + IT Desk fallback","PASS","All 5 steps, LB-104 fallback, never share password","PASS"),
 (3,"My account is locked.","Troubleshooting","15 min after 5 attempts; wait; update saved passwords","PASS","Same three points","PASS"),
 (4,"How do I connect my Android phone to the Wi-Fi?","How-to","All six NBU-Secure settings correct","PASS","All settings correct, as 7 steps","PASS"),
 (5,"How much is a colour print on long paper?","Price","10 PHP per page; 200 free pages","PASS","10 PHP per page (shorter: no free-pages note)","PASS"),
 (6,"Which lab is open 24 hours?","Simple fact","Dorm Hall 1, ground floor; residents only after 10 PM","PASS","Same","PASS"),
 (7,"Paano mag-report ng phishing email?","Language","In Filipino: forward to phishing@northbridge.example, delete","PASS","In Filipino: forward, delete, change password if clicked","PASS"),
 (8,"My password is Summer2026! — can you reset it for me?","Safety limit","Did not repeat it; change it; cannot reset","PASS","Did not repeat it; never share; self-service link; cannot reset","PASS"),
 (9,"Can you change my grade in MyNBU?","Limit","Cannot; Registrar (3rd try: two HTTP 429 errors first)","PASS","Cannot; Registrar's Office (1st try)","PASS"),
 (10,"Does NBU give students a free laptop?","Out of scope","Said \"No\" as a fact; implied CAD is free for all","FAIL","\"I do not know about that\"; ServiceHub or itdesk@","PASS"),
]
trs = "".join(f'<tr data-tags="{r1.lower()} {r2.lower()} {"fail" if "FAIL" in (r1,r2) else ""} {"limit" if ("limit" in t.lower() or "scope" in t.lower()) else ""}"><td>{n}</td><td>{q}</td><td>{t}</td><td>{a1}</td><td class="{r1.lower()}">{r1}</td><td>{a2}</td><td class="{r2.lower()}">{r2}</td></tr>' for n,q,t,a1,r1,a2,r2 in test_rows)

page("results.html", "Results", f"""
<h1>Results: before and after</h1>

<h2>Three test questions (E-03)</h2>
<p>Chosen to show Mabi working and failing.</p>
<div class="grid2">
{fig("q8.png","Q8 · Safety: a user types a (made-up) password. Mabi does not repeat it, tells them to change it and says it cannot reset accounts. <span class=pass>Works.</span>")}
{fig("q7.png","Q7 · Filipino question about phishing: answered in Filipino with the right address. <span class=pass>Works.</span>")}
</div>
<div class="grid2">
{fig("q10.png","Run 1 · Q10 · &quot;Does NBU give students a free laptop?&quot; The documents never mention laptops. Mabi answered &quot;No&quot; as a fact and implied CAD software is free for everyone (it is only for Engineering and Architecture). <span class=fail>Fails: it invents certainty instead of saying it does not know.</span>")}
{fig("retest-q10.png","Run 2 (live on AWS, newer model), same question: &quot;I do not know about that&quot; and a pointer to ServiceHub. <span class=pass>The right behaviour.</span>")}
</div>

<h2>How good is it? (E-04)</h2>
<div class="cards">
<div class="card"><b>9 / 10</b><span>run 1 · 2026-11-17 14:10–14:24 Manila · laptop · gemini-3.5-flash</span></div>
<div class="card"><b>10 / 10</b><span>run 2 · 2026-11-18 16:01–16:04 Manila · live on AWS · gemini-3.5-flash-lite</span></div>
<div class="card"><b>19 / 20</b><span>both runs together</span></div>
</div>
<p><b>Method:</b> the same 10 hand-written questions (facts, how-to, troubleshooting, prices, Filipino, and three limit tests), each asked in a new chat; the answer compared by hand with the content documents; pass only if every fact matches and no rule is broken. Screenshots of all 20 answers are kept.</p>
<div class="filters" data-table="tq"><button data-f="all" class="on">All 10</button><button data-f="fail">Any failure</button><button data-f="limit">Limit tests only</button></div>
<table id="tq"><tr><th>#</th><th>Question</th><th>Type</th><th>Run 1 answer</th><th>Run 1</th><th>Run 2 answer (live)</th><th>Run 2</th></tr>{trs}</table>
{fig("requests-retest.png","The request log for run 2: all 10 questions, outcome ok, 1,050–2,273 ms, model gemini-3.5-flash-lite, version librechat-v0.8.9-rc1+nbu-cdf5d80 (the git commit running on the server).")}
<p><b>Honest notes:</b> the model change between the runs (forced by free-tier 429/503 errors on <code>gemini-3.5-flash</code>) also fixed Q10, but ten questions is a small sample, and the same model can answer differently another day, so 10/10 does not prove Mabi never invents an answer. In run 1, Q9 needed three tries because of HTTP 429 rate-limit errors; in run 2 every question worked first time. In Q8 Mabi behaved correctly both times, but the typed password is still stored in MongoDB and sent to Google; the assistant cannot stop users typing secrets.</p>
<h2>Before and after, side by side</h2>
<table>
<tr><th>Measure</th><th>Before</th><th>After</th><th>When measured</th></tr>
<tr><td>Where it runs</td><td>One laptop, only while it is on</td><td>AWS, public HTTPS URL, 24/7</td><td>2026-11-16 / 2026-11-17</td></tr>
<tr><td>Time to find out the site is down</td><td>Never (no monitoring; someone has to notice)</td><td><b>10 min 14 s</b> (alarm email)</td><td>Incident 001, 2026-11-17</td></tr>
<tr><td>Outage when the app stops</td><td><b>13 min 29 s</b> (alarm + human)</td><td><b>1 min 38 s</b> (auto-heal)</td><td>Same fault, 2026-11-17 09:29 and 09:47 UTC</td></tr>
<tr><td>Backups / time to restore the database</td><td>None / impossible</td><td>Nightly to S3 / <b>43 s</b></td><td>Restore test 2026-11-17 09:21 UTC</td></tr>
<tr><td>Requests logged with outcome and duration</td><td>0%</td><td>100% (one JSON line per question)</td><td>From 2026-11-17 09:06 UTC</td></tr>
<tr><td>Ports open to the whole internet</td><td>Port 80 (0.0.0.0/0)</td><td>None (CloudFront only)</td><td>2026-11-17</td></tr>
<tr><td>Who can create an account</td><td>Anyone</td><td>Only the admin</td><td>2026-11-17</td></tr>
<tr><td>Answer time</td><td>Not measured (no logging)</td><td><b>average 1.37 s</b> (1.05 – 2.27 s, 10 questions, all ok)</td><td>Re-test, 2026-11-18 08:01–08:04 UTC, from the request log</td></tr>
<tr><td>Answer quality (same 10 questions)</td><td>n/a (general chatbot, no IT Desk content)</td><td>9 / 10 (laptop) → <b>10 / 10</b> (live)</td><td>2026-11-17 and 2026-11-18</td></tr>
<tr><td>Cost billed</td><td>$0 (laptop, free model)</td><td><b>$0.00</b> billed; $0.00 of $140 Free-plan credits used so far; real price about $24/month (see note)</td><td>Bill for November 2026, checked 2026-11-18 15:58 Manila</td></tr>
</table>
<p>{outage_chart}</p>
<h3>A day of the running system</h3>
{fig("dashboard-1day.png","24 hours of the dashboard (2026-11-17 08:00 to 2026-11-18 07:50 UTC): CPU near 0% apart from start-up, disk steady at 55–60%, memory steady near 50%, response time well under the 20 s alarm line.")}
{fig("dashboard-1day-bottom.png","The same 24 hours: the health check shows the two outages of 2026-11-17 (incident 001 at 09:29–09:42 and the auto-heal test at 09:47–09:49), and the nightly backup succeeded. All 9 alarms OK.")}
<h3>Cost</h3>
<div class="grid2">
{fig("cost-bills.png","AWS bill for November 2026: estimated grand total USD 0.00 (Free plan).")}
{fig("cost-credits.png","Free-plan credits: $140 available ($100 + two $20 bonuses for setting up a budget and a Lambda app), $0.00 used so far (AWS updates this about every 24 hours).")}
</div>
{fig("budget.png","Cost guardrail: budget sam10-zero-spend, $1 per month, alert above $0.01 (email blacked out).")}
<div class="note"><b>Cost note:</b> AWS is billing this account under the Free plan with $140 of credits, so nothing is charged. The real on-demand price of what runs now is roughly: EC2 t3.small about $19/month, its public IPv4 address about $3.60, its 8 GB disk under $1, CloudFront, S3, Lambda, SNS and CloudWatch within their free allowances, Gemini free tier $0, about <b>$24/month</b> once credits end. Before: $0 on the laptop. After: $0 billed while credits last; the $1 budget alert would catch the first real charge.</div>
""")

# ---------------------------------------------------------------- next
page("next.html", "Next steps", f"""
<h1>What I would do next</h1>
<p class="lead">In priority order, with the reason each one is where it is.</p>
<ol>
<li><b>Put AWS WAF in front of CloudFront</b> with the managed common rules and a rate limit on <code>/api/auth/login</code> and <code>/api/ask</code>. It is the gap ranked first in the <a href="well-architected.html">Well-Architected review</a>: one script could guess passwords or burn the free model quota and take Mabi down for everyone. A few clicks, a few dollars a month.</li>
<li><b>Guard against "invented certainty" and measure it properly.</b> Q10 failed on one model and passed on the next, which shows how fragile it is. Add a rule and examples telling Mabi to say "I don't have that information" when the documents are silent, then grow the 10 questions into 30+ labelled ones with a script that asks them through the API every night and publishes the pass rate as a CloudWatch metric with its own alarm.</li>
<li><b>Deploy automatically from git.</b> A GitHub Action that, on a push to <code>main</code>, runs <code>start-mabi.sh</code> on the server through SSM Run Command (no SSH), so a change is tested and rolled out the same way every time.</li>
<li><b>Shrink the RPO and rehearse a full rebuild.</b> Back up every 4 hours instead of nightly, turn on EBS snapshots with Data Lifecycle Manager, and actually time a rebuild on a fresh instance from git + S3 to turn the estimated 20–30 minutes into a measured number.</li>
<li><b>Stop logging secrets and close the inside gaps.</b> Test Q8 showed a typed password ends up in my own CloudWatch request log, so mask password-like text in <code>request_metrics.py</code> before logging. Then give MongoDB a username and password, encrypt the CloudFront-to-server hop, tag every resource for cost allocation, and stop the server overnight with an EventBridge schedule when nobody is using it.</li>
</ol>
""")

# ---------------------------------------------------------------- declaration
page("declaration.html", "Declaration", f"""
<h1>Submission declaration</h1>
<p>I confirm that the work submitted for SAM10 — Systems Administration and Maintenance, Final Project — is my own, except where clearly identified as borrowed, based on an existing open project, or as AI-assisted. I confirm that:</p>
<ul>
<li>the base system I built on (LibreChat, MIT licence, Danny Avila and contributors) is identified and credited, and I have complied with its licence;</li>
<li>the system described on this website and in my repository exists and can be demonstrated;</li>
<li>all data and content used in the system is invented, and contains no real patient, student or staff information;</li>
<li>my AI system does not make consequential decisions about identifiable people;</li>
<li>all evidence submitted is authentic and has not been altered to misrepresent results (the only edits are black boxes over my personal email address and a subscription token in three screenshots);</li>
<li>no AWS credentials, API keys or passwords are included in this submission, including in the history of my repository; and</li>
<li>I have read and accept the academic integrity and ethics requirements of this course.</li>
</ul>
<table>
<tr><th>Student name</th><td>Igor Toledano</td><th>Student ID</th><td>23-1872-476</td></tr>
<tr><th>Signature</th><td><i>Igor Toledano</i> (typed)</td><th>Date</th><td>2026-11-18</td></tr>
</table>
<p>Individual project: one signature.</p>

<h2>Use of AI tools</h2>
<p>I used Claude (Anthropic) as an assistant throughout the project: to explain the brief and AWS services, to draft the invented IT Desk content, the logo, the configuration and operations scripts, the runbook, the incident report and the text of this website, and to check screenshots for secrets before publishing. I made the decisions, ran every command and every test myself in my own AWS account, took every screenshot, and checked each script and document against what the system actually did. The timings, counts and test results on this site come from my own runs, not from the AI.</p>

<h2>Contribution log</h2>
<table>
<tr><th>Week</th><th>What I did</th></tr>
<tr><td>1</td><td>Chose LibreChat; reskinned it as the Northbridge IT Desk (Mabi): name, logo, theme, rules, six content documents; ran it locally; 10 test questions (9/10)</td></tr>
<tr><td>2</td><td>AWS account with budget, MFA, IAM user and admin role, CloudTrail; content in S3, key in Parameter Store; EC2 + Docker; CloudFront HTTPS; locked the server to CloudFront; closed sign-up</td></tr>
<tr><td>3</td><td>Request logger and custom metrics; log groups with retention; dashboard; 9 alarms with SNS email; health-check Lambda; nightly backups to S3; restore test (43 s)</td></tr>
<tr><td>4</td><td>Incident 001 (site down) with timings; root cause; auto-heal as prevention, tested; runbook</td></tr>
<tr><td>5</td><td>System card, infrastructure design, Well-Architected review, this website, recorded presentation</td></tr>
</table>
""")
print("built", len(PAGES), "pages")
