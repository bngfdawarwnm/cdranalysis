import os
import re
import csv
import json
import datetime
from typing import Dict, List, Tuple, Any, Optional

try:
    import openpyxl
except ImportError:
    openpyxl = None

# Standard CDR canonical field definitions
STANDARD_FIELDS = {
    "calling_number": "A Party / Calling Number",
    "called_number": "B Party / Called Number",
    "call_date": "Call Date",
    "call_time": "Call Time",
    "call_datetime": "Combined Call Timestamp",
    "duration": "Duration (Seconds)",
    "call_type": "Call Type (Voice/SMS/Data)",
    "direction": "Direction (Incoming/Outgoing)",
    "sms_type": "SMS Type",
    "imei": "IMEI (Device Identifier)",
    "imsi": "IMSI (SIM Identifier)",
    "cell_id": "Cell ID",
    "lac": "LAC (Location Area Code)",
    "tac": "TAC (Tracking Area Code)",
    "cgi": "CGI (Cell Global Identity)",
    "site_id": "Site ID / BTS ID",
    "latitude": "Cell Tower Latitude",
    "longitude": "Cell Tower Longitude",
    "termination_cause": "Termination Cause / Release Code",
    "roaming_info": "Roaming Status",
    "operator": "Telecom Operator"
}

# Heuristics patterns for automatic column name detection
SYNONYM_PATTERNS = {
    "calling_number": [r"^calling", r"^caller", r"a_party", r"party_a", r"^anum", r"^a_num", r"^msisdn$", r"source.*num", r"originating"],
    "called_number": [r"^called", r"dialed", r"b_party", r"party_b", r"^bnum", r"^b_num", r"dest.*num", r"target.*num"],
    "call_date": [r"^date$", r"call.*date", r"start.*date", r"session.*date", r"trans.*date"],
    "call_time": [r"^time$", r"call.*time", r"start.*time", r"session.*time"],
    "call_datetime": [r"datetime", r"timestamp", r"start.*datetime", r"call.*timestamp", r"date.*time"],
    "duration": [r"duration", r"^dur$", r"dur.*sec", r"duration.*sec", r"billsec", r"talk_time", r"call.*len"],
    "call_type": [r"call.*type", r"^type$", r"service.*type", r"record.*type", r"event.*type"],
    "direction": [r"direction", r"^dir$", r"flow", r"in_out", r"traffic_direction", r"call.*dir"],
    "sms_type": [r"sms.*type", r"msg.*type", r"message.*type"],
    "imei": [r"imei", r"device.*imei", r"handset.*imei", r"terminal.*id"],
    "imsi": [r"imsi", r"sim.*imsi", r"subscriber.*imsi"],
    "cell_id": [r"cell.*id", r"^cellid$", r"^ci$", r"serving.*cell", r"first.*cell"],
    "lac": [r"^lac$", r"location.*area.*code", r"first.*lac"],
    "tac": [r"^tac$", r"tracking.*area.*code"],
    "cgi": [r"^cgi$", r"cell.*global.*identity", r"first.*cgi"],
    "site_id": [r"site.*id", r"^site$", r"bts.*id", r"enodeb.*id", r"gnodeb.*id"],
    "latitude": [r"lat", r"latitude", r"tower.*lat", r"cell.*lat"],
    "longitude": [r"lon", r"long", r"longitude", r"tower.*lon", r"cell.*lon"],
    "termination_cause": [r"term.*cause", r"disconnect.*reason", r"release.*cause", r"end.*cause", r"cause"],
    "roaming_info": [r"roam", r"roaming.*info", r"roam.*status"],
    "operator": [r"operator", r"carrier", r"service.*provider", r"telecom"]
}

def auto_detect_columns(headers: List[str]) -> Dict[str, str]:
    mapping = {}
    used_headers = set()

    for std_field, patterns in SYNONYM_PATTERNS.items():
        matched = None
        for pattern in patterns:
            regex = re.compile(pattern, re.IGNORECASE)
            for header in headers:
                if header in used_headers:
                    continue
                clean_h = header.strip().lower().replace(" ", "_").replace("-", "_")
                if regex.search(clean_h):
                    matched = header
                    break
            if matched:
                break
        if matched:
            mapping[std_field] = matched
            used_headers.add(matched)

    return mapping

