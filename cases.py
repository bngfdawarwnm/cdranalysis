import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import Case, User, InvestigationNote, AuditLog, Dataset, CDRRecord
from app.schemas import CaseCreate, CaseUpdate, CaseOut, InvestigationNoteCreate, InvestigationNoteOut
from app.auth import get_current_user

router = APIRouter(prefix="/api/cases", tags=["Investigation Case Management"])

def generate_case_id() -> str:
    now = datetime.datetime.utcnow()
    rand_suffix = str(uuid.uuid4())[:4].upper()
    return f"CASE-{now.year}-{rand_suffix}"

@router.get("", response_model=List[CaseOut])
def get_cases(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cases = db.query(Case).order_by(Case.created_at.desc()).all()
    out = []
    for c in cases:
        c_dict = {
            "id": c.id,
            "case_id": c.case_id,
            "title": c.title,
            "description": c.description,
            "investigator": c.investigator,
            "authorized_scope": c.authorized_scope,
            "warrant_reference": c.warrant_reference,
            "status": c.status,
            "watchlist_numbers": c.watchlist_numbers or [],
            "created_at": c.created_at,
            "updated_at": c.updated_at,
            "dataset_count": len(c.datasets),
            "record_count": sum(d.record_count for d in c.datasets)
        }
        out.append(c_dict)
    return out

@router.post("", response_model=CaseOut)
def create_case(case_in: CaseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c_id = generate_case_id()
    new_case = Case(
        case_id=c_id,
        title=case_in.title,
        description=case_in.description,
        investigator=case_in.investigator,
        authorized_scope=case_in.authorized_scope,
        warrant_reference=case_in.warrant_reference,
        status="Active",
        created_by_id=current_user.id,
        watchlist_numbers=[]
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)

    # Initial investigation note
    init_note = InvestigationNote(
        case_id=new_case.id,
        author=current_user.full_name or current_user.username,
        title="Case Initiated & Authorization Logged",
        content=f"Investigation opened with scope: '{new_case.authorized_scope or 'Standard Telecom Forensic Analysis'}'. Assigned Lead: {new_case.investigator}.",
        category="Legal Authorization"
    )
    db.add(init_note)

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="CASE_CREATED",
        target_type="CASE",
        target_id=new_case.case_id,
        details=f"Created case '{new_case.title}' with ID {new_case.case_id}"
    )
    db.add(audit)
    db.commit()

    return {
        "id": new_case.id,
        "case_id": new_case.case_id,
        "title": new_case.title,
        "description": new_case.description,
        "investigator": new_case.investigator,
        "authorized_scope": new_case.authorized_scope,
        "warrant_reference": new_case.warrant_reference,
        "status": new_case.status,
        "watchlist_numbers": new_case.watchlist_numbers or [],
        "created_at": new_case.created_at,
        "updated_at": new_case.updated_at,
        "dataset_count": 0,
        "record_count": 0
    }

@router.get("/{case_id}")
def get_case_details(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.query(Case).filter(Case.id == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Investigation case not found")
    
    datasets = [
        {
            "id": d.id, "filename": d.filename, "record_count": d.record_count,
            "upload_time": d.upload_time.strftime("%Y-%m-%d %H:%M"), "operator": d.operator_name,
            "is_synthetic": d.is_synthetic
        }
        for d in c.datasets
    ]

    notes = [
        {
            "id": n.id, "author": n.author, "title": n.title, "content": n.content,
            "category": n.category, "created_at": n.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for n in c.notes
    ]

    return {
        "id": c.id,
        "case_id": c.case_id,
        "title": c.title,
        "description": c.description,
        "investigator": c.investigator,
        "authorized_scope": c.authorized_scope,
        "warrant_reference": c.warrant_reference,
        "status": c.status,
        "watchlist_numbers": c.watchlist_numbers or [],
        "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "datasets": datasets,
        "notes": notes
    }

@router.put("/{case_id}/watchlist")
def update_watchlist(case_id: int, numbers: List[str], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.query(Case).filter(Case.id == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")
    
    c.watchlist_numbers = numbers
    db.commit()
    return {"status": "success", "watchlist_numbers": c.watchlist_numbers}

@router.post("/{case_id}/notes", response_model=InvestigationNoteOut)
def add_note(case_id: int, note_in: InvestigationNoteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.query(Case).filter(Case.id == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")
    
    note = InvestigationNote(
        case_id=case_id,
        author=current_user.full_name or current_user.username,
        title=note_in.title,
        content=note_in.content,
        category=note_in.category or "Analytical Finding"
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note
