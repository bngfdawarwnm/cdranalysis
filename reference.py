from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter(prefix="/api/reference", tags=["CDR Dictionary"])

DICTIONARY_ENTRIES: List[Dict[str, Any]] = [
    # A. Subscriber Information
    {
        "category": "A. Subscriber Information",
        "field_name": "A Number / Calling Party",
        "standard_key": "calling_number",
        "description": "The Mobile Station International Subscriber Directory Number (MSISDN) or phone number initiating the voice call or SMS.",
        "typical_format": "+91 98201 12345 or 9820112345 (E.164 standard)",
        "investigative_relevance": "Primary anchor point for outgoing calls. Pinpoints originator in conspiracy or incident coordination."
    },
    {
        "category": "A. Subscriber Information",
        "field_name": "B Number / Called Party",
        "standard_key": "called_number",
        "description": "The recipient telephone number to which the voice call was dialed or SMS was directed.",
        "typical_format": "+91 98110 99887 or 10-digit national number",
        "investigative_relevance": "Establishes association networks, accomplices, suppliers, or victim destinations."
    },
    {
        "category": "A. Subscriber Information",
        "field_name": "MSISDN",
        "standard_key": "msisdn",
        "description": "Mobile Station International Subscriber Directory Number uniquely identifying a subscription in a GSM or UMTS mobile network.",
        "typical_format": "CC + NDC + SN (Country Code + National Destination Code + Subscriber Number)",
        "investigative_relevance": "Crucial for identifying the SIM subscription and cross-referencing with Customer Acquisition Forms (CAF)."
    },
    {
        "category": "A. Subscriber Information",
        "field_name": "IMSI",
        "standard_key": "imsi",
        "description": "International Mobile Subscriber Identity. A 15-digit unique serial number stored inside the SIM card.",
        "typical_format": "MCC (3) + MNC (2-3) + MSIN (9-10), e.g. 404450912345678",
        "investigative_relevance": "Detects SIM card replacement / SIM swap frauds. When a phone number remains the same but IMSI changes, SIM has been reissued."
    },
    {
        "category": "A. Subscriber Information",
        "field_name": "IMEI",
        "standard_key": "imei",
        "description": "International Mobile Equipment Identity. A 15-digit unique electronic identifier for the physical cellular radio handset.",
        "typical_format": "TAC (8) + SNR (6) + CD (1), e.g. 864209041234567",
        "investigative_relevance": "Tracks physical handset hardware. Detects burner SIMs being rotated within the same physical device, or one suspect using multiple handsets."
    },
    {
        "category": "A. Subscriber Information",
        "field_name": "ICCID",
        "standard_key": "iccid",
        "description": "Integrated Circuit Card Identifier. 19 or 20-digit serial number physically engraved on the SIM card chip.",
        "typical_format": "89 + Country Code + Network Code + Manufacturer Serial + Checksum",
        "investigative_relevance": "Provides physical proof of the specific SIM chip manufactured and supplied to telecom distributors."
    },

    # B. Call Information
    {
        "category": "B. Call Information",
        "field_name": "Call Date & Time (Start / End)",
        "standard_key": "call_datetime",
        "description": "Exact chronological timestamp when the call setup succeeded and radio channel answered, along with termination time.",
        "typical_format": "YYYY-MM-DD HH:MM:SS (UTC or Local Telecom Switch Time)",
        "investigative_relevance": "Correlates suspect communication directly against crime scene timestamps, surveillance footage, and alibi statements."
    },
    {
        "category": "B. Call Information",
        "field_name": "Call Duration",
        "standard_key": "duration",
        "description": "Length of the connected voice transmission in seconds (billable talk time).",
        "typical_format": "Integer seconds (e.g. 184 seconds = 3m 4s)",
        "investigative_relevance": "Differentiates substantive conversations (>60s) from signaling pings (1-4s) or unanswered calls (0s)."
    },
    {
        "category": "B. Call Information",
        "field_name": "Call Direction",
        "standard_key": "direction",
        "description": "Orientation of the communication: Incoming (Mobile Terminated / MT) vs Outgoing (Mobile Originated / MO).",
        "typical_format": "Incoming, Outgoing, Forwarded, Missed",
        "investigative_relevance": "Establishes initiative: who triggered contact, command-and-control hierarchy in criminal enterprises."
    },
    {
        "category": "B. Call Information",
        "field_name": "Call Type",
        "standard_key": "call_type",
        "description": "Bearer service category utilized: Voice, SMS, VoLTE, VoWiFi, Video, GPRS/Packet Data.",
        "typical_format": "Voice, SMS, Data, Video",
        "investigative_relevance": "Reveals whether targets communicate verbally, via SMS text, or packet data sessions."
    },
    {
        "category": "B. Call Information",
        "field_name": "Termination Cause",
        "standard_key": "termination_cause",
        "description": "Network Q.850 release cause code indicating why the call ended (Normal, Subscriber Busy, Call Drop, Network Congestion).",
        "typical_format": "Normal Clearing, No Answer, Busy, Radio Link Failure, Unreachable",
        "investigative_relevance": "Confirms intentional disconnects, sudden panic hangups, cell drops due to rapid movement, or blocked callers."
    },

    # C. SMS Information
    {
        "category": "C. SMS Information",
        "field_name": "SMS Direction & Type",
        "standard_key": "sms_type",
        "description": "Short Message Service delivery: Mobile Originated SMS (MO-SMS) sent from handset, or Mobile Terminated SMS (MT-SMS) received.",
        "typical_format": "MO-SMS, MT-SMS, Flash SMS, Application-to-Peer (A2P)",
        "investigative_relevance": "Detects automated 2FA banking OTP messages, bulk messaging, or operational SMS command signals."
    },

    # D. Network & Cell Tower Information
    {
        "category": "D. Network & Cell Tower Information",
        "field_name": "Cell ID (CI)",
        "standard_key": "cell_id",
        "description": "Unique identifier assigned by the mobile operator to a specific cellular base transceiver antenna sector.",
        "typical_format": "Integer or Hexadecimal string (e.g. MUM-4001 or 58921)",
        "investigative_relevance": "Core anchor for estimating approximate geographic location and travel velocity of target handset."
    },
    {
        "category": "D. Network & Cell Tower Information",
        "field_name": "LAC / TAC",
        "standard_key": "lac_tac",
        "description": "Location Area Code (2G/3G) or Tracking Area Code (4G LTE / 5G NR). Groups multiple cell towers into a regional cluster.",
        "typical_format": "Decimal integer (e.g. LAC 4001, TAC 12010)",
        "investigative_relevance": "Validates regional telecom boundaries and cross-city travel when target transitions between LACs."
    },
    {
        "category": "D. Network & Cell Tower Information",
        "field_name": "CGI / ECGI",
        "standard_key": "cgi",
        "description": "Cell Global Identity (MCC + MNC + LAC + CI) or E-UTRAN CGI. Globally unique antenna sector address worldwide.",
        "typical_format": "404-45-4001-58921 (MCC-MNC-LAC-CI)",
        "investigative_relevance": "Definitively resolves the exact cellular transmitter internationally without operator ambiguity."
    },
    {
        "category": "D. Network & Cell Tower Information",
        "field_name": "Tower Coordinates (Lat / Long)",
        "standard_key": "latitude_longitude",
        "description": "Geographic latitude and longitude coordinates of the physical mast installation.",
        "typical_format": "Decimal degrees (e.g. Lat: 19.0664, Lon: 72.8687)",
        "investigative_relevance": "Enables mapping of serving towers on interactive geospatial maps. NOTE: Represents antenna site, not exact device GPS."
    },
    {
        "category": "D. Network & Cell Tower Information",
        "field_name": "Radio Access Technology (RAT)",
        "standard_key": "network_type",
        "description": "Cellular generation: 2G (GSM), 3G (UMTS), 4G (LTE), or 5G (NR).",
        "typical_format": "2G, 3G, 4G LTE, 5G NR",
        "investigative_relevance": "4G/5G cell radii are much tighter (100m - 1km) in urban centers compared to legacy 2G towers (up to 35km)."
    },

    # E. Roaming & Regulatory Information
    {
        "category": "E. Roaming & Regulatory Information",
        "field_name": "Roaming Status",
        "standard_key": "roaming_info",
        "description": "Indicates whether subscriber was operating on Home Public Land Mobile Network (HPLMN) or visiting a roaming partner.",
        "typical_format": "Home Network, National Roaming, International Roaming",
        "investigative_relevance": "Confirms travel beyond the home telecom circle or international border crossings."
    },
    {
        "category": "E. Roaming & Regulatory Information",
        "field_name": "Legal Evidentiary Disclaimer",
        "standard_key": "legal_disclaimer",
        "description": "Forensic caveat explaining that CDR demonstrates serving antenna connections, not physical presence.",
        "typical_format": "Legal evidentiary admissibility clause under Section 65B Indian Evidence Act / Federal Rules of Evidence",
        "investigative_relevance": "Essential in court proceedings to prevent inaccurate claims regarding pinpoint GPS device tracking."
    }
]

@router.get("/dictionary")
def get_dictionary():
    return {
        "total_fields": len(DICTIONARY_ENTRIES),
        "fields": DICTIONARY_ENTRIES
    }
