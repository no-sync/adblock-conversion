from pathlib import Path
import requests
import re

BLACKLIST_URLS = Path("sources/blacklist_urls.txt")
WHITELIST_URLS = Path("sources/whitelist_urls.txt")

OUTPUT = Path("output/blacklist-mihomo.yaml")
OUTPUT.parent.mkdir(exist_ok=True)

DOMAIN_RE = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$",
    re.I
)

def read_urls(file):
    if not file.exists():
        return []

    urls = []

    for line in file.read_text().splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        urls.append(line)

    return urls


def extract_domain(line):
    line = line.strip().lower()

    if not line:
        return None

    if line.startswith("#"):
        return None

    if "#" in line:
        line = line.split("#", 1)[0].strip()

    if not line:
        return None

    parts = line.split()

    candidate = parts[-1]

    if candidate.startswith("*."):
        candidate = candidate[2:]

    candidate = candidate.rstrip(".")

    if DOMAIN_RE.match(candidate):
        return candidate

    return None


def download_domains(urls):
    domains = set()

    for url in urls:
        print("Downloading:", url)

        try:
            r = requests.get(url, timeout=120)
            r.raise_for_status()
        except Exception as e:
            print("Failed:", e)
            continue

        for line in r.text.splitlines():
            domain = extract_domain(line)

            if domain:
                domains.add(domain)

    return domains


def whitelisted(domain, whitelist):
    current = domain

    while True:
        if current in whitelist:
            return True

        if "." not in current:
            return False

        current = current.split(".", 1)[1]


blacklist = download_domains(
    read_urls(BLACKLIST_URLS)
)

whitelist = download_domains(
    read_urls(WHITELIST_URLS)
)

result = {
    d
    for d in blacklist
    if not whitelisted(d, whitelist)
}

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("payload:\n")

    for domain in sorted(result):
        f.write(f"  - {domain}\n")

print("Blacklist:", len(blacklist))
print("Whitelist:", len(whitelist))
print("Final:", len(result))
