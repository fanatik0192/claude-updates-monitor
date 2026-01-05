# Claude Updates Monitor

Veille automatique des mises a jour Claude/Anthropic avec notifications Telegram.

## Sources monitorees

- **Anthropic API Changelog** - Mises a jour API, nouveaux modeles
- **Claude Code Releases** - Nouvelles versions de Claude Code
- **Anthropic Blog** - Articles et annonces
- **Anthropic Status** - Incidents et maintenances

## Comment ca marche

```
GitHub Actions (cron) → Script Python → Telegram Bot → Ton telephone
```

1. Toutes les 12h, GitHub Actions execute le script
2. Le script verifie les sources pour de nouvelles updates
3. Si nouveaute, envoie une notification Telegram
4. Le cache evite les doublons

## Installation

1. Fork ce repo
2. Ajoute les secrets dans Settings > Secrets > Actions :
   - `TELEGRAM_BOT_TOKEN` : Token de ton bot
   - `TELEGRAM_CHAT_ID` : Ton ID Telegram
3. Active GitHub Actions
4. C'est tout !

## Configuration

### Modifier la frequence

Dans `.github/workflows/claude-updates.yml` :

```yaml
schedule:
  - cron: '0 8,20 * * *'  # 8h et 20h UTC
```

### Tester manuellement

Actions > Claude Updates Monitor > Run workflow

## Structure

```
.github/workflows/claude-updates.yml  # Workflow GitHub Actions
scripts/check_updates.py              # Script de verification
cache/last_check.json                 # Cache (auto-genere)
```

## Couts

**Gratuit** - GitHub Actions offre 2000 min/mois, on utilise ~5 min/mois.

---

*Cree avec Claude Code*
