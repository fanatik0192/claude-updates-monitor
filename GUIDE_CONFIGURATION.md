# GUIDE : Configuration GitHub Actions pour Claude Updates

## ETAPE 1 : Creer le repository GitHub (2 min)

### Option A : Nouveau repo
```
1. Va sur https://github.com/new
2. Repository name : claude-updates-monitor
3. Description : Veille automatique des mises a jour Claude/Anthropic
4. Visibilite : Public ou Private (les deux marchent)
5. Coche : Add a README file
6. Clique : Create repository
```

### Option B : Utiliser un repo existant
Tu peux aussi ajouter ces fichiers dans n'importe quel repo existant.

---

## ETAPE 2 : Ajouter les secrets (2 min)

Les secrets permettent de stocker tes credentials de maniere securisee.

```
1. Dans ton repo GitHub, va dans :
   Settings > Secrets and variables > Actions

2. Clique "New repository secret"

3. Premier secret :
   Name  : TELEGRAM_BOT_TOKEN
   Value : 8562655785:AAEubzqhtsfXLoX3aT8M9wZVS0b0G5wgNcQ
   → Clique "Add secret"

4. Deuxieme secret :
   Name  : TELEGRAM_CHAT_ID
   Value : 5050460432
   → Clique "Add secret"
```

Screenshot du chemin :
```
Repository > Settings > Secrets and variables > Actions > New repository secret
```

---

## ETAPE 3 : Ajouter les fichiers (2 min)

### Structure des fichiers a creer
```
ton-repo/
├── .github/
│   └── workflows/
│       └── claude-updates.yml    ← Workflow GitHub Actions
├── scripts/
│   └── check_updates.py          ← Script Python
├── cache/
│   └── (cree automatiquement)
└── README.md
```

### Methode 1 : Via l'interface GitHub

1. Dans ton repo, clique "Add file" > "Create new file"

2. Pour le workflow :
   - Nom : `.github/workflows/claude-updates.yml`
   - Contenu : copie depuis le fichier fourni

3. Pour le script :
   - Nom : `scripts/check_updates.py`
   - Contenu : copie depuis le fichier fourni

### Methode 2 : Via Git (si tu as clone le repo)
```powershell
# Clone ton repo
git clone https://github.com/TON_USERNAME/claude-updates-monitor.git
cd claude-updates-monitor

# Copie les fichiers depuis claude-updates-monitor/
# (le dossier que j'ai cree)

# Commit et push
git add .
git commit -m "Add Claude updates monitor"
git push
```

### Methode 3 : Upload direct
1. Telecharge le dossier complet que j'ai cree
2. Dans GitHub, clique "Add file" > "Upload files"
3. Drag & drop tous les fichiers

---

## ETAPE 4 : Activer GitHub Actions (30 sec)

```
1. Va dans l'onglet "Actions" de ton repo
2. Si c'est la premiere fois, clique "I understand my workflows, go ahead and enable them"
3. Tu devrais voir "Claude Updates Monitor" dans la liste
```

---

## ETAPE 5 : Tester manuellement (1 min)

```
1. Va dans Actions > Claude Updates Monitor
2. Clique "Run workflow" (bouton a droite)
3. Clique "Run workflow" (bouton vert)
4. Attends ~30 secondes
5. Verifie sur Telegram !
```

### En cas de succes
Tu recevras un message du type :
```
📦 CLAUDE UPDATE

🏷️ Source: Claude Code
📝 v1.0.xxx - Release notes...

🔗 Voir plus
```

### En cas d'echec
1. Clique sur le workflow en erreur
2. Regarde les logs pour voir l'erreur
3. Causes courantes :
   - Secrets mal configures
   - Erreur de syntaxe dans les fichiers

---

## ETAPE 6 : C'est fini !

Le workflow s'executera automatiquement :
- **8h UTC** (9h Paris)
- **20h UTC** (21h Paris)

Tu n'as plus rien a faire !

---

## MODIFIER LA FREQUENCE

Dans `.github/workflows/claude-updates.yml`, ligne `cron:` :

```yaml
# Toutes les 12h (par defaut)
- cron: '0 8,20 * * *'

# Toutes les 6h
- cron: '0 */6 * * *'

# Toutes les 4h
- cron: '0 */4 * * *'

# Toutes les 2h
- cron: '0 */2 * * *'

# 1x par jour a 9h UTC
- cron: '0 9 * * *'

# 1x par jour a 9h et 18h UTC
- cron: '0 9,18 * * *'
```

Format cron : `minute heure jour mois jour_semaine`

---

## TROUBLESHOOTING

### "Workflow not found"
→ Verifie que le fichier est bien dans `.github/workflows/`

### "Error: Resource not accessible by integration"
→ Va dans Settings > Actions > General > Workflow permissions
→ Selectionne "Read and write permissions"

### "Telegram error 401"
→ Token invalide. Verifie le secret TELEGRAM_BOT_TOKEN

### "Telegram error 400 chat not found"
→ Tu n'as jamais parle a ton bot. Ouvre le bot sur Telegram et envoie /start

### Le workflow ne se declenche pas automatiquement
→ Les workflows schedules peuvent avoir du retard (jusqu'a 1h)
→ Ils ne tournent pas si le repo est inactif depuis 60 jours

---

## LOGS ET HISTORIQUE

Pour voir l'historique des executions :
```
Actions > Claude Updates Monitor > Clique sur une execution
```

Tu verras :
- Heure d'execution
- Status (succes/echec)
- Logs detailles
- Nombre de notifications envoyees

---

## COUTS

| Element | Cout |
|---------|------|
| GitHub Actions | Gratuit (2000 min/mois) |
| Notre usage | ~5 min/mois |
| Telegram Bot | Gratuit |
| **TOTAL** | **0 EUR** |

---

*Guide cree le 05/01/2026*
