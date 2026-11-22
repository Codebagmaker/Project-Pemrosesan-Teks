"""
01_scrape_youtube.py
Mengambil komentar dari 5 video YouTube (Demonstrasi 10 November Yogyakarta)
menggunakan YouTube Data API v3 (resmi, tidak melanggar ToS seperti scraping HTML).

Cara pakai:
    export YOUTUBE_API_KEY="API_KEY_KAMU"          # Windows PowerShell: $env:YOUTUBE_API_KEY="..."
    python 01_scrape_youtube.py                    # top-level + replies
    python 01_scrape_youtube.py --no-replies       # hanya komentar utama

Output: data/comments_raw.csv
Catatan privasi: nama/ID akun TIDAK disimpan (proposal hanya memakai isi komentar).
"""
import argparse
import os
import re
import time

import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# (nomor video, URL, jumlah komentar yang tampil di YouTube saat kamu mencatat)
VIDEOS = [
    (1, "https://youtu.be/hL1acLEcxak", 775),
    (2, "https://youtube.com/shorts/mX-5VQQzDrg", 2120),
    (3, "https://youtu.be/D40KJT6rUqY", 399),
    (4, "https://youtube.com/shorts/FaGxQw_ugrU", 3116),
    (5, "https://youtu.be/2UnqiQNcPlI", 207),
]

ID_RE = re.compile(r"(?:youtu\.be/|shorts/|v=)([A-Za-z0-9_-]{11})")


def video_id(url: str) -> str:
    m = ID_RE.search(url)
    if not m:
        raise ValueError(f"Tidak bisa mengambil video ID dari: {url}")
    return m.group(1)


def call(request, retries=5):
    """Eksekusi request API dengan retry untuk error sementara."""
    for i in range(retries):
        try:
            return request.execute()
        except HttpError as e:
            status = getattr(e.resp, "status", None)
            if status in (500, 502, 503, 504) and i < retries - 1:
                time.sleep(2 ** i)
                continue
            raise


def parse(item, video_no, vid, parent_id=None):
    s = item["snippet"]
    return {
        "comment_id": item["id"],
        "video_no": video_no,
        "video_id": vid,
        "parent_id": parent_id,
        "is_reply": parent_id is not None,
        "text_raw": s.get("textDisplay", s.get("textOriginal", "")),
        "like_count": s.get("likeCount", 0),
        "published_at": s.get("publishedAt"),
    }


def fetch_replies(yt, parent_id, video_no, vid):
    rows, token = [], None
    while True:
        resp = call(yt.comments().list(
            part="snippet", parentId=parent_id, maxResults=100,
            pageToken=token, textFormat="plainText"))
        rows += [parse(it, video_no, vid, parent_id) for it in resp["items"]]
        token = resp.get("nextPageToken")
        if not token:
            return rows


def fetch_video(yt, video_no, vid, include_replies=True):
    rows, token = [], None
    while True:
        resp = call(yt.commentThreads().list(
            part="snippet,replies", videoId=vid, maxResults=100,
            pageToken=token, textFormat="plainText", order="time"))
        for item in resp["items"]:
            top = item["snippet"]["topLevelComment"]
            rows.append(parse(top, video_no, vid))
            if include_replies:
                total = item["snippet"].get("totalReplyCount", 0)
                inline = item.get("replies", {}).get("comments", [])
                if total > len(inline):          # replies yang ikut respon bisa terpotong
                    rows += fetch_replies(yt, top["id"], video_no, vid)
                else:
                    rows += [parse(r, video_no, vid, top["id"]) for r in inline]
        token = resp.get("nextPageToken")
        print(f"  video {video_no}: {len(rows)} komentar terkumpul", end="\r")
        if not token:
            break
    print()
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-replies", action="store_true")
    ap.add_argument("--out", default="data/comments_raw.csv")
    args = ap.parse_args()

    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        raise SystemExit("Set dulu environment variable YOUTUBE_API_KEY.")
    yt = build("youtube", "v3", developerKey=key)

    all_rows = []
    for no, url, expected in VIDEOS:
        vid = video_id(url)
        print(f"[Video {no}] {vid} (target tampil di YouTube: {expected})")
        try:
            rows = fetch_video(yt, no, vid, include_replies=not args.no_replies)
        except HttpError as e:
            print(f"  GAGAL video {no}: {e}")
            continue
        all_rows += rows

    df = pd.DataFrame(all_rows).drop_duplicates("comment_id")
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df.to_csv(args.out, index=False, encoding="utf-8-sig")

    print("\n=== Ringkasan ===")
    expected = {n: e for n, _, e in VIDEOS}
    for n, g in df.groupby("video_no"):
        print(f"Video {n}: {len(g)} diambil "
              f"({(~g.is_reply).sum()} utama + {g.is_reply.sum()} balasan) | target {expected[n]}")
    print(f"TOTAL: {len(df)} komentar | target 6617 -> {args.out}")
    print("Selisih kecil wajar (komentar dihapus/disembunyikan, atau angka YouTube belum sinkron).")


if __name__ == "__main__":
    main()