def read_preview_data(file_path: str, nrows: int = 10) -> Tuple[List[str], List[Dict[str, Any]], int]:
    ext = os.path.splitext(file_path)[1].lower()
    headers = []
    records = []
    total_rows = 0

    if ext in [".xlsx", ".xls"] and openpyxl:
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        sheet = wb.active
        all_rows = list(sheet.iter_rows(values_only=True))
        if all_rows:
            headers = [str(c or '').strip() for c in all_rows[0]]
            for r in all_rows[1:nrows+1]:
                row_dict = {}
                for idx, h in enumerate(headers):
                    val = r[idx] if idx < len(r) else ''
                    row_dict[h] = str(val) if val is not None else ''
                records.append(row_dict)
            total_rows = max(0, len(all_rows) - 1)
        wb.close()
    elif ext == ".json":
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                data = data.get("records", data.get("data", []))
            if isinstance(data, list) and len(data) > 0:
                headers = list(data[0].keys())
                records = data[:nrows]
                total_rows = len(data)
    else:
        # Delimited text (CSV, TSV, Pipe)
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            sample = f.read(4096)
            f.seek(0)
            delimiter = ','
            if '\t' in sample:
                delimiter = '\t'
            elif '|' in sample:
                delimiter = '|'
            elif ';' in sample:
                delimiter = ';'

            reader = csv.DictReader(f, delimiter=delimiter)
            headers = [h.strip() for h in (reader.fieldnames or [])]
            for i, r in enumerate(reader):
                if i < nrows:
                    records.append({k.strip(): (v or '').strip() for k, v in r.items()})
                total_rows += 1

    return headers, records, total_rows

def clean_phone_number(num_str: Any) -> str:
    if num_str is None:
        return "UNKNOWN"
    s = str(num_str).strip()
    if s.endswith(".0"):
        s = s[:-2]
    has_plus = s.startswith("+")
    digits = re.sub(r"[^\d]", "", s)
    if not digits:
        return "UNKNOWN"
    if has_plus:
        return f"+{digits}"
    return digits

DATETIME_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
    "%d-%m-%Y %H:%M:%S",
    "%m/%d/%Y %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%d/%m/%Y %H:%M",
    "%Y-%m-%d",
    "%d/%m/%Y",
]

def parse_flexible_dt(s: str) -> Optional[datetime.datetime]:
    s = s.strip()
    for fmt in DATETIME_FORMATS:
        try:
            return datetime.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None

def parse_datetime_field(row: Dict[str, Any], date_col: Optional[str], time_col: Optional[str], dt_col: Optional[str]) -> Tuple[Optional[str], Optional[str], datetime.datetime, List[str]]:
    flags = []
    now = datetime.datetime.utcnow()

    # If combined datetime column is present
    if dt_col and dt_col in row and str(row[dt_col]).strip() not in ("", "nan", "None"):
        val_str = str(row[dt_col]).strip()
        dt = parse_flexible_dt(val_str)
        if dt:
            return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S"), dt, flags
        flags.append("MALFORMED_COMBINED_TIMESTAMP")

    # If separate date and time columns
    date_val = str(row.get(date_col, "")).strip() if date_col else ""
    time_val = str(row.get(time_col, "")).strip() if time_col else ""

    if date_val and date_val not in ("", "nan", "None"):
        comb = f"{date_val} {time_val}".strip()
        dt = parse_flexible_dt(comb)
        if not dt:
            dt = parse_flexible_dt(date_val)
        if dt:
            return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S"), dt, flags
        flags.append("MALFORMED_DATE_TIME")

    flags.append("MISSING_TIMESTAMP_DEFAULTED")
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), now, flags

