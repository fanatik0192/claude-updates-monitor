#!/usr/bin/env python3
"""
Claude Updates Monitor - VERSION COMPLETE (FR)
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
    print("Installation des dependances...")
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
        "name": "Journal des modifications API"
    },
    "docs_api": {
        "url": "https://docs.anthropic.com/en/api",
        "name": "Documentation API"
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

    # SDK & Bibliotheques
    "npm_sdk": {
        "url": "https://registry.npmjs.org/@anthropic-ai/sdk",
        "name": "SDK Anthropic npm"
    },
    "pypi_sdk": {
        "url": "https://pypi.org/pypi/anthropic/json",
        "name": "SDK Anthropic PyPI"
    },
    "github_sdk_python": {
        "url": "https://github.com/anthropics/anthropic-sdk-python/releases.atom",
        "name": "SDK Python GitHub"
    },
    "github_sdk_typescript": {
        "url": "https://github.com/anthropics/anthropic-sdk-typescript/releases.atom",
        "name": "SDK TypeScript GitHub"
    },

    # Blog & Actualites
    "blog": {
        "url": "https://www.anthropic.com/news",
        "name": "Blog Anthropic"
    },
    "research": {
        "url": "https://www.anthropic.com/research",
        "name": "Recherche Anthropic"
    },

    # Statut
    "status": {
        "url": "https://status.anthropic.com",
        "name": "Statut Anthropic"
    },

    # Depots GitHub Anthropic
    "github_anthropic": {
        "url": "https://github.com/anthropics",
        "name": "GitHub Anthropic"
    }
}


def load_cache():
    """Charge le cache des mises a jour precedentes."""
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
    cache["seen_hashes"] = cache["seen_hashes"][-200:]
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def get_hash(content):
    """Genere un hash unique pour un contenu."""
    return hashlib.md5(content.encode()).hexdigest()[:16]


def send_telegram(message):
    """Envoie un message Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[TELEGRAM DESACTIVE] {message[:100]}...")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # Nettoie le message pour eviter les erreurs Markdown
    message = message.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("]", "\\]")
    message = message.replace("\\*", "*").replace("\\_", "_")

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"[TELEGRAM] Message envoye !")
            return True
        else:
            payload["parse_mode"] = None
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"[TELEGRAM] Message envoye (sans formatage)")
                return True
            print(f"[ERREUR TELEGRAM] {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"[ERREUR TELEGRAM] {e}")
        return False


def fetch_changelog():
    """Recupere les mises a jour du changelog Anthropic."""
    updates = []
    try:
        response = requests.get(SOURCES["changelog"]["url"], timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

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
                    "source": "Journal API",
                    "title": text,
                    "summary": content[:400] + "..." if len(content) > 400 else content,
                    "url": SOURCES["changelog"]["url"],
                    "hash": get_hash(text + content[:200])
                })
    except Exception as e:
        print(f"[ERREUR] Changelog: {e}")

    print(f"[INFO] Changelog: {len(updates)} entrees")
    return updates


def fetch_github_releases():
    """Recupere les versions de TOUS les depots GitHub Anthropic."""
    updates = []

    github_feeds = [
        ("github_releases", "Claude Code"),
        ("github_sdk_python", "SDK Python"),
        ("github_sdk_typescript", "SDK TypeScript"),
    ]

    for source_key, source_name in github_feeds:
        try:
            feed = feedparser.parse(SOURCES[source_key]["url"])
            for entry in feed.entries[:5]:
                title = entry.get("title", "Nouvelle version")
                summary = entry.get("summary", "")[:400]
                summary = re.sub(r'<[^>]+>', '', summary)

                updates.append({
                    "source": source_name,
                    "title": title,
                    "summary": summary,
                    "url": entry.get("link", ""),
                    "hash": get_hash(entry.get("id", title))
                })
        except Exception as e:
            print(f"[ERREUR] {source_name}: {e}")

    print(f"[INFO] GitHub: {len(updates)} versions")
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
            print(f"[ERREUR] npm {package_name}: {e}")

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
        print(f"[ERREUR] PyPI: {e}")

    print(f"[INFO] PyPI: {len(updates)} packages")
    return updates


