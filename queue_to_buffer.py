#!/usr/bin/env python3
"""
MedPharmaConnect → Buffer Queue Script
Reads all social post markdown files and queues them to Buffer via API.
Schedules one post per platform per day starting from tomorrow.

Usage:
    python3 queue_to_buffer.py

You'll be prompted for your Buffer API key.
Get it at: https://publish.buffer.com/settings/api
"""

import json
import re
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── CONFIG ──────────────────────────────────────────────────────────────────

SOCIAL_DIR = Path(__file__).parent / "content" / "social"
API_ENDPOINT = "https://api.buffer.com"

# Posting times in UTC (adjust to match your preferred local times)
# These are set to mid-morning US Eastern (EST = UTC-5, EDT = UTC-4)
PLATFORM_TIMES = {
    "linkedin":  "14:00:00",  # 9 AM EDT / 10 AM EST
    "facebook":  "15:00:00",  # 10 AM EDT / 11 AM EST
    "twitter":   "16:00:00",  # 11 AM EDT / 12 PM EST
    # instagram: skipped — requires image/video via API (text-only not supported)
    # tiktok: skipped — requires video via API
}

# Add platform names here to skip them this run (e.g. already queued)
SKIP_PLATFORMS = []

# Only queue posts for these specific scheduled dates (leave empty to queue all)
ONLY_DATES = set()

# ── GRAPHQL HELPERS ──────────────────────────────────────────────────────────

def gql(api_key, query, variables=None):
    """Execute a GraphQL request against the Buffer API."""
    import urllib.request
    import urllib.error
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        API_ENDPOINT,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise Exception(f"HTTP {e.code}: {e.reason}\nResponse body: {body}")


def get_org_and_channels(api_key):
    """Fetch organization ID and all connected channel IDs."""
    result = gql(api_key, """
        query {
          account {
            organizations { id name }
          }
        }
    """)
    orgs = result["data"]["account"]["organizations"]
    if not orgs:
        print("❌  No organizations found in your Buffer account.")
        sys.exit(1)
    org_id = orgs[0]["id"]
    org_name = orgs[0]["name"]

    result = gql(api_key, f"""
        query GetChannels {{
          channels(input: {{ organizationId: "{org_id}" }}) {{
            id name service
          }}
        }}
    """)

    channels = result["data"]["channels"]
    return org_name, channels


def create_post(api_key, channel_id, text, due_at_iso, service=None):
    """Create a scheduled post via the Buffer API."""
    input_data = {
        "text": text,
        "channelId": channel_id,
        "schedulingType": "automatic",
        "mode": "customScheduled",
        "dueAt": due_at_iso,
    }
    # Facebook requires explicit post type metadata
    if service == "facebook":
        input_data["metadata"] = {"facebook": {"type": "post"}}

    result = gql(api_key, """
        mutation CreatePost($input: CreatePostInput!) {
          createPost(input: $input) {
            ... on PostActionSuccess {
              post { id text dueAt }
            }
            ... on MutationError {
              message
            }
          }
        }
    """, {"input": input_data})

    cp = result.get("data", {}).get("createPost", {})
    if "post" in cp:
        return True, cp["post"]["dueAt"]
    else:
        return False, cp.get("message", "Unknown error")


# ── MARKDOWN PARSERS ─────────────────────────────────────────────────────────

def extract_section(text, header_pattern):
    """Extract content between a ## header and the next --- or ## header.
    header_pattern is used as a raw regex (not escaped), so pass literal
    strings for simple headers and regex strings for complex ones."""
    pattern = rf"##\s+{header_pattern}\s*\n(.*?)(?=\n---|\n##|\Z)"
    m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if not m:
        return None
    return m.group(1).strip()


def clean_twitter(text):
    """Remove char-count annotations and markdown formatting from Twitter posts."""
    # Remove (NNN chars) annotations
    text = re.sub(r"\*?\(?\d{2,3}\s+chars?\)?\*?", "", text, flags=re.IGNORECASE)
    # Strip markdown bold/italic (**text** → text, *text* → text)
    text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)
    # Strip markdown underline
    text = re.sub(r"_{1,2}([^_]+)_{1,2}", r"\1", text)
    return text.strip()


def clean_instagram(text):
    """Strip the 'Visual: ...' block; keep only the caption text."""
    # Remove **Visual:** or Visual: block (up to blank line or Caption:)
    text = re.sub(r"\*?\*?Visual:?\*?\*?.*?(?=\n\n|\*?\*?Caption:?\*?\*?|\Z)", "", text, flags=re.DOTALL)
    # Strip **Caption:** label
    text = re.sub(r"\*?\*?Caption:?\*?\*?\s*", "", text).strip()
    return text


