"""
scraper.py
==========
WHAT THIS FILE DOES:
Takes a GitHub URL, fetches the README, and extracts the
architecture section. Returns clean text for the extractor.

PSEUDO CODE:
1. Take a GitHub URL like https://github.com/owner/repo
2. Convert it to GitHub API format
3. Try to fetch README.md (or readme.md or README.rst)
4. If rate limited — tell user to add GitHub token
5. Try to find the Architecture section in the README
6. If found return just that section (max 3000 chars)
7. If not found return full README (max 3000 chars)
"""

import os
import re
import requests
from dotenv import load_dotenv
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# ── Fetch README ──────────────────────────────────────────────
def fetch_readme(github_url: str) -> str:
    """
    Fetches README content from a GitHub repo URL.
    Returns raw text string.
    """
    try:
        parts = github_url.rstrip("/").split("github.com/")[-1].split("/")
        owner, repo = parts[0], parts[1]
    except (IndexError, ValueError):
        raise ValueError(f"Invalid GitHub URL: {github_url}")

    headers = {"Accept": "application/vnd.github.raw+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    for filename in ["README.md", "readme.md", "README.rst", "README.txt"]:
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"  README fetched: {filename} ({len(response.text)} chars)")
                return response.text
            elif response.status_code == 403:
                raise ConnectionError("GitHub rate limit hit. Add GITHUB_TOKEN to .env")
            elif response.status_code == 404:
                continue
        except requests.exceptions.Timeout:
            raise ConnectionError("GitHub request timed out")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("No internet connection")

    raise FileNotFoundError(f"No README found in: {github_url}")

# ── Extract Architecture Section ──────────────────────────────
def extract_architecture_section(readme_text: str) -> str:
    """
    Tries to find the Architecture or Components section.
    Falls back to first 3000 chars if not found.
    """
    match = re.search(
        r"#{1,3}\s*(architecture|components|services|system design|system overview)(.*?)(?=\n#{1,3}|\Z)",
        readme_text,
        re.IGNORECASE | re.DOTALL
    )
    if match:
        section = match.group(2).strip()
        print(f"  Architecture section found ({len(section)} chars)")
        return section[:3000]

    print("  No architecture section found — using full README")
    return readme_text[:3000]

# ── Cache README Locally ──────────────────────────────────────
def fetch_readme_cached(github_url: str) -> str:
    """
    Caches README locally so we don't re-fetch during testing.
    Saves to cache/ folder.
    """
    import hashlib
    os.makedirs("cache", exist_ok=True)
    cache_key  = hashlib.md5(github_url.encode()).hexdigest()
    cache_file = f"cache/{cache_key}.txt"

    if os.path.exists(cache_file):
        with open(cache_file, encoding="utf-8") as f:
            print(f"  Using cached README for {github_url}")
            return f.read()

    text = fetch_readme(github_url)
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(text)
    return text

# ── Smoke Test ────────────────────────────────────────────────
if __name__ == "__main__":
    url = "https://github.com/HospitalRun/hospitalrun-frontend"
    try:
        readme = fetch_readme(url)
        section = extract_architecture_section(readme)
        print(f"\nFirst 300 chars of extracted section:\n{section[:300]}")
        print("\n✅ scraper.py working, SAIF did it")
    except Exception as e:
        print(f"  ERROR: {e}")
