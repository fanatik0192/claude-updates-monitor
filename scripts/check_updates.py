#!/usr/bin/env python3
"""
Claude Updates Monitor - VERSION COMPLETE
Verifie TOUTES les mises a jour d'Anthropic et envoie des notifications Telegram.
"""

import os
import json
import hashlib
import requests
import re
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

# TOUTES les sources a monitorer
SOURCES = {
    # API & Documentation
    "changelog": {
        "url": "https://docs.anthropic.com/en/docs/changelog",
        "name": "API Changelog"
    },
    "docs_api": {
        "url": "https://docs.anthropic.com/en/api",
        "name": "API Documentation"
    },

    # Claude Code
    "github_releases": {
        "url": "https://github.com/anthropics/claude-code/releases.atom",
        "name": "Claude Code GitHub"
    },
    "npm_claude_code": {
        "url": "https://registry.npmjs.org/@anthropic-ai/claude-code",
        "name": "Claude Code npm"
    },

    # SDK & Libraries
    "npm_sdk": {
        "url": "https://registry.npmjs.org/@anthropic-ai/sdk",
        "name": "Anthropic SDK npm"
    },
    "pypi_sdk": {
        "url": "https://pypi.org/pypi/anthropic/json",
        "name": "Anthropic SDK PyPI"
    },
    "github_sdk_python": {
        "url": "https://github.com/anthropics/anthropic-sdk-python/releases.atom",
        "name": "Python SDK GitHub"
    },
    "github_sdk_typescript": {
        "url": "https://github.com/anthropics/anthropic-sdk-typescript/releases.atom",
        "name": "TypeScript SDK GitHub"
    },

    # Blog & News
    "blog": {
        "url": "https://www.anthropic.com/news",
        "name": "Anthropic Blog"
    },
    "research": {
        "url": "https://www.anthropic.com/research",
        "name": "Anthropic Research"
    },

    # Status
    "status": {
        "url": "https://status.anthropic.com",
        "name": "Anthropic Status"
    },

    # GitHub repos Anthropic
    "github_anthropic": {
        "url": "https://github.com/anthropics",
        "name": "Anthropic GitHub"
    }
}


def load_cache():
    """Charge le cache des updates precedentes."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"seen_hashes": [], "last_check": None, "doc_hashes": {}}


def save_cache(cache):
    """Sauvegarde le cache."""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    cache["last_check"] = datetime.now().isoformat()
    cache["seen_hashes"] = cache["seen_hashes"][-200:]  # Garde 200 hashes
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def get_hash(content):
    """Genere un hash unique pour un contenu."""
    return hashlib.md5(content.encode()).hexdigest()[:16]


def send_telegram(message):
    """Envoie un message Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[TELEGRAM DISABLED] {message[:100]}...")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # Nettoie le message pour eviter les erreurs Markdown
    message = message.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("]", "\\]")
    message = message.replace("\\*", "*").replace("\\_", "_")  # Restore les vrais formatages

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
            # Retry sans Markdown si erreur
            payload["parse_mode"] = None
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"[TELEGRAM] Message envoye (sans formatage)")
                return True
            print(f"[TELEGRAM ERROR] {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")
        return False


