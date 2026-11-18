from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.dependencies import get_current_user, require_roles
from backend.app.models.user import User, UserRole
from backend.app.models.accounting import (
    Account,
    JournalEntry,
    JournalEntryLine,
    AuditLog,
)
from backend.app.schemas.accounting import (
    AccountCreate,
    AccountResponse,
    JournalEntryCreate,
    JournalEntryResponse,
    JournalEntryLineResponse,
    TrialBalanceResponse,
    GeneralLedgerResponse,
    AuditLogResponse,
)
from backend.app.services.accounting_service import (
    seed_chart_of_accounts,
    create_journal_entry,
    get_trial_balance,
    get_general_ledger,
)
from backend.app.services.audit_service import log_audit_event

router = APIRouter(prefix="/accounting", tags=["accounting"])


@router.get(
    "/accounts",
    response_model=List[AccountResponse],
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR, UserRole.SALESMAN]))],
)
def list_accounts(db: Session = Depends(get_db)):
    """List Chart of Accounts (auto-seeding defaults if needed)."""
    seed_chart_of_accounts(db)
    accounts = db.query(Account).order_by(Account.code.asc()).all()
    return accounts


@router.post(
    "/accounts",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN]))],
)
def create_account(
    data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new Chart of Accounts ledger code."""
    exists = db.query(Account).filter((Account.code == data.code) | (Account.name == data.name)).first()
    if exists:
        raise HTTPException(status_code=400, detail="Account with this code or name already exists")

    account = Account(**data.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)

    log_audit_event(db, current_user, "CREATE", "ACCOUNT", account.id, f"Created account {account.code} - {account.name}")
    return account


@router.get(
    "/journals",
    response_model=List[JournalEntryResponse],
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR]))],
)
def list_journal_entries(
    source_module: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """List double-entry journal vouchers."""
    query = (
        db.query(JournalEntry)
        .options(joinedload(JournalEntry.lines).joinedload(JournalEntryLine.account))
        .order_by(desc(JournalEntry.entry_date), desc(JournalEntry.created_at))
    )
    if source_module:
        query = query.filter(JournalEntry.source_module == source_module)
    if from_date:
        query = query.filter(JournalEntry.entry_date >= from_date)
    if to_date:
        query = query.filter(JournalEntry.entry_date <= to_date)

    entries = query.all()
    return [
        JournalEntryResponse(
            id=e.id,
            entry_number=e.entry_number,
            entry_date=e.entry_date,
            source_module=e.source_module,
            source_document_id=e.source_document_id,
            source_reference=e.source_reference,
            narration=e.narration,
            total_debit_paise=e.total_debit_paise,
            total_credit_paise=e.total_credit_paise,
            is_posted=e.is_posted,
            created_by=e.created_by,
            created_at=e.created_at,
            lines=[
                JournalEntryLineResponse(
                    id=l.id,
                    entry_id=l.entry_id,
                    account_id=l.account_id,
                    account_code=l.account.code if l.account else None,
                    account_name=l.account.name if l.account else None,
                    debit_paise=l.debit_paise,
                    credit_paise=l.credit_paise,
                    line_narration=l.line_narration,
                )
                for l in e.lines
            ],
        )
        for e in entries
    ]


@router.post(
    "/journals",
    response_model=JournalEntryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN]))],
)
def create_journal(
    data: JournalEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a manual double-entry journal voucher."""
    entry = create_journal_entry(db, data, current_user.id)
    log_audit_event(
        db,
        current_user,
        "POST",
        "JOURNAL_ENTRY",
        entry.id,
        f"Posted manual journal {entry.entry_number} for ₹{entry.total_debit_paise/100:.2f}",
    )
    return JournalEntryResponse(
        id=entry.id,
        entry_number=entry.entry_number,
        entry_date=entry.entry_date,
        source_module=entry.source_module,
        source_document_id=entry.source_document_id,
        source_reference=entry.source_reference,
        narration=entry.narration,
        total_debit_paise=entry.total_debit_paise,
        total_credit_paise=entry.total_credit_paise,
        is_posted=entry.is_posted,
        created_by=entry.created_by,
        created_at=entry.created_at,
        lines=[
            JournalEntryLineResponse(
                id=l.id,
                entry_id=l.entry_id,
                account_id=l.account_id,
                account_code=l.account.code if l.account else None,
                account_name=l.account.name if l.account else None,
                debit_paise=l.debit_paise,
                credit_paise=l.credit_paise,
                line_narration=l.line_narration,
            )
            for l in entry.lines
        ],
    )


@router.get(
    "/trial-balance",
    response_model=TrialBalanceResponse,
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR]))],
)
def get_tb(
    as_of: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """Calculate Trial Balance across all accounts."""
    return get_trial_balance(db, as_of)


@router.get(
    "/general-ledger/{account_id}",
    response_model=GeneralLedgerResponse,
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR]))],
)
def get_gl(
    account_id: str,
    db: Session = Depends(get_db),
):
    """Fetch General Ledger statement for an account."""
    return get_general_ledger(db, account_id)


@router.get(
    "/audit-logs",
    response_model=List[AuditLogResponse],
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.AUDITOR]))],
)
def list_audit_logs(
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    """Fetch chronological system audit log entries for statutory audit."""
    query = db.query(AuditLog).order_by(desc(AuditLog.created_at))
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    logs = query.limit(limit).all()
    return logs
