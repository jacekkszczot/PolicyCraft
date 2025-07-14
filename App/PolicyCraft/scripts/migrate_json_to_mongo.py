"""One-off migration: load existing JSON analyses into MongoDB.
Run:
    python scripts/migrate_json_to_mongo.py --json ../data/database_storage.json \
           --mongo-uri mongodb://localhost:27017 --db policycraft
Will skip documents that already exist (same _id).
"""

import argparse
import json
from pymongo import MongoClient
from tqdm import tqdm


def migrate(json_path: str, mongo_uri: str, db_name: str):
    client = MongoClient(mongo_uri)
    db = client[db_name]
    col = db["analyses"]

    with open(json_path, "r", encoding="utf-8") as f:
        storage = json.load(f)

    analyses = storage.get("analyses", [])
    inserted, skipped = 0, 0
    for doc in tqdm(analyses, desc="Importing analyses"):
        _id = doc.get("_id")
        if col.find_one({"_id": _id}):
            skipped += 1
            continue
        col.insert_one(doc)
        inserted += 1
    print(f"Analyses imported: inserted={inserted}, skipped={skipped}")

    # Import recommendations
    rec_col = db["recommendations"]
    recs = storage.get("recommendations", [])
    r_ins, r_skip = 0, 0
    for rec in tqdm(recs, desc="Importing recommendations"):
        _id = rec.get("_id")
        if rec_col.find_one({"_id": _id}):
            r_skip += 1
            continue
        rec_col.insert_one(rec)
        r_ins += 1
    print(f"Recommendations imported: inserted={r_ins}, skipped={r_skip}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True)
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017")
    parser.add_argument("--db", default="policycraft")
    args = parser.parse_args()
    migrate(args.json, args.mongo_uri, args.db)
