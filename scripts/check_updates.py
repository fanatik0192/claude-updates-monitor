#!/usr/bin/env python3
"""
Claude Updates Monitor
Verifie les mises a jour d'Anthropic et envoie des notifications Telegram.
"""

import os
import json
import hashlib
import requests
from datetime import datetime, timedelta
from pathlib import Path

try:
    from bs4 import BeautifulSoup
    import feedparser
except ImportError:
    print("Installing dependencies...")
    os.system("pip install beautifulsoup4 feedparser")
    from bs4 import BeautifulSoup
    import feedparser


# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CACHE_FILE = Path("cache/last_check.json")

# Sources a monitorer
SOURCES = {
    "changelog": {
        "url": "https://docs.anthropic.com/en/docs/changelog",
        "type": "html",
        "name": "Anthropic API Changelog"
    },
    "github_releases": {
        "url": "https://github.com/anthropics/claude-code/releases.atom",
        "type": "atom",
        "name": "Claude Code Releases"
    },
    "blog": {
        "url": "https://www.anthropic.com/news",
        "type": "html",
        "name": "Anthropic Blog"
    },
    "status": {
        "url": "https://status.anthropic.com",
        "type": "status",
        "name": "Anthropic Status"
    }
}


def load_cache():
    """Charge le cache des updates precedentes."""
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {"seen_hashes": [], "last_check": None}


def save_cache(cache):
    """Sauvegarde le cache."""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    cache["last_check"] = datetime.now().isoformat()
    # Garde seulement les 100 derniers hashes
    cache["seen_hashes"] = cache["seen_hashes"][-100:]
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def get_hash(content):
    """Genere un hash unique pour un contenu."""
    return hashlib.md5(content.encode()).hexdigest()[:12]


def send_telegram(message):
    """Envoie un message Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[TELEGRAM DISABLED] {message[:100]}...")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"[TELEGRAM] Message envoye!")
            return True
        else:
            print(f"[TELEGRAM ERROR] {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")
        return False


def fetch_changelog():
    """Recupere les updates du changelog Anthropic."""
    updates = []
    try:
        response = requests.get(SOURCES["changelog"]["url"], timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        # Cherche les sections de date dans le changelog
        # La structure peut varier, on cherche des patterns communs
        headers = soup.find_all(["h2", "h3"])
        for header in headers[:5]:  # Les 5 premieres
            text = header.get_text(strip=True)
            # Cherche des dates dans le texte
            if any(month in text for month in ["January", "February", "March", "April",
                "May", "June", "July", "August", "September", "October", "November", "December",
                "2024", "2025", "2026"]):
                # Recupere le contenu suivant
                content = ""
                sibling = header.find_next_sibling()
                while sibling and sibling.name not in ["h2", "h3"]:
                    content += sibling.get_text(strip=True) + " "
                    sibling = sibling.find_next_sibling()
                    if len(content) > 500:
                        break

                updates.append({
                    "source": "API Changelog",
                    "title": text,
                    "summary": content[:300] + "..." if len(content) > 300 else content,
                    "url": SOURCES["changelog"]["url"],
                    "hash": get_hash(text + content[:100])
                })
    except Exception as e:
        print(f"[ERROR] Changelog: {e}")

    return updates


def fetch_github_releases():
    """Recupere les releases Claude Code depuis GitHub."""
    updates = []
    try:
        feed = feedparser.parse(SOURCES["github_releases"]["url"])
        for entry in feed.entries[:5]:  # Les 5 dernieres
            updates.append({
                "source": "Claude Code",
                "title": entry.get("title", "New Release"),
                "summary": entry.get("summary", "")[:300].replace("<", "").replace(">", ""),
                "url": entry.get("link", SOURCES["github_releases"]["url"]),
                "hash": get_hash(entry.get("id", entry.get("title", "")))
            })
    except Exception as e:
        print(f"[ERROR] GitHub Releases: {e}")

    return updates


def fetch_blog():
    """Recupere les articles du blog Anthropic."""
    updates = []
    try:
        response = requests.get(SOURCES["blog"]["url"], timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        # Cherche les articles/posts
        articles = soup.find_all("article")[:5] or soup.find_all("a", href=True)[:10]

        for article in articles:
            title = article.get_text(strip=True)[:100]
            link = article.get("href", "")
            if link and not link.startswith("http"):
                link = "https://www.anthropic.com" + link

            if title and len(title) > 10 and "claude" in title.lower() or "anthropic" in title.lower():
                updates.append({
                    "source": "Blog",
                    "title": title,
                    "summary": "",
                    "url": link or SOURCES["blog"]["url"],
                    "hash": get_hash(title)
                })
    except Exception as e:
        print(f"[ERROR] Blog: {e}")

    return updates


def fetch_status():
    """Verifie le status d'Anthropic."""
    updates = []
    try:
        response = requests.get(SOURCES["status"]["url"], timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        # Cherche les indicateurs de status
        status_text = soup.get_text().lower()

        # Detecte les problemes
        if any(word in status_text for word in ["degraded", "outage", "incident", "maintenance", "investigating"]):
            # Il y a un probleme
            updates.append({
                "source": "Status",
                "title": "Incident detecte sur Anthropic",
                "summary": "Un incident ou maintenance est en cours. Consultez la page status.",
                "url": SOURCES["status"]["url"],
                "hash": get_hash(f"incident-{datetime.now().strftime('%Y-%m-%d')}")
            })
    except Exception as e:
        print(f"[ERROR] Status: {e}")

    return updates


def format_message(update):
    """Formate un message Telegram."""
    emoji = {
        "API Changelog": "🔧",
        "Claude Code": "📦",
        "Blog": "📰",
        "Status": "⚠️"
    }

    return f"""
{emoji.get(update['source'], '📌')} *CLAUDE UPDATE*

🏷️ *Source:* {update['source']}
📝 *{update['title']}*

{update['summary'][:200] if update['summary'] else ''}

🔗 [Voir plus]({update['url']})

━━━━━━━━━━━━━━━━━━
""".strip()


def main():
    print(f"[START] Claude Updates Monitor - {datetime.now().isoformat()}")

    # Charge le cache
    cache = load_cache()
    seen_hashes = set(cache.get("seen_hashes", []))
    new_hashes = list(seen_hashes)

    # Collecte les updates de toutes les sources
    all_updates = []
    all_updates.extend(fetch_changelog())
    all_updates.extend(fetch_github_releases())
    all_updates.extend(fetch_blog())
    all_updates.extend(fetch_status())

    print(f"[INFO] {len(all_updates)} updates trouvees au total")

    # Filtre les nouvelles updates
    new_updates = []
    for update in all_updates:
        if update["hash"] not in seen_hashes:
            new_updates.append(update)
            new_hashes.append(update["hash"])
            print(f"[NEW] {update['source']}: {update['title'][:50]}")

    print(f"[INFO] {len(new_updates)} nouvelles updates")

    # Envoie les notifications
    if new_updates:
        for update in new_updates[:5]:  # Max 5 notifications
            message = format_message(update)
            send_telegram(message)
        # Resume final
        send_telegram(f"✅ *{len(new_updates)} nouvelle(s) update(s) detectee(s)*\n📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    else:
        # Notification quand aucune nouveaute
        send_telegram(f"✅ *Check OK* - Aucune nouveaute\n📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # Sauvegarde le cache
    cache["seen_hashes"] = new_hashes
    save_cache(cache)

    print(f"[END] Termine - {len(new_updates)} notifications envoyees")


if __name__ == "__main__":
    main()
