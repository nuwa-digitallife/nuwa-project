#!/usr/bin/env python3
"""Generate images via Gemini API for WeChat articles.

Usage:
    python gen_image.py --prompt "描述" --output path/to/output.png
    python gen_image.py --prompt "描述" --output path/to/output.png --aspect 16:9
"""

import argparse
import os
import sys
from pathlib import Path

def load_api_key():
    """Load Gemini API key from .env file."""
    env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip()
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    print("Error: GEMINI_API_KEY not found in .env or environment", file=sys.stderr)
    sys.exit(1)

def generate_image(prompt: str, output_path: str, aspect: str = "16:9"):
    """Generate an image using Gemini 2.0 Flash."""
    from google import genai
    from google.genai import types

    api_key = load_api_key()
    client = genai.Client(api_key=api_key)

    # Add aspect ratio hint to prompt
    aspect_hint = f"Image aspect ratio: {aspect}."
    full_prompt = f"{prompt}\n{aspect_hint}"

    print(f"Generating image...")
    print(f"Prompt: {prompt[:100]}...")

    response = client.models.generate_content(
        model="gemini-2.0-flash-exp-image-generation",
        contents=full_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"]
        )
    )

    image_saved = False
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(part.inline_data.data)
            size_kb = len(part.inline_data.data) // 1024
            print(f"Saved: {output_path} ({size_kb}KB, {part.inline_data.mime_type})")
            image_saved = True
        elif part.text is not None:
            print(f"Gemini: {part.text[:200]}")

    if not image_saved:
        print("Error: No image generated", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Generate images via Gemini API")
    parser.add_argument("--prompt", "-p", required=True, help="Image description prompt")
    parser.add_argument("--output", "-o", required=True, help="Output file path")
    parser.add_argument("--aspect", "-a", default="16:9", help="Aspect ratio (default: 16:9)")
    args = parser.parse_args()

    generate_image(args.prompt, args.output, args.aspect)

if __name__ == "__main__":
    main()
