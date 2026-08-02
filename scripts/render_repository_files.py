#!/usr/bin/env python3

import argparse
import base64
import configparser
import html
import json
import re
import shutil
from pathlib import Path


APP_ID = "io.github.vincentzyuapps.dartflutterdemo"
BRANCH = "stable"
ARCH = "x86_64"
PAGES_URL = "https://vincentzyuapps.github.io/flatpak-repo"
REPOSITORY_URL = f"{PAGES_URL}/repo/"
SOURCE_URL = "https://github.com/VincentZyuApps/dart-flutter-demo"
RUNTIME_REPO_URL = "https://dl.flathub.org/repo/flathub.flatpakrepo"
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[.-][0-9A-Za-z]+)*$")
FINGERPRINT_PATTERN = re.compile(r"^[0-9A-F]{40}$")


def decode_armored_public_key(content: str) -> bytes:
    lines = content.splitlines()
    try:
        start = lines.index("-----BEGIN PGP PUBLIC KEY BLOCK-----")
        end = lines.index("-----END PGP PUBLIC KEY BLOCK-----")
    except ValueError as error:
        raise ValueError("invalid armored public key") from error

    payload_started = False
    payload: list[str] = []
    for line in lines[start + 1 : end]:
        stripped = line.strip()
        if not payload_started:
            if not stripped:
                payload_started = True
            continue
        if stripped and not stripped.startswith("="):
            payload.append(stripped)

    if not payload:
        raise ValueError("armored public key has no payload")
    try:
        decoded = base64.b64decode("".join(payload), validate=True)
    except ValueError as error:
        raise ValueError("armored public key payload is invalid") from error
    if not decoded or decoded[0] & 0x80 == 0:
        raise ValueError("decoded OpenPGP key is invalid")
    return decoded


def write_key_file(path: Path, section: str, values: dict[str, str]) -> None:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    parser[section] = values
    with path.open("w", encoding="utf-8", newline="\n") as output:
        parser.write(output, space_around_delimiters=False)


def render_repository_files(
    output_directory: Path,
    version: str,
    public_key_path: Path,
    fingerprint: str,
) -> None:
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"invalid release version: {version}")
    if not FINGERPRINT_PATTERN.fullmatch(fingerprint):
        raise ValueError("fingerprint must contain 40 uppercase hexadecimal characters")

    armored_key = public_key_path.read_text(encoding="ascii")
    encoded_key = base64.b64encode(
        decode_armored_public_key(armored_key)
    ).decode("ascii")
    output_directory.mkdir(parents=True, exist_ok=True)

    write_key_file(
        output_directory / "dart-flutter-demo.flatpakrepo",
        "Flatpak Repo",
        {
            "Title": "dart-flutter-demo",
            "Url": REPOSITORY_URL,
            "Homepage": SOURCE_URL,
            "Comment": "Signed stable Flatpak repository",
            "Description": "Self-hosted Flatpak updates for dart-flutter-demo",
            "DefaultBranch": BRANCH,
            "GPGKey": encoded_key,
        },
    )
    write_key_file(
        output_directory / "dart-flutter-demo.flatpakref",
        "Flatpak Ref",
        {
            "Title": "dart-flutter-demo",
            "Name": APP_ID,
            "Branch": BRANCH,
            "Url": REPOSITORY_URL,
            "IsRuntime": "false",
            "RuntimeRepo": RUNTIME_REPO_URL,
            "GPGKey": encoded_key,
        },
    )

    public_key_output = output_directory / "flatpak-repo-signing-public.asc"
    shutil.copyfile(public_key_path, public_key_output)
    (output_directory / ".nojekyll").write_text("", encoding="ascii")
    (output_directory / "repository.json").write_text(
        json.dumps(
            {
                "app_id": APP_ID,
                "arch": ARCH,
                "branch": BRANCH,
                "fingerprint": fingerprint,
                "repository_url": REPOSITORY_URL,
                "source_url": SOURCE_URL,
                "version": version,
            },
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="ascii",
    )

    safe_version = html.escape(version)
    safe_fingerprint = html.escape(fingerprint)
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>dart-flutter-demo Flatpak Repository</title>
  <style>
    :root {{ color-scheme: light dark; font-family: system-ui, sans-serif; }}
    body {{ margin: 0; line-height: 1.55; }}
    header, main, footer {{ max-width: 880px; margin: 0 auto; padding: 24px; }}
    header {{ display: flex; align-items: center; gap: 18px; border-bottom: 1px solid #7776; }}
    header img {{ width: 72px; height: 72px; }}
    h1 {{ margin: 0; font-size: 28px; letter-spacing: 0; }}
    h2 {{ margin-top: 30px; font-size: 20px; letter-spacing: 0; }}
    code {{ overflow-wrap: anywhere; }}
    pre {{ padding: 14px; overflow-x: auto; border-left: 4px solid #2f9d66; background: #7771; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 8px 10px; text-align: left; border-bottom: 1px solid #7775; }}
    a {{ color: #168052; }}
  </style>
</head>
<body>
  <header>
    <img src="https://raw.githubusercontent.com/VincentZyuApps/dart-flutter-demo/main/assets/icons/linux/app_icon_128.png" alt="dart-flutter-demo icon">
    <div>
      <h1>dart-flutter-demo</h1>
      <div>Signed Flatpak repository</div>
    </div>
  </header>
  <main>
    <table>
      <tr><th>Version</th><td>{safe_version}</td></tr>
      <tr><th>Channel</th><td>{BRANCH}</td></tr>
      <tr><th>Architecture</th><td>{ARCH}</td></tr>
      <tr><th>GPG fingerprint</th><td><code>{safe_fingerprint}</code></td></tr>
    </table>
    <h2>Install</h2>
    <pre><code>flatpak install --user {PAGES_URL}/dart-flutter-demo.flatpakref</code></pre>
    <h2>Update</h2>
    <pre><code>flatpak update --user {APP_ID}</code></pre>
    <p><a href="dart-flutter-demo.flatpakref">Flatpak reference</a> · <a href="dart-flutter-demo.flatpakrepo">Repository descriptor</a> · <a href="repository.json">Repository metadata</a> · <a href="{SOURCE_URL}">Source code</a></p>
  </main>
  <footer>Generated from the signed stable repository.</footer>
</body>
</html>
"""
    (output_directory / "index.html").write_text(page, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--public-key", type=Path, required=True)
    parser.add_argument("--fingerprint", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    render_repository_files(
        args.output_directory,
        args.version,
        args.public_key,
        args.fingerprint,
    )


if __name__ == "__main__":
    main()
