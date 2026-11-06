"""2026 Gyeongbokgung mission scoring.
Rules: H04 (20) + one video (30) + highest 4 other approved missions.
Maximum raw 120; normalized mission portion is 70; voting supplies 10+20.
Never count pending, rejected or test submissions.
"""
from collections import defaultdict

MISSION_POINTS = {
    "E02": 10, "E08": 10, "E10": 10,
    "M01": 15, "M06": 15, "M11": 15, "M12": 15,
    "H01": 20, "H04": 20, "H05": 20,
    "V01": 30, "V02": 30, "V03": 30,
}
THREE_PHOTO = {"M01", "M11", "H05"}
VIDEO_CODES = {"V01", "V02", "V03"}
EXTRA_CODES = set(MISSION_POINTS) - {"H04"} - VIDEO_CODES
RAW_MAX = 120
SCORE_MAX = 70


def calculate_mission_scores(db, query, teams):
    """Return team -> snapshot. One grouped query; no mutation, no per-file read."""
    rows = query(db,
        "SELECT team, mission_code, COUNT(*) AS n "
        "FROM mission_submissions "
        "WHERE status<>'rejected' AND is_test=FALSE "
        "GROUP BY team, mission_code",
        all=True)
    submitted = defaultdict(dict)
    for row in rows:
        team = int(row["team"])
        code = str(row["mission_code"])
        if team in range(1, 6) and code in MISSION_POINTS:
            submitted[team][code] = int(row["n"])

    result = {}
    for team in teams:
        tid = int(team["team"])
        counts = submitted[tid]
        complete = {
            code for code in MISSION_POINTS
            if counts.get(code, 0) >= (3 if code in THREE_PHOTO else 1)
        }
        photo_registered = bool(team.get("photo") or team.get("photo_ready"))
        video_registered = bool(team.get("video") or team.get("video_ready"))

        photo_done = "H04" in complete or photo_registered
        video_done = bool(complete & VIDEO_CODES) or video_registered
        # Distinct mission codes only; no repeats for multiple uploads.
        extras = sorted(
            (code for code in complete if code in EXTRA_CODES),
            key=lambda code: (-MISSION_POINTS[code], code)
        )
        credited = extras[:4]
        raw = (20 if photo_done else 0) + (30 if video_done else 0) + sum(
            MISSION_POINTS[c] for c in credited
        )
        normalized = round(raw * SCORE_MAX / RAW_MAX, 2)
        video_code = next((c for c in sorted(VIDEO_CODES) if c in complete), None)
        result[tid] = {
            "raw": raw,
            "normalized": normalized,
            "raw_max": RAW_MAX,
            "mission_max": SCORE_MAX,
            "completed": len(credited) + int(photo_done) + int(video_done),
            "photo_done": photo_done,
            "video_done": video_done,
            "video_code": video_code or ("운영진등록" if video_done else None),
            "selected_free": [{"code":c,"points":MISSION_POINTS[c]} for c in credited],
            "counted_files": sum(counts.values()),
            "counted_codes": sorted(complete),
            "incomplete_three_photo": {
                c: counts[c] for c in sorted(THREE_PHOTO)
                if 0 < counts.get(c, 0) < 3
            },
        }
    return result
