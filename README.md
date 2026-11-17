# Northbridge University IT Desk — Mabi

An IT help-desk chatbot for **Northbridge University**, a fictional university. Students and
staff can ask Mabi about accounts and passwords, MFA, Wi-Fi, email, NBU Drive, software,
printing and the computer labs.

SAM10 Systems Administration and Maintenance — Final Project (individual).

## Credits and licence (base system)
| | |
|---|---|
| Base system | LibreChat |
| Source | https://github.com/danny-avila/LibreChat (images now published by the LibreChat-AI organisation) |
| Author | Danny Avila and the LibreChat contributors |
| Licence | MIT — https://github.com/danny-avila/LibreChat/blob/main/LICENSE |
| Version used | LibreChat v0.8.9-rc1 (dev image, first run 2026-11-16) |
| AI model | Google Gemini (`gemini-3.5-flash`) via the Gemini API free tier, personal Google account |

The MIT licence lets us use, modify and rename the software as long as the copyright and
licence notice are kept. All university and IT Desk information in `content/` is invented; there is no
personal data in this project.

## What was changed (the reskin)
| Part | Original LibreChat | Northbridge IT Desk (Mabi) |
|---|---|---|
| Name and logo | "LibreChat", LibreChat logo | "Northbridge University IT Desk" and assistant "Mabi", bridge-and-star logo (`brand/logo.svg`) |
| Colours | Grey/white with green buttons | University palette: navy, teal, gold (`interface.theme` in `librechat.yaml`) |
| Data | None — general chat | Six invented IT Desk documents (`content/`) |
| Wording | General AI assistant | IT help desk: passwords, Wi-Fi, printing, labs; safety rules on passwords (`scripts/build_config.py`) |
| Model choice | Many providers, user picks | One fixed assistant (model specs enforced) |
| AWS integration | — | Week 2: content stored in S3, key in Parameter Store |

## Folder layout
```
northbridge-itdesk/
  brand/        logo, icons and the Dockerfile for the reskinned image
  content/      the IT Desk's (invented) knowledge, in Markdown
  scripts/      build_config.py turns content/ into librechat.yaml
  deploy/       docker-compose.override.yml and the .env changes
  docs/         test questions
  librechat.yaml  generated — edit content/ and re-run the script instead
```

## Run it on Windows (week 1)

### 0. Install the tools (once)
1. **Docker Desktop** — https://www.docker.com/products/docker-desktop/ . Accept the WSL 2
   option during install, restart, then open Docker Desktop and wait until it says
   *Engine running*. Give it at least 4 GB of memory (Settings → Resources).
2. **Git for Windows** — https://git-scm.com/download/win (default options are fine).
3. **Python 3** (optional, only to rebuild the config) — https://www.python.org/downloads/ .
   Tick *Add python.exe to PATH* during install.
4. **A Gemini API key** — sign in at https://aistudio.google.com/apikey and click
   *Create API key*. Keep it private. Use only invented data with it.

### 1. Put the two folders side by side
Open **PowerShell** and run:
```powershell
mkdir C:\sam10
cd C:\sam10
git clone https://github.com/danny-avila/LibreChat.git
```
Unzip this project so you have `C:\sam10\northbridge-itdesk\README.md`.

### 2. Run the ORIGINAL LibreChat first and take a screenshot (evidence E-05)
```powershell
cd C:\sam10\LibreChat
copy .env.example .env
notepad .env
```
In Notepad, set `GOOGLE_KEY=` to your key, save, then:
```powershell
docker compose up -d
```
The first start downloads a few GB and takes several minutes. Open http://localhost:3080 ,
click *Sign up*, create an account (use an invented name and an email you control), ask any
question, and **take a screenshot**. This is your "before" picture. Then stop it:
```powershell
docker compose down
```

### 3. Apply the Northbridge reskin
```powershell
cd C:\sam10\LibreChat
copy ..\northbridge-itdesk\deploy\docker-compose.override.yml .
notepad .env
```
Make the changes listed in `C:\sam10\northbridge-itdesk\deploy\env-changes.txt`, then save.

### 4. Build and start Mabi
```powershell
docker compose up -d --build
```
Open http://localhost:3080 (press **Ctrl+F5** to clear the old logo from the cache).
You should see the Northbridge name, the bridge logo and navy/teal colours, and *Mabi* as
the only assistant. Ask "I forgot my password. What do I do?" and **take a screenshot**
(evidence E-01).

### 5. Check it is healthy
```powershell
docker compose ps                 # all services should be "running"
docker compose logs api --tail 50 # look for errors, e.g. about librechat.yaml
```

### 6. Record the version you used
```powershell
docker image inspect northbridge-itdesk-librechat:local --format "{{.Created}}"
```
Write the date in the Credits table above.

### 7. Start your Git repository (do this today — commit history is marked)
```powershell
cd C:\sam10\northbridge-itdesk
git init
git add .
git commit -m "Week 1: Northbridge IT Desk reskin of LibreChat"
```
Check `git status` never shows a `.env` file. Your key must never be committed.

## Changing the IT Desk information
1. Edit or add Markdown files in `content/`.
2. `python scripts\build_config.py`
3. `cd C:\sam10\LibreChat` then `docker compose restart api`

## Changing the logo or colours
Edit `brand/logo.svg` (and `northbridge-logo.svg`), or the theme colours in `scripts/build_config.py`, then in `C:\sam10\LibreChat` run
`docker compose up -d --build`. If you change the logo, regenerate the PNG icons too.

## Troubleshooting
| Symptom | Likely cause | Fix |
|---|---|---|
| `docker` is not recognised | Docker Desktop not running | Open Docker Desktop, wait for *Engine running* |
| Page shows old LibreChat look | Browser cache | Ctrl+F5, or open a private window |
| Assistant answers with an error about the model | Model name not available to your key | Check the model list in AI Studio; change `MODEL` in `scripts/build_config.py` and `GOOGLE_MODELS` in `.env`, rebuild the config, restart |
| 429 / quota errors | Free-tier rate limit reached | Wait a minute (or until the next day); note it — it is a good fault for WS-F |
| Logs say librechat.yaml is invalid | YAML typo | Re-run `python scripts\build_config.py` instead of editing by hand |
| Build fails pulling the base image | Registry not reachable | In `brand/Dockerfile` switch to the `ghcr.io/...` image named in the comment |

## Contribution log (individual project)
| Week | Dates | What I did | Evidence |
|---|---|---|---|
| 1 | | Chose LibreChat, reskinned it as Northbridge IT Desk (Mabi), ran it locally | Screenshots E-01, E-05 |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

## Use of AI tools (copy into the declaration, in your own words)
Claude (Anthropic) was used to help draft the IT Desk content, the branding files, the
configuration script and this README. I checked every file by running the system locally,
testing the answers against the content files, and editing the text myself.
