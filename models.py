import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    full_name = Column(String(128), nullable=True)
    role = Column(String(32), default="Analyst", nullable=False)  # Admin, Lead Investigator, Analyst, Viewer
    department = Column(String(128), default="Telecom Cyber Forensics Cell", nullable=True)
    badge_number = Column(String(64), default="TCFC-0914", nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    cases = relationship("Case", back_populates="creator")
    audit_logs = relationship("AuditLog", back_populates="user")


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    investigator = Column(String(128), nullable=False)
    authorized_scope = Column(Text, nullable=True)
    warrant_reference = Column(String(128), nullable=True)
    status = Column(String(32), default="Active")  # Active, Under Review, Closed, Archived
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    watchlist_numbers = Column(JSON, default=list)  # list of strings
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    creator = relationship("User", back_populates="cases")
    datasets = relationship("Dataset", back_populates="case", cascade="all, delete-orphan")
    notes = relationship("InvestigationNote", back_populates="case", cascade="all, delete-orphan")
    records = relationship("CDRRecord", back_populates="case", cascade="all, delete-orphan")


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=True)
    filename = Column(String(256), nullable=False)
    stored_path = Column(String(512), nullable=True)
    file_format = Column(String(32), default="CSV")
    record_count = Column(Integer, default=0)
    operator_name = Column(String(64), default="Standard Telecom / Multi-Carrier")
    upload_time = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(32), default="Processed")  # Uploaded, Processing, Processed, Failed
    column_mapping = Column(JSON, default=dict)
    summary_stats = Column(JSON, default=dict)
    is_synthetic = Column(Boolean, default=False)

    case = relationship("Case", back_populates="datasets")
    records = relationship("CDRRecord", back_populates="dataset", cascade="all, delete-orphan")


class CDRRecord(Base):
    __tablename__ = "cdr_records"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), index=True, nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="SET NULL"), index=True, nullable=True)

    # Calling / Called parties
    calling_number = Column(String(64), index=True, nullable=False)  # A Party / MSISDN
    called_number = Column(String(64), index=True, nullable=False)   # B Party / Dialed digits

    # Timestamps & duration
    call_date = Column(String(32), index=True, nullable=True)       # YYYY-MM-DD
    call_time = Column(String(32), nullable=True)                   # HH:MM:SS
    call_datetime = Column(DateTime, index=True, nullable=False)
    duration = Column(Integer, default=0)                           # In seconds

    # Call / Message characteristics
    call_type = Column(String(32), default="Voice")                 # Voice, SMS, Data, Video, VoLTE
    direction = Column(String(32), default="Outgoing")              # Incoming, Outgoing, Forwarded, Missed
    sms_type = Column(String(32), nullable=True)                    # MO-SMS, MT-SMS, Flash, OTP
    termination_cause = Column(String(64), default="Normal Clearing") # Normal, Call Drop, Busy, No Answer, Unreachable

    # Hardware & Subscriber identifiers
    imei = Column(String(32), index=True, nullable=True)
    imsi = Column(String(32), index=True, nullable=True)

    # Cellular Network identifiers
    cell_id = Column(String(64), index=True, nullable=True)
    lac = Column(String(32), nullable=True)                         # Location Area Code
    tac = Column(String(32), nullable=True)                         # Tracking Area Code (LTE/5G)
    cgi = Column(String(64), nullable=True)                         # Cell Global Identity
    ecgi = Column(String(64), nullable=True)                        # E-UTRAN CGI
    site_id = Column(String(64), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Roaming and Network
    network_type = Column(String(32), default="4G LTE")             # 2G, 3G, 4G, 5G
    roaming_info = Column(String(64), default="Home Network")       # Home, National Roaming, International
    operator = Column(String(64), default="Telecom Operator")

    # Data validation flags
    is_valid = Column(Boolean, default=True)
    validation_flags = Column(JSON, default=list)

    dataset = relationship("Dataset", back_populates="records")
    case = relationship("Case", back_populates="records")


# Composite indexes for fast analytics queries
Index("idx_records_party_a", CDRRecord.calling_number, CDRRecord.call_datetime)
Index("idx_records_party_b", CDRRecord.called_number, CDRRecord.call_datetime)
Index("idx_records_imei", CDRRecord.imei, CDRRecord.call_datetime)
Index("idx_records_cell", CDRRecord.cell_id, CDRRecord.call_datetime)


class CellTower(Base):
    __tablename__ = "cell_towers"

    id = Column(Integer, primary_key=True, index=True)
    cell_id = Column(String(64), unique=True, index=True, nullable=False)
    lac = Column(String(32), nullable=True)
    tac = Column(String(32), nullable=True)
    cgi = Column(String(64), nullable=True)
    site_name = Column(String(128), nullable=True)
    address = Column(String(256), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    azimuth = Column(Integer, default=0)
    technology = Column(String(32), default="4G LTE")
    operator = Column(String(64), default="Universal Carrier")
    observation_count = Column(Integer, default=1)


class InvestigationNote(Base):
    __tablename__ = "investigation_notes"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    author = Column(String(128), nullable=False)
    title = Column(String(256), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(64), default="Analytical Finding") # Finding, Lead, Surveillance, Legal
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    case = relationship("Case", back_populates="notes")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    username = Column(String(64), default="System")
    action = Column(String(64), nullable=False)  # Login, Upload, Search, Export, Delete, CaseCreate
    target_type = Column(String(64), nullable=True) # Dataset, Number, Report, Case
    target_id = Column(String(128), nullable=True)
    ip_address = Column(String(64), default="127.0.0.1")
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")
