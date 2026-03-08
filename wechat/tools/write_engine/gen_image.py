#!/usr/bin/env python3
"""Generate or search images for WeChat articles.

Primary: Gemini API image generation
Fallback: Wikimedia Commons search (CC-licensed photos)

Usage:
    python gen_image.py --prompt "描述" --output path/to/output.png
    python gen_image.py --prompt "描述" --output path/to/output.png --aspect 16:9
    python gen_image.py --prompt "描述" --output path/to/output.png --source wikimedia
    python gen_image.py --search "Go board game stones" --output path/to/output.jpg
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path


def load_api_key():
    """Load Gemini API key from .env file."""
    env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("GEMINI_API_KEY")


def generate_gemini(prompt: str, output_path: str, aspect: str = "16:9") -> bool:
    """Generate an image using Gemini 2.0 Flash. Returns True on success."""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("  Gemini SDK not installed, skipping", file=sys.stderr)
        return False

    api_key = load_api_key()
    if not api_key:
        print("  GEMINI_API_KEY not found, skipping", file=sys.stderr)
        return False

    client = genai.Client(api_key=api_key)
    aspect_hint = f"Image aspect ratio: {aspect}."
    full_prompt = f"{prompt}\n{aspect_hint}"

    print(f"  [Gemini] Generating...")

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            )
        )
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            print(f"  [Gemini] Quota exhausted, falling back", file=sys.stderr)
        else:
            print(f"  [Gemini] Error: {err_str[:200]}", file=sys.stderr)
        return False

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(part.inline_data.data)
            size_kb = len(part.inline_data.data) // 1024
            print(f"  [Gemini] Saved: {output_path} ({size_kb}KB)")
            return True
        elif part.text is not None:
            print(f"  [Gemini] {part.text[:200]}")

    print("  [Gemini] No image in response", file=sys.stderr)
    return False


def search_wikimedia(query: str, output_path: str, min_width: int = 800,
                     orientation: str = "any") -> bool:
    """Search Wikimedia Commons for CC-licensed photos. Returns True on success."""
    print(f"  [Wikimedia] Searching: {query}")
    headers = {"User-Agent": "NuwaBot/1.0 (nuwa-project; research)"}

    # Search for files
    search_url = (
        "https://commons.wikimedia.org/w/api.php?"
        f"action=query&list=search&srnamespace=6"
        f"&srsearch={urllib.parse.quote(query)}&srlimit=10&format=json"
    )
    req = urllib.request.Request(search_url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
    except Exception as e:
        print(f"  [Wikimedia] Search failed: {e}", file=sys.stderr)
        return False

    results = data.get("query", {}).get("search", [])
    candidates = [r["title"] for r in results
                  if r["title"].endswith((".jpg", ".png", ".jpeg"))]

    if not candidates:
        print("  [Wikimedia] No image results found", file=sys.stderr)
        return False

    # Get image info for candidates, pick best one
    for title in candidates[:5]:
        encoded = urllib.parse.quote(title)
        info_url = (
            f"https://commons.wikimedia.org/w/api.php?"
            f"action=query&titles={encoded}"
            f"&prop=imageinfo&iiprop=url|size&iiurlwidth=1280&format=json"
        )
        req = urllib.request.Request(info_url, headers=headers)
        try:
            resp = urllib.request.urlopen(req, timeout=15)
            info_data = json.loads(resp.read())
        except Exception:
            continue

        pages = info_data.get("query", {}).get("pages", {})
        for pid, page in pages.items():
            if "imageinfo" not in page:
                continue
            img_info = page["imageinfo"][0]
            w, h = img_info["width"], img_info["height"]

            if w < min_width:
                continue

            # Check orientation preference
            if orientation == "landscape" and h > w:
                continue
            if orientation == "portrait" and w > h:
                continue

            # Download thumbnail (1280px, standard Wikimedia step)
            thumb_url = img_info.get("thumburl", img_info["url"])
            print(f"  [Wikimedia] Found: {title} ({w}x{h})")
            print(f"  [Wikimedia] Downloading: {thumb_url[:80]}...")

            req = urllib.request.Request(thumb_url, headers=headers)
            try:
                img_data = urllib.request.urlopen(req, timeout=30).read()
            except Exception as e:
                print(f"  [Wikimedia] Download failed: {e}", file=sys.stderr)
                time.sleep(2)
                continue

            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(img_data)
            print(f"  [Wikimedia] Saved: {output_path} ({len(img_data)//1024}KB)")
            return True

        time.sleep(1)  # Rate limit between API calls

    print("  [Wikimedia] No suitable image found", file=sys.stderr)
    return False


def generate_image(prompt: str, output_path: str, aspect: str = "16:9",
                   source: str = "auto", search_query: str = None):
    """Generate or find an image with fallback chain.

    source: "gemini", "wikimedia", or "auto" (try Gemini first, then Wikimedia)
    search_query: override Wikimedia search terms (default: extract from prompt)
    """
    print(f"Prompt: {prompt[:100]}...")

    if source in ("gemini", "auto"):
        if generate_gemini(prompt, output_path, aspect):
            return

    if source in ("wikimedia", "auto"):
        query = search_query or prompt
        orientation = "landscape" if ":" in aspect else "any"
        if search_wikimedia(query, output_path, orientation=orientation):
            return

    print("Error: All image sources failed", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Generate/search images for articles")
    parser.add_argument("--prompt", "-p", required=True, help="Image description or generation prompt")
    parser.add_argument("--output", "-o", required=True, help="Output file path")
    parser.add_argument("--aspect", "-a", default="16:9", help="Aspect ratio (default: 16:9)")
    parser.add_argument("--source", "-s", default="auto",
                        choices=["auto", "gemini", "wikimedia"],
                        help="Image source (default: auto = Gemini then Wikimedia)")
    parser.add_argument("--search", default=None,
                        help="Override Wikimedia search query (default: use prompt)")
    args = parser.parse_args()

    generate_image(args.prompt, args.output, args.aspect, args.source, args.search)


if __name__ == "__main__":
    main()
