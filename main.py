import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import engine, Base, SessionLocal
from app.auth import init_default_users
from app.models import Case, Dataset, CDRRecord, CellTower, User
from app.synthetic_generator import generate_synthetic_cdr, TOWERS
from app.routers import auth, cases, datasets, analytics, reports, reference

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CDR Intelligence & Analysis System",
    description="Advanced Telecommunications Forensic Intelligence & Digital Network Analysis Platform",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(datasets.router)
app.include_router(analytics.router)
app.include_router(reports.router)
app.include_router(reference.router)

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        # 1. Initialize default forensic users
        init_default_users(db)

        # 2. Check if a default case and dataset exist; if empty, seed automatically
        existing_cases = db.query(Case).count()
        if existing_cases == 0:
            admin_user = db.query(User).filter(User.username == "lead_investigator").first()
            user_id = admin_user.id if admin_user else 1

            # Seed cell tower catalog
            for t_data in TOWERS:
                existing_t = db.query(CellTower).filter(CellTower.cell_id == t_data["cell_id"]).first()
                if not existing_t:
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
                        observation_count=35
                    )
                    db.add(ct)
            db.commit()

            # Create default investigation case
            demo_case = Case(
                case_id="CASE-2026-CITADEL",
                title="Operation Citadel: Telecom Surveillance & Syndicate Network",
                description="Comprehensive digital forensics analysis investigating suspected organized burner phone communications, late-night coordination windows, and multi-IMSI device hopping.",
                investigator="Insp. Vikramaditya Rathore",
                authorized_scope="Court Warrant #CR-2026/8941 - Full Telecommunications Intercept & Forensic Analysis",
                warrant_reference="WARRANT-DEL-8941",
                status="Active",
                created_by_id=user_id,
                watchlist_numbers=["+919820112345", "+919820154321", "+919988776655"]
            )
            db.add(demo_case)
            db.commit()
            db.refresh(demo_case)

            # Generate synthetic records
            raw_records = generate_synthetic_cdr(case_id=demo_case.id, record_count=450)
            dataset = Dataset(
                case_id=demo_case.id,
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

            cdr_objs = []
            for r in raw_records:
                r["dataset_id"] = dataset.id
                r["case_id"] = demo_case.id
                cdr_objs.append(CDRRecord(**r))
            db.bulk_save_objects(cdr_objs)
            db.commit()
    finally:
        db.close()

@app.get("/api/health")
def healthcheck():
    return {
        "status": "healthy",
        "system": "CDR Intelligence & Analysis System",
        "engine": "FastAPI + SQLAlchemy + Forensic Parser 2.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
