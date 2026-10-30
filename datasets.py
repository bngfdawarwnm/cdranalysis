import os
import shutil
import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.database import get_db
from app.config import UPLOADS_DIR
from app.models import Dataset, CDRRecord, CellTower, Case, User, AuditLog
from app.schemas import DatasetOut, ColumnMappingRequest
from app.auth import get_current_user
from app.cdr_parser import (
    auto_detect_columns, read_preview_data, process_raw_records
)
from app.synthetic_generator import generate_synthetic_cdr, TOWERS
import csv
import json
try:
    import openpyxl
except ImportError:
    openpyxl = None

router = APIRouter(prefix="/api/datasets", tags=["CDR Datasets & Ingestion"])

@router.get("", response_model=List[DatasetOut])
def list_datasets(case_id: Optional[int] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Dataset)
    if case_id:
        query = query.filter(Dataset.case_id == case_id)
    return query.order_by(Dataset.upload_time.desc()).all()

@router.post("/upload")
async def upload_cdr_file(
    file: UploadFile = File(...),
    case_id: Optional[int] = Form(None),
    operator_name: Optional[str] = Form("Multi-Carrier / Generic"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".csv", ".xlsx", ".xls", ".json", ".txt"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported format. Allowed formats: CSV, XLSX, XLS, JSON, TXT"
        )

    timestamp_str = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    clean_filename = f"{timestamp_str}_{file.filename.replace(' ', '_')}"
    file_path = UPLOADS_DIR / clean_filename

    # Save to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Read preview and auto detect mapping
    try:
        headers, preview_rows, total_rows = read_preview_data(str(file_path), nrows=10)
        detected_mapping = auto_detect_columns(headers)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Failed to parse file preview: {str(e)}")

    # Create dataset record
    dataset = Dataset(
        case_id=case_id,
        filename=file.filename,
        stored_path=str(file_path),
        file_format=ext[1:].upper(),
        record_count=total_rows,
        operator_name=operator_name or "Standard Carrier",
        status="Uploaded",
        column_mapping=detected_mapping,
        summary_stats={"preview_count": len(preview_rows), "total_detected": total_rows},
        is_synthetic=False
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="FILE_UPLOAD",
        target_type="DATASET",
        target_id=str(dataset.id),
        details=f"Uploaded file {file.filename} with {total_rows} estimated records"
    )
    db.add(audit)
    db.commit()

    return {
        "dataset_id": dataset.id,
        "filename": dataset.filename,
        "format": dataset.file_format,
        "estimated_records": total_rows,
        "headers": headers,
        "preview_rows": preview_rows,
        "detected_mapping": detected_mapping
    }

@router.post("/process")
def process_uploaded_dataset(
    req: ColumnMappingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == req.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not dataset.stored_path or not os.path.exists(dataset.stored_path):
        raise HTTPException(status_code=400, detail="Stored source file not found on disk")

    ext = os.path.splitext(dataset.stored_path)[1].lower()
    raw_rows: List[Dict[str, Any]] = []
    try:
        if ext in [".xlsx", ".xls"] and openpyxl:
            wb = openpyxl.load_workbook(dataset.stored_path, read_only=True, data_only=True)
            sheet = wb.active
            all_rows = list(sheet.iter_rows(values_only=True))
            if all_rows:
                headers = [str(c or '').strip() for c in all_rows[0]]
                for r in all_rows[1:]:
                    row_dict = {}
                    for idx, h in enumerate(headers):
                        val = r[idx] if idx < len(r) else ''
                        row_dict[h] = str(val) if val is not None else ''
                    raw_rows.append(row_dict)
            wb.close()
        elif ext == ".json":
            with open(dataset.stored_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    data = data.get("records", data.get("data", []))
                raw_rows = data if isinstance(data, list) else []
        else:
            with open(dataset.stored_path, 'r', encoding='utf-8', errors='ignore') as f:
                sample = f.read(4096)
                f.seek(0)
                delimiter = '\t' if '\t' in sample else ('|' if '|' in sample else (';' if ';' in sample else ','))
                reader = csv.DictReader(f, delimiter=delimiter)
                for r in reader:
                    raw_rows.append({k.strip(): (v or '').strip() for k, v in r.items()})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    # Process and validate records
    record_dicts = process_raw_records(raw_rows, req.mapping, dataset.id, dataset.case_id)
    
    # Bulk insert CDR records
    cdr_objs = [CDRRecord(**rd) for rd in record_dicts]
    db.bulk_save_objects(cdr_objs)

    # Populate cell towers
    for rd in record_dicts:
        if rd.get("cell_id") and rd.get("latitude") and rd.get("longitude"):
            cid = rd["cell_id"]
            existing = db.query(CellTower).filter(CellTower.cell_id == cid).first()
            if not existing:
                tower = CellTower(
                    cell_id=cid,
                    lac=rd.get("lac"),
                    tac=rd.get("tac"),
                    cgi=rd.get("cgi"),
                    site_name=rd.get("site_id") or f"Tower {cid}",
                    latitude=rd["latitude"],
                    longitude=rd["longitude"],
                    technology=rd.get("network_type", "4G LTE"),
                    operator=rd.get("operator", "Universal Carrier"),
                    observation_count=1
                )
                db.add(tower)
            else:
                existing.observation_count += 1

    dataset.record_count = len(record_dicts)
    dataset.status = "Processed"
    dataset.column_mapping = req.mapping
    db.commit()

    return {
        "status": "success",
        "dataset_id": dataset.id,
        "processed_records": len(record_dicts),
        "message": f"Successfully processed and indexed {len(record_dicts)} records."
    }

@router.post("/generate-synthetic")
def create_synthetic_demo_dataset(
    case_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Instantly generate and index 450+ realistic forensic CDR records with criminal network patterns."""
    # Ensure target case exists
    target_case = None
    if case_id:
        target_case = db.query(Case).filter(Case.id == case_id).first()
    
    if not target_case:
        # Create default case if none exists
        target_case = db.query(Case).first()
        if not target_case:
            target_case = Case(
                case_id="CASE-2026-CITADEL",
                title="Operation Citadel: Telecom Surveillance & Syndicate Network",
                description="Comprehensive digital forensics analysis into suspected organized burner phone communications, late-night coordination, and multi-IMSI device hopping.",
                investigator=current_user.full_name or "Insp. Vikramaditya Rathore",
                authorized_scope="Court Warrant #CR-2026/8941 - Full Telecommunications Intercept & Forensic Analysis",
                warrant_reference="WARRANT-DEL-8941",
                status="Active",
                created_by_id=current_user.id,
                watchlist_numbers=["+919820112345", "+919820154321", "+919988776655"]
            )
            db.add(target_case)
            db.commit()
            db.refresh(target_case)

    # Pre-seed cell towers in catalog
    for t_data in TOWERS:
        existing = db.query(CellTower).filter(CellTower.cell_id == t_data["cell_id"]).first()
        if not existing:
            ct = CellTower(
                cell_id=t_data["cell_id"],
                lac=t_data["lac"],
                tac=t_data["tac"],
                cgi=f"404-45-{t_data['lac']}-{t_data['cell_id'].split('-')[1]}",
                site_name=t_data["site"],
                latitude=t_data["lat"],
                longitude=t_data["lon"],
                technology=t_data["tech"],
                operator=t_data["op"],
                observation_count=25
            )
            db.add(ct)
    db.commit()

    # Generate synthetic records
    raw_records = generate_synthetic_cdr(case_id=target_case.id, record_count=450)

    dataset = Dataset(
        case_id=target_case.id,
        filename="SYNTHETIC_TELCO_CDR_OPERATION_CITADEL.csv",
        stored_path=None,
        file_format="CSV",
        record_count=len(raw_records),
        operator_name="Multi-Carrier (Airtel / Jio / Vi / BSNL)",
        status="Processed",
        column_mapping={"calling_number": "A_PARTY", "called_number": "B_PARTY", "duration": "DURATION_SEC"},
        summary_stats={"scenario": "Operation Citadel Criminal Syndicate", "sim_swaps": 2, "burst_windows": 3},
        is_synthetic=True
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    # Insert records
    cdr_objs = []
    for r in raw_records:
        r["dataset_id"] = dataset.id
        r["case_id"] = target_case.id
        cdr_objs.append(CDRRecord(**r))

    db.bulk_save_objects(cdr_objs)
    db.commit()

    # Add case note
    note = InvestigationNote(
        case_id=target_case.id,
        author="System Forensic Automator",
        title="Forensic Dataset Seeded: Operation Citadel",
        content="Imported 450 synthetic Call Detail Records simulating target '+919820112345' across 10 Mumbai/Navi Mumbai cell towers, highlighting SIM swapping on IMEI 864209041234567, late-night coordination, and burner pings.",
        category="Dataset Import"
    )
    db.add(note)

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="DEMO_DATASET_LOADED",
        target_type="DATASET",
        target_id=str(dataset.id),
        details=f"Loaded 450 synthetic records for case {target_case.case_id}"
    )
    db.add(audit)
    db.commit()

    return {
        "status": "success",
        "case_id": target_case.id,
        "dataset_id": dataset.id,
        "record_count": len(raw_records),
        "message": "Synthetic investigation dataset successfully initialized with realistic patterns."
    }

@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    d = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Remove records
    db.query(CDRRecord).filter(CDRRecord.dataset_id == dataset_id).delete()
    if d.stored_path and os.path.exists(d.stored_path):
        try:
            os.remove(d.stored_path)
        except Exception:
            pass

    db.delete(d)
    db.commit()
    return {"status": "success", "message": f"Dataset {dataset_id} deleted."}
