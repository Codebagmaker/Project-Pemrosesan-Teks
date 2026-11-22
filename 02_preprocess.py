"""
02_preprocess.py
Pembersihan teks komentar + deduplikasi (sebelum pelabelan & split).

Prinsip (sesuai proposal): informasi emosi tidak boleh hilang.
 - emoji TIDAK dibuang, diubah menjadi token teks (mis. "emoji_wajah_marah")
 - kata negasi (tidak, bukan, dll.) TIDAK dihapus walau stopword removal diaktifkan
 - stemming tidak dipakai (bisa merusak kata slang & FastText subword)

Cara pakai:
    python 02_preprocess.py
    python 02_preprocess.py --remove-stopwords
    python 02_preprocess.py --slang data/slang_dict.csv    # CSV kolom: slang,formal (opsional, untuk menambah kamus)

Output: data/comments_clean.csv
"""
import argparse
import os
import re

import emoji
import pandas as pd

NEGATIONS = {"tidak", "tak", "bukan", "belum", "jangan", "tanpa", "nggak", "gak", "enggak"}

# Kamus slang awal -> PERLU kamu perluas setelah membaca data aslinya.
SLANG = {
    "gk": "tidak", "ga": "tidak", "gak": "tidak", "nggak": "tidak", "ngga": "tidak",
    "enggak": "tidak", "tdk": "tidak", "yg": "yang", "dgn": "dengan", "dg": "dengan",
    "utk": "untuk", "krn": "karena", "karna": "karena", "bgt": "banget", "bngt": "banget",
    "sm": "sama", "jd": "jadi", "jg": "juga", "udh": "sudah", "udah": "sudah",
    "sdh": "sudah", "blm": "belum", "tp": "tapi", "tpi": "tapi", "emg": "memang",
    "emang": "memang", "org": "orang", "lg": "lagi", "bs": "bisa", "klo": "kalau",
    "kalo": "kalau", "gw": "saya", "gue": "saya", "lu": "kamu", "lo": "kamu",
    "aja": "saja", "aj": "saja", "plis": "tolong", "pls": "tolong", "wkwk": "haha",
    "wkwkwk": "haha", "hrs": "harus", "dr": "dari", "sy": "saya", "mhs": "mahasiswa",
    "pemerintah": "pemerintah", "kpn": "kapan", "knp": "kenapa", "gmn": "bagaimana",
}

URL_RE = re.compile(r"https?://\S+|www\.\S+")
MENTION_RE = re.compile(r"@[\w.\-]+")
NONWORD_RE = re.compile(r"[^a-z0-9_\s]")
REPEAT_RE = re.compile(r"(.)\1{2,}")


def clean(text, slang, stopwords=None):
    t = str(text)
    t = URL_RE.sub(" ", t)
    t = MENTION_RE.sub(" ", t)
    t = t.lower()
    t = emoji.demojize(t, language="id", delimiters=(" emoji_", " "))
    t = NONWORD_RE.sub(" ", t)
    t = REPEAT_RE.sub(r"\1\1", t)                    # "marahhhh" -> "marahh"
    tokens = [slang.get(w, w) for w in t.split()]
    if stopwords:
        tokens = [w for w in tokens if w in NEGATIONS or w not in stopwords]
    return " ".join(tokens)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inp", default="data/comments_raw.csv")
    ap.add_argument("--out", default="data/comments_clean.csv")
    ap.add_argument("--slang", default=None)
    ap.add_argument("--remove-stopwords", action="store_true")
    ap.add_argument("--min-tokens", type=int, default=1)
    args = ap.parse_args()

    slang = dict(SLANG)
    if args.slang and os.path.exists(args.slang):
        extra = pd.read_csv(args.slang)
        slang.update(dict(zip(extra["slang"].str.lower(), extra["formal"].str.lower())))

    stopwords = None
    if args.remove_stopwords:
        from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
        stopwords = set(StopWordRemoverFactory().get_stop_words())

    df = pd.read_csv(args.inp)
    n0 = len(df)
    df["text_raw"] = df["text_raw"].fillna("").astype(str)
    df["text_clean"] = df["text_raw"].apply(lambda x: clean(x, slang, stopwords))

    df = df[df["text_clean"].str.split().str.len() >= args.min_tokens]
    n1 = len(df)
    df = df.drop_duplicates("text_clean", keep="first")   # cegah data leakage antar split
    n2 = len(df)

    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df[["comment_id", "video_no", "text_raw", "text_clean"]].to_csv(
        args.out, index=False, encoding="utf-8-sig")

    print(f"Awal: {n0} | setelah buang kosong: {n1} | setelah dedup: {n2}")
    print(df.groupby("video_no").size().rename("jumlah").to_string())
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
