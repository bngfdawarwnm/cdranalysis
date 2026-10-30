from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import User, AuditLog
from app.auth import get_current_user
from app.reports import generate_excel_report, generate_pdf_report

router = APIRouter(prefix="/api/reports", tags=["Forensic Report Exports"])

@router.get("/pdf")
def export_pdf(
    case_id: Optional[int] = None,
    dataset_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate and download official PDF forensic intelligence report."""
    try:
        pdf_stream = generate_pdf_report(db, case_id=case_id, dataset_id=dataset_id)
        
        # Log export in audit
        audit = AuditLog(
            user_id=current_user.id,
            username=current_user.username,
            action="EXPORT_PDF",
            target_type="REPORT",
            details=f"Exported forensic PDF report for case_id={case_id}"
        )
        db.add(audit)
        db.commit()

        filename = f"CDR_Forensic_Report_{case_id or 'General'}.pdf"
        return Response(
            content=pdf_stream.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

@router.get("/excel")
def export_excel(
    case_id: Optional[int] = None,
    dataset_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate and download multi-sheet Excel analytical workbook."""
    try:
        excel_stream = generate_excel_report(db, case_id=case_id, dataset_id=dataset_id)

        audit = AuditLog(
            user_id=current_user.id,
            username=current_user.username,
            action="EXPORT_EXCEL",
            target_type="REPORT",
            details=f"Exported analytical Excel workbook for case_id={case_id}"
        )
        db.add(audit)
        db.commit()

        filename = f"CDR_Analytics_Workbook_{case_id or 'General'}.xlsx"
        return Response(
            content=excel_stream.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Excel: {str(e)}")
