import random
import datetime
from typing import List, Dict, Any

# Forensic Synthetic Scenario: "OPERATION CITADEL - ORGANIZED NETWORK TELECOM AUDIT"

TARGET_ALPHA = "+919820112345"
ASSOCIATES = [
    {"num": "+919820154321", "name": "Associate 1 (Field Lead)", "role": "Co-Conspirator"},
    {"num": "+919811099887", "name": "Associate 2 (Logistics)", "role": "Handler"},
    {"num": "+919765432100", "name": "Associate 3 (Courier)", "role": "Transporter"},
    {"num": "+919988776655", "name": "Burner 1 (Disposable)", "role": "Burner"},
    {"num": "+919456711223", "name": "Burner 2 (Signal Ping)", "role": "Burner"},
    {"num": "+919820044332", "name": "Legitimate Contact (Family)", "role": "Normal"},
    {"num": "+919123456789", "name": "Business Corp Office", "role": "Normal"},
    {"num": "+919833322110", "name": "Taxi / Transport Dispatch", "role": "Service"},
    {"num": "+919700011222", "name": "Bank Tele-Verification", "role": "Service"},
    {"num": "+919999988888", "name": "Intermediary / Broker", "role": "Suspect"}
]

TOWERS = [
    {"cell_id": "MUM-4001", "lac": "4001", "tac": "12010", "site": "Nariman Point Apex BTS", "lat": 18.9256, "lon": 72.8242, "tech": "4G LTE", "op": "Airtel"},
    {"cell_id": "MUM-4002", "lac": "4001", "tac": "12010", "site": "Marine Drive Tower 2", "lat": 18.9438, "lon": 72.8231, "tech": "4G LTE", "op": "Airtel"},
    {"cell_id": "MUM-4003", "lac": "4002", "tac": "12015", "site": "Dadar Central Junction", "lat": 19.0178, "lon": 72.8478, "tech": "4G LTE", "op": "Vodafone Idea"},
    {"cell_id": "MUM-4004", "lac": "4003", "tac": "12020", "site": "BKC Diamond Bourse", "lat": 19.0664, "lon": 72.8687, "tech": "5G NR", "op": "Jio 5G"},
    {"cell_id": "MUM-4005", "lac": "4003", "tac": "12020", "site": "Kurla West Flyover Site", "lat": 19.0650, "lon": 72.8790, "tech": "4G LTE", "op": "Airtel"},
    {"cell_id": "MUM-4006", "lac": "4004", "tac": "12025", "site": "CSM Int'l Airport T2 Node", "lat": 19.0896, "lon": 72.8656, "tech": "5G NR", "op": "Jio 5G"},
    {"cell_id": "MUM-4007", "lac": "4005", "tac": "12030", "site": "Andheri Link Road Sector 3", "lat": 19.1363, "lon": 72.8277, "tech": "4G LTE", "op": "Vodafone Idea"},
    {"cell_id": "MUM-4008", "lac": "4006", "tac": "12035", "site": "Vashi Toll Plaza BTS", "lat": 19.0771, "lon": 72.9986, "tech": "4G LTE", "op": "Airtel"},
    {"cell_id": "MUM-4009", "lac": "4007", "tac": "12040", "site": "Thane Teen Hath Naka", "lat": 19.2183, "lon": 72.9781, "tech": "4G LTE", "op": "Airtel"},
    {"cell_id": "MUM-4010", "lac": "4008", "tac": "12045", "site": "Belapur CBD Metro Station", "lat": 19.0222, "lon": 73.0410, "tech": "4G LTE", "op": "Jio"}
]

IMEI_PRIMARY = "864209041234567"
IMEI_BURNER = "352109059876543"
IMEI_SECONDARY = "867800045544332"

IMSI_SIM1 = "404450912345678"  # Airtel Primary
IMSI_SIM2 = "404450998877665"  # Swapped SIM on primary IMEI
IMSI_BURNER = "404700012398745"

