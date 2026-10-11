"""
Live diagnostic for Zoom poll retrieval.

Reads credentials from zpa.ini, authenticates, and dumps the RAW responses
of every poll-related endpoint so we can see the exact structure Zoom returns
(in particular whether participant names come back as "Anonymous Attendee").

Secrets are never printed. Run:  python scripts/diagnose_polls.py
"""

import configparser
import json
import sys
from pathlib import Path

# Ensure UTF-8 output even when stdout is redirected/piped on Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

# Make the package importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from zpa.core.zoom_api import ZoomAPI  # noqa: E402


def load_ini() -> dict:
    ini_path = ROOT / "zpa.ini"
    if not ini_path.exists():
        raise SystemExit(f"zpa.ini not found at {ini_path}")
    cp = configparser.ConfigParser()
    cp.read(ini_path, encoding="utf-8")
    return {
        "account_id": cp.get("Zoom", "account_id", fallback=""),
        "client_id": cp.get("Zoom", "client_id", fallback=""),
        "client_secret": cp.get("Zoom", "client_secret", fallback=""),
        "meeting_id": cp.get("Zoom", "meeting_id", fallback=""),
    }


def dump(label: str, obj) -> None:
    print("\n" + "=" * 78)
    print(label)
    print("=" * 78)
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def main() -> None:
    cfg = load_ini()
    meeting_id = cfg["meeting_id"]
    print(f"Meeting ID from ini: {meeting_id}")

    api = ZoomAPI(cfg["account_id"], cfg["client_id"], cfg["client_secret"])

    try:
        api.get_access_token()
        print("OAuth token: OK (obtained)")
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"OAuth failed: {e}") from e

    endpoints = {
        "past_meetings/{id}/polls": f"https://api.zoom.us/v2/past_meetings/{meeting_id}/polls",
        "meetings/{id}/polls (definitions)": f"https://api.zoom.us/v2/meetings/{meeting_id}/polls",
        "report/meetings/{id}/polls (results)": f"https://api.zoom.us/v2/report/meetings/{meeting_id}/polls",
    }

    for label, url in endpoints.items():
        try:
            result = api.make_api_request(url)
        except Exception as e:  # noqa: BLE001
            dump(f"[{label}] -> ERROR", str(e))
            continue

        # Summarise the shape without losing the raw content
        if isinstance(result, dict):
            summary = {
                k: (f"<list len={len(v)}>" if isinstance(v, list) else type(v).__name__)
                for k, v in result.items()
            }
        else:
            summary = type(result).__name__
        dump(f"[{label}] SHAPE", summary)
        dump(f"[{label}] RAW", result)

        # If this looks like a results payload, list the names it attributes answers to
        if isinstance(result, dict) and isinstance(result.get("questions"), list):
            names = []
            for q in result["questions"]:
                if isinstance(q, dict):
                    qd = q.get("question_details", [])
                    names.append(
                        {
                            "name": q.get("name"),
                            "email": "<present>" if q.get("email") else "<empty>",
                            "num_answers": len(qd) if isinstance(qd, list) else "n/a",
                            "answers": [d.get("answer") for d in qd]
                            if isinstance(qd, list)
                            else qd,
                        }
                    )
            dump(f"[{label}] NAME/ANSWER MAP", names)

    # Participant names (for comparison with poll names)
    try:
        participants = api.get_participants(meeting_id)
        names = sorted({p.get("name", "") for p in participants})
        dump(
            "PARTICIPANT NAMES (in_meeting)",
            {"count": len(participants), "unique_names": names},
        )
    except Exception as e:  # noqa: BLE001
        dump("PARTICIPANTS -> ERROR", str(e))
        participants = []

    # Verify the corrected processing (mirrors the new logic in main.on_data_loaded)
    results = api.get_poll_results(meeting_id)
    verify_processing(results.get("questions", []), participants)


def verify_processing(polls, participants):
    """Mirror of the fixed main.on_data_loaded aggregation, to confirm the
    corrected Total and the anonymous summary row against the live data."""
    import re

    def num(answer):
        m = re.search(r"^\s*(\d+)", str(answer))
        return int(m.group(1)) if m else None

    def is_anon(v):
        return not v or str(v).strip().lower().startswith("anonymous")

    named = {}
    anon_votes = []
    for q in polls:
        if not isinstance(q, dict):
            continue
        name = q.get("name", "")
        details = q.get("question_details", []) or []
        if is_anon(name):
            anon_votes += [
                num(d.get("answer", ""))
                for d in details
                if isinstance(d, dict) and num(d.get("answer", "")) is not None
            ]
            continue
        nums = [num(d.get("answer", "")) for d in details if isinstance(d, dict)]
        nums = [n for n in nums if n is not None]
        named[name] = max(nums) if nums else "N/A"

    total = sum(v for v in named.values() if isinstance(v, int))
    rows = []
    if anon_votes:
        counts = {}
        for v in anon_votes:
            counts[v] = counts.get(v, 0) + 1
        breakdown = ", ".join(f"{counts[v]}x{v}" for v in sorted(counts))
        total += sum(anon_votes)
        rows.append(
            f"Anonymous responses ({len(anon_votes)}): {breakdown}  -> {sum(anon_votes)}"
        )

    dump(
        "CORRECTED RESULT (with fix)",
        {
            "named_voters_with_number": {
                k: v for k, v in named.items() if isinstance(v, int)
            },
            "anonymous_summary_row": rows,
            "anonymous_vote_count": len(anon_votes),
            "TOTAL": total,
        },
    )


if __name__ == "__main__":
    main()