def fetch_blog():
    """Recupere TOUS les articles du blog Anthropic."""
    updates = []
    try:
        response = requests.get(SOURCES["blog"]["url"], timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)

            if "/news/" in href and len(text) > 15 and text not in ["News", "Read more", "Learn more"]:
                full_url = href if href.startswith("http") else f"https://www.anthropic.com{href}"
                updates.append({
                    "source": "Blog",
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
        updates = unique_updates[:10]

    except Exception as e:
        print(f"[ERREUR] Blog: {e}")

    print(f"[INFO] Blog: {len(updates)} articles")
    return updates


def fetch_research():
    """Recupere les publications de recherche."""
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
                    "source": "Recherche",
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
        print(f"[ERREUR] Recherche: {e}")

    print(f"[INFO] Recherche: {len(updates)} articles")
    return updates


def fetch_status():
    """Verifie le statut d'Anthropic."""
    updates = []
    try:
        response = requests.get(SOURCES["status"]["url"], timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        status_text = soup.get_text().lower()

        keywords = ["degraded", "outage", "incident", "maintenance", "investigating",
                    "monitoring", "identified", "update", "resolved"]

        if any(word in status_text for word in keywords[:5]):
            updates.append({
                "source": "Statut",
                "title": "Incident en cours sur Anthropic",
                "summary": "Un incident ou une maintenance est en cours.",
                "url": SOURCES["status"]["url"],
                "hash": get_hash(f"incident-{datetime.now().strftime('%Y-%m-%d-%H')}")
            })
    except Exception as e:
        print(f"[ERREUR] Statut: {e}")

    print(f"[INFO] Statut: {len(updates)} alertes")
    return updates


def fetch_github_anthropic_repos():
    """Verifie les nouveaux depots GitHub d'Anthropic."""
    updates = []
    try:
        response = requests.get(
            "https://api.github.com/orgs/anthropics/repos?sort=created&per_page=10",
            timeout=15,
            headers={"Accept": "application/vnd.github.v3+json"}
        )
        repos = response.json()

        for repo in repos[:5]:
            if isinstance(repo, dict):
                updates.append({
                    "source": "Nouveau Depot",
                    "title": repo.get("name", ""),
                    "summary": repo.get("description", "")[:200] if repo.get("description") else "",
                    "url": repo.get("html_url", ""),
                    "hash": get_hash(f"repo-{repo.get('name', '')}-{repo.get('created_at', '')}")
                })
    except Exception as e:
        print(f"[ERREUR] Depots GitHub: {e}")

    print(f"[INFO] Depots GitHub: {len(updates)} depots")
    return updates


def format_message(update):
    """Formate un message Telegram."""
    emoji = {
        "Journal API": "🔧",
        "Claude Code": "📦",
        "SDK Python": "🐍",
        "SDK TypeScript": "📘",
        "npm @anthropic-ai/sdk": "📦",
        "npm @anthropic-ai/claude-code": "📦",
        "PyPI anthropic": "🐍",
        "Blog": "📰",
        "Recherche": "🔬",
        "Statut": "⚠️",
        "Nouveau Depot": "🆕"
    }

    e = emoji.get(update['source'], '📌')
    title = update['title'][:80] if update['title'] else "N/A"
    summary = update['summary'][:250] if update['summary'] else ""

    msg = f"{e} *MISE A JOUR CLAUDE*\n\n"
    msg += f"🏷 *Source :* {update['source']}\n"
    msg += f"📝 {title}\n"
    if summary:
        msg += f"\n{summary}\n"
    msg += f"\n🔗 {update['url']}\n"
    msg += "━━━━━━━━━━━━━━━━━━"

    return msg


def generate_daily_report(all_updates, new_updates, versions, cache):
    """Genere le rapport quotidien complet."""

    now = datetime.now()
    previous_versions = cache.get("versions", {})

    # En-tete du rapport
    report = f"""
📊 *RAPPORT QUOTIDIEN CLAUDE*
📅 {now.strftime('%d/%m/%Y a %H:%M')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

    # Statut global
    if new_updates:
        report += f"🔔 *{len(new_updates)} NOUVEAUTE(S) DETECTEE(S)*\n\n"
    else:
        report += "✅ *AUCUNE NOUVEAUTE*\n\n"

    # Tableau des versions actuelles
    report += "📦 *VERSIONS ACTUELLES*\n"
    report += "```\n"

    version_items = [
        ("Claude Code npm", versions.get("claude_code_npm", "?")),
        ("Claude Code GitHub", versions.get("claude_code_github", "?")),
        ("SDK Python (PyPI)", versions.get("sdk_python", "?")),
        ("SDK TypeScript", versions.get("sdk_typescript", "?")),
        ("SDK npm", versions.get("sdk_npm", "?")),
    ]

    for name, version in version_items:
        prev = previous_versions.get(name, version)
        if prev != version and prev != "?":
            indicator = "🆕"
        else:
            indicator = "  "
        report += f"{indicator} {name}: {version}\n"

    report += "```\n\n"

    # Resume par source
    report += "📋 *RESUME PAR SOURCE*\n"
    report += "```\n"

    source_counts = {}
    source_new = {}
    for u in all_updates:
        src = u["source"]
        source_counts[src] = source_counts.get(src, 0) + 1
    for u in new_updates:
        src = u["source"]
        source_new[src] = source_new.get(src, 0) + 1

    sources_order = [
        ("Journal API", "Journal API"),
        ("Claude Code", "Claude Code"),
        ("SDK Python", "SDK Python"),
        ("SDK TypeScript", "SDK TypeScript"),
        ("npm @anthropic-ai/sdk", "SDK npm"),
        ("npm @anthropic-ai/claude-code", "Claude Code npm"),
        ("PyPI anthropic", "SDK PyPI"),
        ("Blog", "Blog"),
        ("Recherche", "Recherche"),
        ("Statut", "Statut"),
        ("Nouveau Depot", "Nouveaux depots")
    ]

    for src, label in sources_order:
        total = source_counts.get(src, 0)
        new = source_new.get(src, 0)
        if total > 0:
            if new > 0:
                report += f"🔴 {label}: +{new} nouveau\n"
            else:
                report += f"⚪ {label}: OK\n"

    report += "```\n\n"

    # Liste des nouveautes
    if new_updates:
        report += "🆕 *NOUVEAUTES DETECTEES*\n\n"
        for i, update in enumerate(new_updates[:8], 1):
            title = update['title'][:50] + "..." if len(update['title']) > 50 else update['title']
            report += f"{i}. *{update['source']}*\n"
            report += f"   {title}\n"
            report += f"   🔗 {update['url'][:50]}...\n\n"

    # Pied de page
    report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    report += f"⏰ Prochain check : demain 20h\n"
    report += f"📡 Sources : {len(SOURCES)} actives"

    return report


def main():
    print(f"[DEMARRAGE] Claude Updates Monitor - {datetime.now().isoformat()}")
    print("=" * 50)

    # Charge le cache
    cache = load_cache()
    seen_hashes = set(cache.get("seen_hashes", []))
    new_hashes = list(seen_hashes)

    # Dictionnaire pour stocker les versions actuelles
    versions = {}

    # Collecte TOUTES les mises a jour
    all_updates = []

    print("\n[RECUPERATION] Journal des modifications...")
    all_updates.extend(fetch_changelog())

    print("[RECUPERATION] Versions GitHub...")
    github_updates = fetch_github_releases()
    all_updates.extend(github_updates)
    for u in github_updates:
        if u["source"] == "Claude Code":
            versions["claude_code_github"] = u["title"][:20]
        elif u["source"] == "SDK Python":
            versions["sdk_python_github"] = u["title"][:20]
        elif u["source"] == "SDK TypeScript":
            versions["sdk_typescript"] = u["title"][:20]

    print("[RECUPERATION] Packages npm...")
    npm_updates = fetch_npm_packages()
    all_updates.extend(npm_updates)
    for u in npm_updates:
        if "claude-code" in u["source"]:
            versions["claude_code_npm"] = u["title"]
        elif "sdk" in u["source"]:
            versions["sdk_npm"] = u["title"]

    print("[RECUPERATION] Package PyPI...")
    pypi_updates = fetch_pypi_package()
    all_updates.extend(pypi_updates)
    for u in pypi_updates:
        versions["sdk_python"] = u["title"]

    print("[RECUPERATION] Blog...")
    all_updates.extend(fetch_blog())

    print("[RECUPERATION] Recherche...")
    all_updates.extend(fetch_research())

    print("[RECUPERATION] Statut...")
    all_updates.extend(fetch_status())

    print("[RECUPERATION] Depots GitHub...")
    all_updates.extend(fetch_github_anthropic_repos())

    print(f"\n[TOTAL] {len(all_updates)} elements trouves")
    print("=" * 50)

    # Filtre les nouvelles mises a jour
    new_updates = []
    for update in all_updates:
        if update["hash"] not in seen_hashes:
            new_updates.append(update)
            new_hashes.append(update["hash"])
            print(f"[NOUVEAU] {update['source']}: {update['title'][:50]}")

    print(f"\n[NOUVEAUTES] {len(new_updates)} nouvelles mises a jour")

    # Genere et envoie le rapport quotidien
    report = generate_daily_report(all_updates, new_updates, versions, cache)
    send_telegram(report)

    # Si nouvelles mises a jour, envoie aussi les details individuels
    if new_updates:
        for update in new_updates[:5]:
            message = format_message(update)
            send_telegram(message)

    # Sauvegarde le cache avec les versions
    cache["seen_hashes"] = new_hashes
    cache["versions"] = versions
    save_cache(cache)

    print(f"\n[FIN] Termine - {len(new_updates)} notifications envoyees")


if __name__ == "__main__":
    main()