def generate_synthetic_cdr(case_id: int = 1, record_count: int = 450) -> List[Dict[str, Any]]:
    """Generate high-fidelity synthetic CDR dataset with specific criminal investigation patterns."""
    records = []
    
    # Base timeframe: 14 days preceding today
    base_date = datetime.datetime.utcnow() - datetime.timedelta(days=14)
    base_date = base_date.replace(hour=8, minute=0, second=0, microsecond=0)

    # 1. Generate core surveillance records for Target Alpha
    for i in range(record_count):
        # Determine day offset (0 to 13)
        day_offset = random.randint(0, 13)
        
        # Decide scenario type:
        # 30% late night coordination (00:00 - 04:30)
        # 25% ping calls (< 5 seconds)
        # 30% daytime standard calls
        # 15% SMS events
        rand_roll = random.random()

        if rand_roll < 0.25:
            # Late-night coordination window
            hour = random.choice([0, 1, 2, 3, 4])
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            # Communicates mostly with conspirators
            partner = random.choice(ASSOCIATES[:4])
            call_type = random.choice(["Voice", "Voice", "SMS"])
            direction = random.choice(["Outgoing", "Incoming"])
            duration = random.randint(60, 480) if call_type == "Voice" else 0
            tower = random.choice([TOWERS[0], TOWERS[1], TOWERS[3]])
        elif rand_roll < 0.45:
            # Short ping call / missed call coordination
            hour = random.randint(9, 22)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            partner = random.choice([ASSOCIATES[3], ASSOCIATES[4], ASSOCIATES[0]])
            call_type = "Voice"
            direction = random.choice(["Outgoing", "Incoming"])
            duration = random.choice([0, 1, 2, 3, 4])
            tower = random.choice(TOWERS)
        elif rand_roll < 0.60:
            # SMS event
            hour = random.randint(8, 23)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            partner = random.choice(ASSOCIATES)
            call_type = "SMS"
            direction = random.choice(["Outgoing", "Incoming"])
            duration = 0
            tower = random.choice(TOWERS)
        else:
            # Daytime standard voice call
            hour = random.randint(8, 21)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            partner = random.choice(ASSOCIATES)
            call_type = "Voice"
            direction = random.choice(["Outgoing", "Incoming"])
            duration = random.randint(20, 650)
            tower = random.choice(TOWERS)

        event_time = base_date + datetime.timedelta(days=day_offset, hours=hour, minutes=minute, seconds=second)

        # SIM swap scenario: on days 8 and 9, Target Alpha uses SIM 2 on the primary phone
        if day_offset in [8, 9]:
            imsi = IMSI_SIM2
            imei = IMEI_PRIMARY
        elif day_offset == 11 and partner["num"] == ASSOCIATES[3]["num"]:
            # Burner phone usage on day 11
            imsi = IMSI_BURNER
            imei = IMEI_BURNER
        else:
            imsi = IMSI_SIM1
            imei = IMEI_PRIMARY

        # Calling vs Called party assignment
        if direction == "Outgoing":
            calling_party = TARGET_ALPHA
            called_party = partner["num"]
        else:
            calling_party = partner["num"]
            called_party = TARGET_ALPHA

        # Validation flags & occasional realistic flaws
        flags = []
        term_cause = "Normal Clearing"
        if duration == 0 and call_type == "Voice":
            term_cause = random.choice(["No Answer", "Subscriber Busy", "Call Drop"])
            direction = "Missed" if direction == "Incoming" else "Outgoing"

        # 2% intentional data anomalies for parser robustness testing
        if i % 85 == 0:
            flags.append("DATA_FORMAT_WARNING_FLAGGED")
        elif i % 120 == 0:
            called_party = "+919999900000"
            flags.append("SHORT_CONTACT_PROBE")

        sms_type = None
        if call_type == "SMS":
            sms_type = "MO-SMS" if direction == "Outgoing" else "MT-SMS"

        records.append({
            "calling_number": calling_party,
            "called_number": called_party,
            "call_date": event_time.strftime("%Y-%m-%d"),
            "call_time": event_time.strftime("%H:%M:%S"),
            "call_datetime": event_time,
            "duration": duration,
            "call_type": call_type,
            "direction": direction,
            "sms_type": sms_type,
            "termination_cause": term_cause,
            "imei": imei,
            "imsi": imsi,
            "cell_id": tower["cell_id"],
            "lac": tower["lac"],
            "tac": tower["tac"],
            "cgi": f"404-45-{tower['lac']}-{tower['cell_id'].split('-')[1]}",
            "site_id": tower["site"],
            "latitude": tower["lat"],
            "longitude": tower["lon"],
            "network_type": tower["tech"],
            "roaming_info": "National Roaming" if day_offset == 10 else "Home Network",
            "operator": tower["op"],
            "is_valid": True,
            "validation_flags": flags
        })

    # Sort chronologically
    records.sort(key=lambda x: x["call_datetime"])
    return records
