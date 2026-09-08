#!/usr/bin/env python3
"""Convert dnsmasq-china-list domains into a Loon Host plugin."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path


LINE_RE = re.compile(r"server=/([^/]+)/[^/]+")
DOH = "https://dns.alidns.com/dns-query"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def load_domains(source: Path) -> tuple[list[str], str]:
    data = source.read_bytes()
    domains: set[str] = set()

    for line_number, raw_line in enumerate(data.decode("utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = LINE_RE.fullmatch(line)
        if not match:
            raise ValueError(f"unsupported source line {line_number}: {line!r}")
        domain = match.group(1).lower().rstrip(".")
        if not domain or any(char.isspace() for char in domain):
            raise ValueError(f"invalid domain on source line {line_number}: {domain!r}")
        domains.add(domain)

    if len(domains) < 100_000:
        raise ValueError(f"source contains only {len(domains)} domains; refusing to replace output")

    return sorted(domains), hashlib.sha256(data).hexdigest()


def render(domains: list[str], source_sha256: str) -> str:
    lines = [
        "#!name = 国内域名阿里 DoH 映射",
        "#!desc = 将 dnsmasq-china-list 的国内域名交给阿里 DoH 解析。",
        "# Source: https://github.com/felixonmars/dnsmasq-china-list",
        f"# Source-SHA256: {source_sha256}",
        "[Host]",
    ]
    for domain in domains:
        lines.append(f"{domain} = server:{DOH}")
        lines.append(f"*.{domain} = server:{DOH}")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    domains, source_sha256 = load_domains(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(render(domains, source_sha256), encoding="utf-8")
    temporary.replace(args.output)
    print(f"generated {args.output} from {len(domains)} domains")


if __name__ == "__main__":
    main()
