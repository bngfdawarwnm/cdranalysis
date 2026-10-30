from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from typing import Optional, List, Dict, Any

from app.database import get_db
from app.models import CDRRecord, Case, User
from app.auth import get_current_user
from app.analytics import (
    get_dashboard_summary, get_number_analysis, get_incoming_outgoing_analysis,
    get_contact_network_graph, get_imei_imsi_analysis, get_cell_tower_analytics,
    get_anomaly_indicators, get_two_number_comparison
)

router = APIRouter(prefix="/api/analytics", tags=["Forensic Analytics Engine"])

@router.get("/dashboard")
def dashboard_metrics(
    case_id: Optional[int] = None,
    dataset_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_dashboard_summary(db, case_id=case_id, dataset_id=dataset_id, start_date=start_date, end_date=end_date)

@router.get("/number-profile")
def number_profile(
    number: str = Query(..., description="Mobile number to investigate"),
    case_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = get_number_analysis(db, number=number.strip(), case_id=case_id)
    return res

@router.get("/incoming-outgoing")
def incoming_outgoing(
    case_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_incoming_outgoing_analysis(db, case_id=case_id)

@router.get("/network-graph")
def network_graph(
    target_number: Optional[str] = None,
    case_id: Optional[int] = None,
    max_nodes: int = 40,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    clean_target = target_number.strip() if target_number else None
    return get_contact_network_graph(db, target_number=clean_target, case_id=case_id, max_nodes=max_nodes)

@router.get("/imei-imsi")
def imei_imsi(
    query_term: Optional[str] = None,
    case_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_imei_imsi_analysis(db, query_term=query_term, case_id=case_id)

@router.get("/cell-towers")
def cell_towers(
    case_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_cell_tower_analytics(db, case_id=case_id)

@router.get("/anomalies")
def anomalies(
    case_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_anomaly_indicators(db, case_id=case_id)

@router.get("/comparative")
def comparative_analysis(
    num_a: str = Query(..., description="Target Mobile Number A"),
    num_b: str = Query(..., description="Target Mobile Number B"),
    case_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_two_number_comparison(db, num_a.strip(), num_b.strip(), case_id=case_id)

@router.get("/records")
def query_records(
    case_id: Optional[int] = None,
    dataset_id: Optional[int] = None,
    search: Optional[str] = None,
    number: Optional[str] = None,
    imei: Optional[str] = None,
    imsi: Optional[str] = None,
    cell_id: Optional[str] = None,
    call_type: Optional[str] = None,
    direction: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Universal multi-parameter search across all CDR records with pagination."""
    query = db.query(CDRRecord)

    if case_id:
        query = query.filter(CDRRecord.case_id == case_id)
    if dataset_id:
        query = query.filter(CDRRecord.dataset_id == dataset_id)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(or_(
            CDRRecord.calling_number.like(s),
            CDRRecord.called_number.like(s),
            CDRRecord.imei.like(s),
            CDRRecord.imsi.like(s),
            CDRRecord.cell_id.like(s),
            CDRRecord.site_id.like(s)
        ))

    if number:
        n = number.strip()
        query = query.filter(or_(CDRRecord.calling_number == n, CDRRecord.called_number == n))
    if imei:
        query = query.filter(CDRRecord.imei == imei.strip())
    if imsi:
        query = query.filter(CDRRecord.imsi == imsi.strip())
    if cell_id:
        query = query.filter(CDRRecord.cell_id == cell_id.strip())
    if call_type:
        query = query.filter(CDRRecord.call_type == call_type)
    if direction:
        query = query.filter(CDRRecord.direction == direction)
    if start_date:
        query = query.filter(CDRRecord.call_date >= start_date)
    if end_date:
        query = query.filter(CDRRecord.call_date <= end_date)

    total = query.count()
    records = query.order_by(desc(CDRRecord.call_datetime)).offset((page - 1) * limit).limit(limit).all()

    items = [
        {
            "id": r.id,
            "calling_number": r.calling_number,
            "called_number": r.called_number,
            "call_date": r.call_date,
            "call_time": r.call_time,
            "call_datetime": r.call_datetime.strftime("%Y-%m-%d %H:%M:%S") if r.call_datetime else "",
            "duration": r.duration,
            "call_type": r.call_type,
            "direction": r.direction,
            "sms_type": r.sms_type,
            "termination_cause": r.termination_cause,
            "imei": r.imei,
            "imsi": r.imsi,
            "cell_id": r.cell_id,
            "lac": r.lac,
            "tac": r.tac,
            "cgi": r.cgi,
            "site_id": r.site_id,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "network_type": r.network_type,
            "roaming_info": r.roaming_info,
            "operator": r.operator,
            "is_valid": r.is_valid,
            "validation_flags": r.validation_flags or []
        }
        for r in records
    ]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 1,
        "records": items
    }
