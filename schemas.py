from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "Analyst"
    department: Optional[str] = "Telecom Cyber Forensics Cell"
    badge_number: Optional[str] = "TCFC-0914"

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    department: Optional[str]
    badge_number: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Case Schemas
class CaseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    investigator: str
    authorized_scope: Optional[str] = None
    warrant_reference: Optional[str] = None

class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    investigator: Optional[str] = None
    authorized_scope: Optional[str] = None
    warrant_reference: Optional[str] = None
    status: Optional[str] = None
    watchlist_numbers: Optional[List[str]] = None

class InvestigationNoteCreate(BaseModel):
    title: str
    content: str
    category: Optional[str] = "Analytical Finding"

class InvestigationNoteOut(BaseModel):
    id: int
    case_id: int
    author: str
    title: str
    content: str
    category: str
    created_at: datetime

    class Config:
        from_attributes = True

class CaseOut(BaseModel):
    id: int
    case_id: str
    title: str
    description: Optional[str]
    investigator: str
    authorized_scope: Optional[str]
    warrant_reference: Optional[str]
    status: str
    watchlist_numbers: List[str]
    created_at: datetime
    updated_at: datetime
    dataset_count: Optional[int] = 0
    record_count: Optional[int] = 0

    class Config:
        from_attributes = True

# Dataset & Column Mapping Schemas
class ColumnMappingRequest(BaseModel):
    dataset_id: int
    mapping: Dict[str, str]

class DatasetOut(BaseModel):
    id: int
    case_id: Optional[int]
    filename: str
    file_format: str
    record_count: int
    operator_name: str
    upload_time: datetime
    status: str
    column_mapping: Dict[str, Any]
    summary_stats: Dict[str, Any]
    is_synthetic: bool

    class Config:
        from_attributes = True

# CDR Record Schemas
class CDRRecordOut(BaseModel):
    id: int
    dataset_id: int
    case_id: Optional[int]
    calling_number: str
    called_number: str
    call_date: Optional[str]
    call_time: Optional[str]
    call_datetime: datetime
    duration: int
    call_type: str
    direction: str
    sms_type: Optional[str]
    termination_cause: Optional[str]
    imei: Optional[str]
    imsi: Optional[str]
    cell_id: Optional[str]
    lac: Optional[str]
    tac: Optional[str]
    cgi: Optional[str]
    site_id: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    network_type: Optional[str]
    roaming_info: Optional[str]
    operator: Optional[str]
    is_valid: bool
    validation_flags: List[str]

    class Config:
        from_attributes = True
