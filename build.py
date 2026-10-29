"""data/ 의 원본 -> data/data.json. 재실행해도 같은 결과여야 한다.

호흡기 명세서(주상병 기준)만 행 단위로 내보낸다. 화면이 필터에 따라 평균·중앙값을 직접 계산한다.
rows 의 각 행: [월 인덱스, 종별 인덱스, 연령대 인덱스, 분위 인덱스, 입원여부(0/1), 총진료비]

사용: python build.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
RAW = ROOT / "data" / CONFIG["raw"]
OUT = ROOT / "data" / "data.json"

QUINTILES = ["1", "2", "3", "4", "5", "MA"]  # MA = 의료급여 (분위 값 없음)


def load_sheets(path: Path) -> dict[str, list[dict]]:
    """xlsx 모든 시트를 {시트명: [행 dict]} 로 읽는다. 값은 원본 그대로(문자열)."""
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheets = {}
    for ws in wb:
        rows = ws.iter_rows(values_only=True)
        header = next(rows, None)
        if header:
            sheets[ws.title] = [dict(zip(header, r)) for r in rows]
    return sheets


def is_resp(sick: str) -> bool:
    head = (sick or "")[:3]
    return any(lo <= head <= hi for lo, hi in CONFIG["resp_ranges"])


def band_index(age: int) -> int:
    for i, (lo, hi) in enumerate(CONFIG["age_bands"]):
        if lo <= age <= hi:
            return i
    raise ValueError(age)


def band_label(lo: int, hi: int) -> str:
    return f"{lo}세 이상" if hi >= 150 else f"{lo}-{hi}세"


def transform(sheets: dict[str, list[dict]]) -> dict:
    claims, patients, inst = sheets["claim"], sheets["patient"], sheets["institution"]
    cl_names = {r["code"]: r["code_nm"] for r in sheets["code_table"] if r["code_type"] == "종별코드"}
    cl_of = {r["yid"]: r["cl_cd"] for r in inst}
    cl_codes = CONFIG["cl_order"]

    # 환자 속성은 환자 단위로 고정 (연령대는 age_ref_year 기준)
    pat = {}
    for p in patients:
        q = p["prem_quintile"] or "MA"
        a = band_index(CONFIG["age_ref_year"] - int(p["birth_yr"]))
        pat[p["jid"]] = (QUINTILES.index(q), a)
    denom = Counter(f"{q}|{a}" for q, a in pat.values())

    months = sorted({c["recu_fr_dd"][:7] for c in claims})
    rows = []
    for c in claims:
        if not is_resp(c["main_sick"]):
            continue
        q, a = pat[c["jid"]]
        rows.append([
            months.index(c["recu_fr_dd"][:7]),
            cl_codes.index(cl_of[c["yid"]]),
            a,
            q,
            1 if c["fom_tp_cd"] == "021" else 0,
            int(c["rvd_rpe_tamt_amt"]),
        ])

    return {
        "meta": {
            "months": months,
            "asof": months[-1],
            "cl": [cl_names[c] for c in cl_codes],
            "age": [band_label(lo, hi) for lo, hi in CONFIG["age_bands"]],
            "quintile": ["1분위", "2분위", "3분위", "4분위", "5분위", "의료급여"],
            "highlight_months": CONFIG["highlight_months"],
            "total_claims": len(claims),
        },
        "patients": dict(denom),
        "rows": rows,
    }


def main() -> int:
    if not RAW.is_file():
        print(f"원본 없음: {RAW}", file=sys.stderr)
        return 1
    OUT.write_text(json.dumps(transform(load_sheets(RAW)), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
