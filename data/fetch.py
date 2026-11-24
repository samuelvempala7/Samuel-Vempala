"""Download the four public benchmark files used by the adjacent case studies."""
from hashlib import sha256
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
GITHUB_RAW = "https://raw.githubusercontent.com/"
FILES = {
    "CDNOW_sample.txt": (
        "CamDavidsonPilon/lifetimes/master/lifetimes/datasets/CDNOW_sample.txt",
        "6fae10155c0b0ba363c2c386e30f77990d22328220efd862a5edd1443420d94a",
    ),
    "SouthGermanCredit.asc": (
        "iancovert/sage/master/data/SouthGermanCredit.asc",
        "5f363343f356ca38a0236baab849e472846399b2176ccc5bd686483dd8a7562f",
    ),
    "train.csv": (
        "PolyAI-LDN/task-specific-datasets/master/banking_data/train.csv",
        "b06e26ac675513959a63135f11b94ea7786ed02da65db93a5650d8838cbc664b",
    ),
    "test.csv": (
        "PolyAI-LDN/task-specific-datasets/master/banking_data/test.csv",
        "d12d6e3bc4c3103966ae786dc435913c0c563dfa328f5a3646d0e62cfeeb474d",
    ),
}


def main():
    for name, (path, expected) in FILES.items():
        dest = ROOT / name
        if dest.is_file() and sha256(dest.read_bytes()).hexdigest() == expected:
            print(f"Verified {name}")
            continue
        with urlopen(GITHUB_RAW + path, timeout=40) as response:
            body = response.read()
        if sha256(body).hexdigest() != expected:
            raise ValueError(f"{name} differs from the edition used for these results")
        dest.write_bytes(body)
        print(f"Downloaded {name}")


if __name__ == "__main__":
    main()
