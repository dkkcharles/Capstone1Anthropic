"""
fetch.py

Downloads every file this project uses from the primary source, the
Anthropic/EconomicIndex dataset on Hugging Face, pinned to one commit
(HF_REVISION in releases.py) so re-running always gets identical bytes.

  data/<csv>                    -- the eight release CSVs listed in releases.py
  data/docs/<release>_data_documentation.md
  data/reference/onet_task_statements_raw.xlsx  (task -> O*NET-SOC code)

Each CSV is checked against the sha256 recorded below. data/ is git-ignored;
only this script is committed.

Run from the repo root:  python src/fetch.py
Requires: pip install huggingface_hub
"""

import hashlib
import shutil
from pathlib import Path

from huggingface_hub import hf_hub_download

from releases import DATA_DIR, HF_REPO, HF_REVISION, RELEASES

# sha256 of each CSV at HF_REVISION (matches the Hugging Face LFS oid).
SHA256 = {
    "aei_raw_1p_api_2025-08-04_to_2025-08-11.csv": "c0fc061ea7d4feb71a7bd88c528d54e2d3a11e2045574f1e1fb2d594eebffd0f",
    "aei_raw_claude_ai_2025-08-04_to_2025-08-11.csv": "c8ef9c5eee0c42febc73e358ecc7d2358e0a0ce3b50122c0c15ae8ec569aceff",
    "aei_raw_1p_api_2025-11-13_to_2025-11-20.csv": "432f8d14348ba384dd9c659fa7fdc85754cbae3b5a480c14a344ac4823d0e861",
    "aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv": "70dc16780061b84d3f34ddf7fe5c978d65c99a5ef58afd78f9315f886a6a5873",
    "aei_raw_1p_api_2026-02-05_to_2026-02-12.csv": "b3bcd68e7f6d820ffbb50a3c53d71ec2a122556fc2a38226cd86951a054bd4c8",
    "aei_raw_claude_ai_2026-02-05_to_2026-02-12.csv": "69ebf6f9afc1e3be45caab172a84ae09e78bf41b97e1c310100d81c8a35a7433",
    "aei_1p_api_2026-06-26.csv": "62197f003e001945ad130c2f26f5e07f3fda45ff41644df91444b04fd524a19f",
    "aei_claude_ai_2026-06-26.csv": "f974b358bce0e5a8417510c61da4342234cd0de9d9d0b62acf4c6dbcf8ec7b68",
}

DOCS_DIR = DATA_DIR / "docs"
REFERENCE_DIR = DATA_DIR / "reference"
ONET_TASKS = "release_2025_09_15/data/input/onet_task_statements_raw.xlsx"


def resolve_url(repo_path: str) -> str:
    """Permanent link to the pinned file (record these, not /blob/main/ links)."""
    return f"https://huggingface.co/datasets/{HF_REPO}/resolve/{HF_REVISION}/{repo_path}"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(repo_path: str, dest: Path, force: bool = False) -> Path:
    """Fetch one file at HF_REVISION into dest (skipped if already there)."""
    if dest.exists() and not force:
        print(f"  exists   {dest}")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    cached = hf_hub_download(HF_REPO, repo_path, repo_type="dataset", revision=HF_REVISION)
    shutil.copyfile(cached, dest)
    print(f"  fetched  {dest}")
    return dest


def main():
    print(f"{HF_REPO} @ {HF_REVISION}\n")
    bad = []

    for release in RELEASES:
        print(f"Release {release['release']}")
        for path in release["files"].values():
            repo_path = f"{release['hf_dir']}/{path.name}"
            download(repo_path, path)
            ok = sha256(path) == SHA256[path.name]
            print(f"  sha256   {'OK' if ok else 'MISMATCH'}  {resolve_url(repo_path)}")
            if not ok:
                bad.append(path)

        folder = release["hf_dir"].split("/")[0]
        download(f"{folder}/data_documentation.md",
                 DOCS_DIR / f"{folder}_data_documentation.md")

    print("\nReference")
    download(ONET_TASKS, REFERENCE_DIR / Path(ONET_TASKS).name)

    if bad:
        raise SystemExit(f"\n{len(bad)} file(s) do not match the pinned checksum: {bad}. "
                         f"Delete them and re-run.")
    print("\nAll CSVs match the pinned checksums.")


if __name__ == "__main__":
    main()
