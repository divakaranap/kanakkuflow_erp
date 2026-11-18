from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from backend.app.models.accounting import AccountCategory, AccountType


class AccountBase(BaseModel):
    code: str
    name: str
    category: AccountCategory
    account_type: AccountType
    is_active: bool = True
    description: Optional[str] = None


class AccountCreate(AccountBase):
    pass


class AccountResponse(AccountBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JournalEntryLineCreate(BaseModel):
    account_id: str
    debit_paise: int = Field(default=0, ge=0)
    credit_paise: int = Field(default=0, ge=0)
    line_narration: Optional[str] = None


class JournalEntryLineResponse(BaseModel):
    id: str
    entry_id: str
    account_id: str
    account_code: Optional[str] = None
    account_name: Optional[str] = None
    debit_paise: int
    credit_paise: int
    line_narration: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class JournalEntryCreate(BaseModel):
    entry_date: Optional[date] = None
    source_module: str = "MANUAL"
    source_document_id: Optional[str] = None
    source_reference: Optional[str] = None
    narration: str
    lines: List[JournalEntryLineCreate]


class JournalEntryResponse(BaseModel):
    id: str
    entry_number: str
    entry_date: date
    source_module: str
    source_document_id: Optional[str] = None
    source_reference: Optional[str] = None
    narration: str
    total_debit_paise: int
    total_credit_paise: int
    is_posted: bool
    created_by: int
    created_at: datetime
    lines: List[JournalEntryLineResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TrialBalanceRow(BaseModel):
    account_id: str
    account_code: str
    account_name: str
    category: AccountCategory
    account_type: AccountType
    total_debit_paise: int
    total_credit_paise: int
    net_debit_paise: int
    net_credit_paise: int


class TrialBalanceResponse(BaseModel):
    as_of_date: date
    is_balanced: bool
    grand_total_debit_paise: int
    grand_total_credit_paise: int
    difference_paise: int
    accounts: List[TrialBalanceRow] = Field(default_factory=list)


class GeneralLedgerRow(BaseModel):
    id: str
    entry_id: str
    entry_number: str
    entry_date: date
    source_module: str
    source_reference: Optional[str] = None
    narration: str
    line_narration: Optional[str] = None
    debit_paise: int
    credit_paise: int
    running_balance_paise: int


class GeneralLedgerResponse(BaseModel):
    account_id: str
    account_code: str
    account_name: str
    category: AccountCategory
    total_debit_paise: int
    total_credit_paise: int
    closing_balance_paise: int
    rows: List[GeneralLedgerRow] = Field(default_factory=list)


class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[int] = None
    username: str
    role: str
    action: str
    entity_type: str
    entity_id: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