def fetch_changelog():
    """Recupere les updates du changelog Anthropic."""
    updates = []
    try:
        response = requests.get(SOURCES["changelog"]["url"], timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        # Cherche TOUS les headers de date
        headers = soup.find_all(["h2", "h3", "h4"])
        for header in headers[:10]:
            text = header.get_text(strip=True)
            if any(month in text for month in ["January", "February", "March", "April",
                "May", "June", "July", "August", "September", "October", "November", "December",
                "2024", "2025", "2026", "2027"]):

                content = ""
                sibling = header.find_next_sibling()
                while sibling and sibling.name not in ["h2", "h3", "h4"]:
                    content += sibling.get_text(strip=True) + " "
                    sibling = sibling.find_next_sibling()
                    if len(content) > 800:
                        break

                updates.append({
                    "source": "API Changelog",
                    "title": text,
                    "summary": content[:400] + "..." if len(content) > 400 else content,
                    "url": SOURCES["changelog"]["url"],
                    "hash": get_hash(text + content[:200])
                })
    except Exception as e:
        print(f"[ERROR] Changelog: {e}")

    print(f"[INFO] Changelog: {len(updates)} entrees")
    return updates


def fetch_github_releases():
    """Recupere les releases de TOUS les repos GitHub Anthropic."""
    updates = []

    github_feeds = [
        ("github_releases", "Claude Code"),
        ("github_sdk_python", "Python SDK"),
        ("github_sdk_typescript", "TypeScript SDK"),
    ]

    for source_key, source_name in github_feeds:
        try:
            feed = feedparser.parse(SOURCES[source_key]["url"])
            for entry in feed.entries[:5]:
                title = entry.get("title", "New Release")
                summary = entry.get("summary", "")[:400]
                # Nettoie le HTML
                summary = re.sub(r'<[^>]+>', '', summary)

                updates.append({
                    "source": source_name,
                    "title": title,
                    "summary": summary,
                    "url": entry.get("link", ""),
                    "hash": get_hash(entry.get("id", title))
                })
        except Exception as e:
            print(f"[ERROR] {source_name}: {e}")

    print(f"[INFO] GitHub: {len(updates)} releases")
    return updates


def fetch_npm_packages():
    """Recupere les versions npm des packages Anthropic."""
    updates = []

    npm_packages = [
        ("npm_sdk", "@anthropic-ai/sdk"),
        ("npm_claude_code", "@anthropic-ai/claude-code"),
    ]

    for source_key, package_name in npm_packages:
        try:
            response = requests.get(SOURCES[source_key]["url"], timeout=15)
            data = response.json()

            # Version latest
            latest = data.get("dist-tags", {}).get("latest", "")
            if latest:
                time = data.get("time", {}).get(latest, "")
                updates.append({
                    "source": f"npm {package_name}",
                    "title": f"v{latest}",
                    "summary": f"Publie le {time[:10] if time else 'N/A'}",
                    "url": f"https://www.npmjs.com/package/{package_name}",
                    "hash": get_hash(f"{package_name}-{latest}")
                })
        except Exception as e:
            print(f"[ERROR] npm {package_name}: {e}")

    print(f"[INFO] npm: {len(updates)} packages")
    return updates


def fetch_pypi_package():
    """Recupere la version PyPI du SDK Python."""
    updates = []
    try:
        response = requests.get(SOURCES["pypi_sdk"]["url"], timeout=15)
        data = response.json()

        version = data.get("info", {}).get("version", "")
        if version:
            updates.append({
                "source": "PyPI anthropic",
                "title": f"v{version}",
                "summary": data.get("info", {}).get("summary", "")[:200],
                "url": "https://pypi.org/project/anthropic/",
                "hash": get_hash(f"anthropic-pypi-{version}")
            })
    except Exception as e:
        print(f"[ERROR] PyPI: {e}")

    print(f"[INFO] PyPI: {len(updates)} packages")
    return updates


def fetch_blog():
    """Recupere TOUS les articles du blog Anthropic."""
    updates = []
    try:
        response = requests.get(SOURCES["blog"]["url"], timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        # Cherche tous les liens d'articles
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)

            # Filtre les articles de news
            if "/news/" in href and len(text) > 15 and text not in ["News", "Read more", "Learn more"]:
                full_url = href if href.startswith("http") else f"https://www.anthropic.com{href}"
                updates.append({
                    "source": "Blog",
                    "title": text[:100],
                    "summary": "",
                    "url": full_url,
                    "hash": get_hash(href)
                })

        # Deduplique
        seen = set()
        unique_updates = []
        for u in updates:
            if u["hash"] not in seen:
                seen.add(u["hash"])
                unique_updates.append(u)
        updates = unique_updates[:10]

    except Exception as e:
        print(f"[ERROR] Blog: {e}")

    print(f"[INFO] Blog: {len(updates)} articles")
    return updates


def fetch_research():
    """Recupere les publications research."""
    updates = []
    try:
        response = requests.get(SOURCES["research"]["url"], timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)

            if "/research/" in href and len(text) > 15:
                full_url = href if href.startswith("http") else f"https://www.anthropic.com{href}"
                updates.append({
                    "source": "Research",
                    "title": text[:100],
                    "summary": "",
                    "url": full_url,
                    "hash": get_hash(href)
                })

        seen = set()
        unique_updates = []
        for u in updates:
            if u["hash"] not in seen:
                seen.add(u["hash"])
                unique_updates.append(u)
        updates = unique_updates[:5]

    except Exception as e:
        print(f"[ERROR] Research: {e}")

    print(f"[INFO] Research: {len(updates)} articles")
    return updates


def fetch_status():
    """Verifie le status d'Anthropic."""
    updates = []
    try:
        response = requests.get(SOURCES["status"]["url"], timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        status_text = soup.get_text().lower()

        # Detecte TOUT probleme
        keywords = ["degraded", "outage", "incident", "maintenance", "investigating",
                    "monitoring", "identified", "update", "resolved"]

        if any(word in status_text for word in keywords[:5]):  # Problemes actifs
            updates.append({
                "source": "Status",
                "title": "Incident en cours sur Anthropic",
                "summary": "Un incident ou maintenance est en cours.",
                "url": SOURCES["status"]["url"],
                "hash": get_hash(f"incident-{datetime.now().strftime('%Y-%m-%d-%H')}")
            })
    except Exception as e:
        print(f"[ERROR] Status: {e}")

    print(f"[INFO] Status: {len(updates)} alertes")
    return updates


def fetch_github_anthropic_repos():
    """Verifie les nouveaux repos GitHub d'Anthropic."""
    updates = []
    try:
        # API GitHub pour lister les repos
        response = requests.get(
            "https://api.github.com/orgs/anthropics/repos?sort=created&per_page=10",
            timeout=15,
            headers={"Accept": "application/vnd.github.v3+json"}
        )
        repos = response.json()

        for repo in repos[:5]:
            if isinstance(repo, dict):
                updates.append({
                    "source": "GitHub Repo",
                    "title": repo.get("name", ""),
                    "summary": repo.get("description", "")[:200] if repo.get("description") else "",
                    "url": repo.get("html_url", ""),
                    "hash": get_hash(f"repo-{repo.get('name', '')}-{repo.get('created_at', '')}")
                })
    except Exception as e:
        print(f"[ERROR] GitHub repos: {e}")

    print(f"[INFO] GitHub repos: {len(updates)} repos")
    return updates


def format_message(update):
    """Formate un message Telegram."""
    emoji = {
        "API Changelog": "🔧",
        "Claude Code": "📦",
        "Python SDK": "🐍",
        "TypeScript SDK": "📘",
        "npm @anthropic-ai/sdk": "📦",
        "npm @anthropic-ai/claude-code": "📦",
        "PyPI anthropic": "🐍",
        "Blog": "📰",
        "Research": "🔬",
        "Status": "⚠️",
        "GitHub Repo": "🆕"
    }

    e = emoji.get(update['source'], '📌')
    title = update['title'][:80] if update['title'] else "N/A"
    summary = update['summary'][:250] if update['summary'] else ""

    msg = f"{e} *CLAUDE UPDATE*\n\n"
    msg += f"🏷 *Source:* {update['source']}\n"
    msg += f"📝 {title}\n"
    if summary:
        msg += f"\n{summary}\n"
    msg += f"\n🔗 {update['url']}\n"
    msg += "━━━━━━━━━━━━━━━━━━"

    return msg


def main():
    print(f"[START] Claude Updates Monitor FULL - {datetime.now().isoformat()}")
    print("=" * 50)

    # Charge le cache
    cache = load_cache()
    seen_hashes = set(cache.get("seen_hashes", []))
    new_hashes = list(seen_hashes)

    # Collecte TOUTES les updates
    all_updates = []

    print("\n[FETCHING] Changelog...")
    all_updates.extend(fetch_changelog())

    print("[FETCHING] GitHub releases...")
    all_updates.extend(fetch_github_releases())

    print("[FETCHING] npm packages...")
    all_updates.extend(fetch_npm_packages())

    print("[FETCHING] PyPI package...")
    all_updates.extend(fetch_pypi_package())

    print("[FETCHING] Blog...")
    all_updates.extend(fetch_blog())

    print("[FETCHING] Research...")
    all_updates.extend(fetch_research())

    print("[FETCHING] Status...")
    all_updates.extend(fetch_status())

    print("[FETCHING] GitHub repos...")
    all_updates.extend(fetch_github_anthropic_repos())

    print(f"\n[TOTAL] {len(all_updates)} updates trouvees")
    print("=" * 50)

    # Filtre les nouvelles updates
    new_updates = []
    for update in all_updates:
        if update["hash"] not in seen_hashes:
            new_updates.append(update)
            new_hashes.append(update["hash"])
            print(f"[NEW] {update['source']}: {update['title'][:50]}")

    print(f"\n[NOUVELLES] {len(new_updates)} nouvelles updates")

    # Envoie les notifications
    if new_updates:
        for update in new_updates[:10]:  # Max 10 notifications
            message = format_message(update)
            send_telegram(message)

        send_telegram(f"✅ *{len(new_updates)} nouvelle(s) update(s) detectee(s)*\n📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    else:
        send_telegram(f"✅ *Check OK* - Aucune nouveaute\n📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # Sauvegarde le cache
    cache["seen_hashes"] = new_hashes
    save_cache(cache)

    print(f"\n[END] Termine - {len(new_updates)} notifications envoyees")


if __name__ == "__main__":
    main()
