"""
download_data.py
------------------
Automatically downloads the 4 category JSON files (with real dates)
directly into the raw_data_v2 folder - no manual browser downloading
or moving files needed.

Run:
    python download_data.py

This may take a while for Electronics (it's the largest file, a few
hundred MB compressed). Progress is printed as it downloads.
"""

import urllib.request
import ssl
from pathlib import Path

RAW_DATA_DIR = Path("raw_data_v2")
RAW_DATA_DIR.mkdir(exist_ok=True)

FILES = {
    "AMAZON_FASHION_5.json.gz": "https://jmcauley.ucsd.edu/data/amazon_v2/categoryFilesSmall/AMAZON_FASHION_5.json.gz",
    "Digital_Music_5.json.gz": "https://jmcauley.ucsd.edu/data/amazon_v2/categoryFilesSmall/Digital_Music_5.json.gz",
    "Arts_Crafts_and_Sewing_5.json.gz": "https://jmcauley.ucsd.edu/data/amazon_v2/categoryFilesSmall/Arts_Crafts_and_Sewing_5.json.gz",
    "Electronics_5.json.gz": "https://jmcauley.ucsd.edu/data/amazon_v2/categoryFilesSmall/Electronics_5.json.gz",
}

# Some university servers need SSL verification relaxed to work from
# ordinary home computers/networks.
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE


def download_with_progress(url, dest_path):
    def report(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            pct = min(downloaded / total_size * 100, 100)
            mb_done = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            print(f"\r  {pct:5.1f}%  ({mb_done:,.1f} MB / {mb_total:,.1f} MB)", end="", flush=True)

    opener = urllib.request.build_opener()
    urllib.request.install_opener(opener)

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=context) as response:
        total_size = int(response.headers.get("Content-Length", 0))
        block_size = 1024 * 64
        downloaded = 0
        with open(dest_path, "wb") as out_file:
            while True:
                chunk = response.read(block_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    pct = min(downloaded / total_size * 100, 100)
                    mb_done = downloaded / (1024 * 1024)
                    mb_total = total_size / (1024 * 1024)
                    print(f"\r  {pct:5.1f}%  ({mb_done:,.1f} MB / {mb_total:,.1f} MB)", end="", flush=True)
    print()


def main():
    print("=" * 70)
    print("LUMINA - DOWNLOADING REAL REVIEW DATA (WITH DATES)")
    print("=" * 70)

    for filename, url in FILES.items():
        dest = RAW_DATA_DIR / filename

        if dest.exists():
            print(f"\n{filename} already exists - skipping.")
            continue

        print(f"\nDownloading {filename} ...")
        try:
            download_with_progress(url, dest)
            print(f"  Saved to {dest}")
        except Exception as e:
            print(f"\n  [ERROR] Failed to download {filename}: {e}")
            print("  You can also download it manually from:")
            print(f"  {url}")

    print("\n" + "=" * 70)
    print("DOWNLOAD COMPLETE")
    print("=" * 70)
    print(f"Files saved in: {RAW_DATA_DIR.resolve()}")
    print("\nNext step:")
    print("  python load_reviews_v2.py")


if __name__ == "__main__":
    main()