def process_raw_records(rows: List[Dict[str, Any]], mapping: Dict[str, str], dataset_id: int, case_id: Optional[int] = None) -> List[Dict[str, Any]]:
    records = []
    seen_hashes = set()

    for row in rows:
        flags = []

        # Calling number
        calling_col = mapping.get("calling_number")
        raw_calling = row.get(calling_col) if calling_col else None
        calling = clean_phone_number(raw_calling)
        if calling == "UNKNOWN":
            flags.append("MISSING_CALLING_NUMBER")

        # Called number
        called_col = mapping.get("called_number")
        raw_called = row.get(called_col) if called_col else None
        called = clean_phone_number(raw_called)
        if called == "UNKNOWN":
            flags.append("MISSING_CALLED_NUMBER")

        # Timestamps
        date_col = mapping.get("call_date")
        time_col = mapping.get("call_time")
        dt_col = mapping.get("call_datetime")
        call_date, call_time, call_dt, dt_flags = parse_datetime_field(row, date_col, time_col, dt_col)
        flags.extend(dt_flags)

        # Duration
        dur_col = mapping.get("duration")
        duration = 0
        if dur_col and dur_col in row and str(row[dur_col]).strip() not in ("", "nan", "None"):
            try:
                duration = max(0, int(float(str(row[dur_col]).strip())))
            except Exception:
                flags.append("INVALID_DURATION_FORMAT")

        # Call Type & Direction
        ctype_col = mapping.get("call_type")
        raw_ctype = str(row.get(ctype_col, "Voice")).strip()
        call_type = "Voice"
        if any(k in raw_ctype.upper() for k in ["SMS", "TEXT", "MESSAGE", "MSG"]):
            call_type = "SMS"
        elif any(k in raw_ctype.upper() for k in ["DATA", "GPRS", "INTERNET"]):
            call_type = "Data"

        dir_col = mapping.get("direction")
        raw_dir = str(row.get(dir_col, "Outgoing")).strip().upper()
        direction = "Outgoing"
        if "IN" in raw_dir and "OUT" not in raw_dir:
            direction = "Incoming"
        elif "OUT" in raw_dir:
            direction = "Outgoing"
        elif "MISSED" in raw_dir:
            direction = "Missed"
        elif "FORW" in raw_dir:
            direction = "Forwarded"

        sms_col = mapping.get("sms_type")
        sms_type = str(row.get(sms_col, "")).strip() or None
        if call_type == "SMS" and not sms_type:
            sms_type = "MO-SMS" if direction == "Outgoing" else "MT-SMS"

        # Hardware identifiers
        imei_col = mapping.get("imei")
        imei = str(row.get(imei_col, "")).strip().split(".")[0] or None
        if imei and len(imei) < 14:
            flags.append("SHORT_IMEI")

        imsi_col = mapping.get("imsi")
        imsi = str(row.get(imsi_col, "")).strip().split(".")[0] or None

        # Cellular & Location
        cell_col = mapping.get("cell_id")
        cell_id = str(row.get(cell_col, "")).strip().split(".")[0] or None

        lac_col = mapping.get("lac")
        lac = str(row.get(lac_col, "")).strip().split(".")[0] or None

        tac_col = mapping.get("tac")
        tac = str(row.get(tac_col, "")).strip().split(".")[0] or None

        cgi_col = mapping.get("cgi")
        cgi = str(row.get(cgi_col, "")).strip() or None

        site_col = mapping.get("site_id")
        site_id = str(row.get(site_col, "")).strip() or None

        lat_col = mapping.get("latitude")
        lat = None
        if lat_col and row.get(lat_col):
            try:
                lat = float(row[lat_col])
            except Exception:
                pass

        lon_col = mapping.get("longitude")
        lon = None
        if lon_col and row.get(lon_col):
            try:
                lon = float(row[lon_col])
            except Exception:
                pass

        term_col = mapping.get("termination_cause")
        term_cause = str(row.get(term_col, "Normal Clearing")).strip() or "Normal Clearing"
        if duration == 0 and call_type == "Voice" and term_cause == "Normal Clearing":
            term_cause = "No Answer / Missed"

        roam_col = mapping.get("roaming_info")
        roaming = str(row.get(roam_col, "Home Network")).strip() or "Home Network"

        oper_col = mapping.get("operator")
        operator = str(row.get(oper_col, "Standard Carrier")).strip() or "Standard Carrier"

        row_signature = f"{calling}|{called}|{call_dt.isoformat()}|{duration}|{call_type}"
        if row_signature in seen_hashes:
            flags.append("DUPLICATE_RECORD")
        else:
            seen_hashes.add(row_signature)

        is_valid = len(flags) == 0 or (len(flags) == 1 and flags[0] in ["DUPLICATE_RECORD", "SHORT_IMEI"])

        records.append({
            "dataset_id": dataset_id,
            "case_id": case_id,
            "calling_number": calling,
            "called_number": called,
            "call_date": call_date,
            "call_time": call_time,
            "call_datetime": call_dt,
            "duration": duration,
            "call_type": call_type,
            "direction": direction,
            "sms_type": sms_type,
            "termination_cause": term_cause,
            "imei": imei,
            "imsi": imsi,
            "cell_id": cell_id,
            "lac": lac,
            "tac": tac,
            "cgi": cgi,
            "site_id": site_id,
            "latitude": lat,
            "longitude": lon,
            "network_type": "5G NR" if tac and tac.isdigit() and int(tac) > 50000 else "4G LTE",
            "roaming_info": roaming,
            "operator": operator,
            "is_valid": is_valid,
            "validation_flags": flags
        })

    return records