def parse_social_file(filepath):
    """Return dict of {platform: post_text} for a single social markdown file."""
    content = filepath.read_text(encoding="utf-8")
    posts = {}

    raw_linkedin = extract_section(content, "LinkedIn")
    if raw_linkedin:
        posts["linkedin"] = raw_linkedin

    raw_facebook = extract_section(content, "Facebook")
    if raw_facebook:
        posts["facebook"] = raw_facebook

    # Twitter header varies: "X / Twitter", "Twitter", etc. — use regex, not re.escape
    raw_twitter = (extract_section(content, r"X\s*/\s*Twitter")
                   or extract_section(content, "X \\(Twitter\\)")
                   or extract_section(content, "Twitter"))
    if raw_twitter:
        posts["twitter"] = clean_twitter(raw_twitter)

    # Instagram requires images via API — skip automated queuing
    # posts["instagram"] = ...  (needs image URL, can't do text-only)

    # TikTok skipped — Buffer/TikTok API requires video content
    return posts


def load_all_posts():
    """Load and parse all social post files, sorted by date."""
    files = sorted(SOCIAL_DIR.glob("social-*.md"))
    all_posts = []
    for f in files:
        posts = parse_social_file(f)
        if posts:
            all_posts.append(posts)
    return all_posts


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  MedPharmaConnect → Buffer Queue Script")
    print("=" * 60)
    print()
    print("Get your API key at: https://publish.buffer.com/settings/api")
    print()

    api_key = os.environ.get("BUFFER_API_KEY") or input("Paste your Buffer API key: ").strip()
    if not api_key:
        print("❌  No API key provided. Exiting.")
        sys.exit(1)

    print("\n🔍  Fetching your Buffer channels...")
    try:
        org_name, channels = get_org_and_channels(api_key)
    except Exception as e:
        print(f"❌  API error: {e}")
        print("    Make sure your API key is correct and try again.")
        sys.exit(1)

    print(f"✅  Connected to: {org_name}")
    print(f"    Found {len(channels)} channel(s):")
    for ch in channels:
        print(f"      • {ch['name']} ({ch['service']})")

    # Map service → channel_id (pick first match per service)
    channel_map = {}
    for ch in channels:
        svc = ch["service"].lower()
        if svc not in channel_map:
            channel_map[svc] = ch["id"]

    # Normalize: buffer may call it 'twitter' or 'x'
    if "x" in channel_map and "twitter" not in channel_map:
        channel_map["twitter"] = channel_map["x"]

    print()
    print("📂  Loading social post files...")
    all_posts = load_all_posts()
    print(f"    Loaded {len(all_posts)} days of posts.")

    # Schedule starting from tomorrow
    start_date = datetime.now(timezone.utc).date() + timedelta(days=1)
    total_queued = 0
    total_failed = 0

    print()
    print(f"📅  Scheduling posts starting {start_date}...")
    print()

    for day_offset, day_posts in enumerate(all_posts):
        post_date = start_date + timedelta(days=day_offset)

        for platform, text in day_posts.items():
            if platform not in channel_map:
                continue  # Skip platforms not connected in Buffer
            if platform not in PLATFORM_TIMES:
                continue
            if platform in SKIP_PLATFORMS:
                continue  # Already queued
            if ONLY_DATES and str(post_date) not in ONLY_DATES:
                continue  # Date filter active

            channel_id = channel_map[platform]
            time_str = PLATFORM_TIMES[platform]
            due_at = f"{post_date}T{time_str}Z"

            # Trim text to stay well under Twitter's 280 char limit.
            # Use 260 as ceiling to account for Unicode/emoji double-counting.
            if platform == "twitter":
                text = text.strip()
                if len(text) > 260:
                    text = text[:257].rstrip() + "..."

            try:
                ok, info = create_post(api_key, channel_id, text, due_at, service=platform)
                if ok:
                    print(f"  ✅  {post_date} {platform:<12} → queued for {info}")
                    total_queued += 1
                else:
                    print(f"  ❌  {post_date} {platform:<12} → error: {info}")
                    total_failed += 1
            except Exception as e:
                print(f"  ❌  {post_date} {platform:<12} → exception: {e}")
                total_failed += 1

    print()
    print("=" * 60)
    print(f"  Done! Queued: {total_queued}  |  Failed: {total_failed}")
    print(f"  View your queue at: https://publish.buffer.com")
    print("=" * 60)


if __name__ == "__main__":
    main()
