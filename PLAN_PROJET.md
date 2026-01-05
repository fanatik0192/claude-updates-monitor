# PROJET : Veille Claude Updates via GitHub Actions + Telegram

## OBJECTIF
Recevoir une notification Telegram automatique a chaque mise a jour de Claude (API, Claude Code, modeles, fonctionnalites).

**Solution choisie : GitHub Actions** (gratuit, fiable, pas de serveur)

---

## TES CREDENTIALS

```
BOT TOKEN : 8562655785:AAEubzqhtsfXLoX3aT8M9wZVS0b0G5wgNcQ
CHAT ID   : 5050460432
```

---

## ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           GITHUB ACTIONS                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐             │
│  │  Cron    │──►│  Fetch   │──►│ Compare  │──►│ Telegram │             │
│  │ (12h)    │   │ Sources  │   │ + Cache  │   │   API    │             │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘             │
│                                                                          │
│  Gratuit : 2000 min/mois (on utilise ~5 min/mois)                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## SOURCES MONITOREES

| Source | URL | Type |
|--------|-----|------|
| Anthropic Changelog | docs.anthropic.com/en/docs/changelog | HTML |
| Claude Code Releases | github.com/anthropics/claude-code/releases | Atom |
| Anthropic Blog | anthropic.com/news | RSS/HTML |
| Anthropic Status | status.anthropic.com | Status |

---

## PHASES DU PROJET

### PHASE 1 : Creer le repo GitHub (Toi - 2 min)
```
1. Va sur github.com
2. Clique "New repository"
3. Nom : claude-updates-monitor
4. Public ou Private (les deux marchent)
5. Coche "Add a README"
6. Create repository
```

### PHASE 2 : Ajouter les secrets (Toi - 2 min)
```
1. Dans ton repo, va dans Settings > Secrets and variables > Actions
2. Clique "New repository secret"
3. Ajoute :
   - Name: TELEGRAM_BOT_TOKEN
     Value: 8562655785:AAEubzqhtsfXLoX3aT8M9wZVS0b0G5wgNcQ

   - Name: TELEGRAM_CHAT_ID
     Value: 5050460432
```

### PHASE 3 : Ajouter les fichiers (Toi - 2 min)
```
1. Copie les fichiers que je te fournis dans le repo
2. Structure :
   .github/
   └── workflows/
       └── claude-updates.yml
   scripts/
   └── check_updates.py
```

### PHASE 4 : Tester (Toi - 1 min)
```
1. Va dans Actions > Claude Updates Monitor
2. Clique "Run workflow"
3. Verifie que tu recois la notification Telegram
```

---

## AVANTAGES GITHUB ACTIONS

| Critere | GitHub Actions | n8n Cloud |
|---------|----------------|-----------|
| Prix | GRATUIT | 14 jours puis payant |
| Limite | 2000 min/mois | - |
| Notre usage | ~5 min/mois | - |
| Fiabilite | 99.9% | 99.9% |
| Maintenance | Zero | Zero |
| Hebergement | GitHub | Leur cloud |

---

## FICHIERS A CREER

| Fichier | Description |
|---------|-------------|
| `.github/workflows/claude-updates.yml` | Workflow GitHub Actions |
| `scripts/check_updates.py` | Script Python qui fait le travail |
| `cache/last_check.json` | Cache des updates deja vues |
| `README.md` | Documentation du repo |

---

## FREQUENCE

Par defaut : **toutes les 12 heures** (8h et 20h)

Modifiable dans le workflow :
```yaml
schedule:
  - cron: '0 8,20 * * *'  # 8h et 20h UTC
```

Options :
- Toutes les 6h : `'0 */6 * * *'`
- Toutes les 4h : `'0 */4 * * *'`
- 1x par jour : `'0 9 * * *'` (9h UTC)

---

## ESTIMATION USAGE

```
1 run = ~30 secondes
2 runs/jour = 1 minute/jour
30 jours = 30 minutes/mois

Quota gratuit = 2000 minutes/mois
Marge = 1970 minutes restantes

→ Tu peux meme checker toutes les heures si tu veux !
```

---

*Document cree le 05/01/2026*
