import enum
from datetime import date, datetime
from typing import Optional, List
from uuid import uuid4
from sqlalchemy import String, Date, DateTime, BigInteger, Enum, ForeignKey, Text, Boolean, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TimestampMixin


class AccountCategory(str, enum.Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"


class AccountType(str, enum.Enum):
    # Assets
    CASH_BANK = "CASH_BANK"
    ACCOUNTS_RECEIVABLE = "ACCOUNTS_RECEIVABLE"
    RAW_MATERIAL_INVENTORY = "RAW_MATERIAL_INVENTORY"
    PACKAGING_INVENTORY = "PACKAGING_INVENTORY"
    FINISHED_GOODS_INVENTORY = "FINISHED_GOODS_INVENTORY"
    INPUT_CGST = "INPUT_CGST"
    INPUT_SGST = "INPUT_SGST"
    INPUT_IGST = "INPUT_IGST"

    # Liabilities
    ACCOUNTS_PAYABLE = "ACCOUNTS_PAYABLE"
    OUTPUT_CGST = "OUTPUT_CGST"
    OUTPUT_SGST = "OUTPUT_SGST"
    OUTPUT_IGST = "OUTPUT_IGST"

    # Equity
    OWNERS_CAPITAL = "OWNERS_CAPITAL"
    RETAINED_EARNINGS = "RETAINED_EARNINGS"

    # Revenue
    SALES_REVENUE = "SALES_REVENUE"
    DISCOUNT_ALLOWED = "DISCOUNT_ALLOWED"

    # Expenses
    COGS = "COGS"
    DIRECT_LABOUR = "DIRECT_LABOUR"
    FACTORY_OVERHEAD = "FACTORY_OVERHEAD"
    YIELD_VARIANCE_EXPENSE = "YIELD_VARIANCE_EXPENSE"


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category: Mapped[AccountCategory] = mapped_column(
        Enum(AccountCategory, name="account_category_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    account_type: Mapped[AccountType] = mapped_column(
        Enum(AccountType, name="account_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class JournalEntry(Base, TimestampMixin):
    __tablename__ = "journal_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    entry_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    entry_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False, index=True)
    source_module: Mapped[str] = mapped_column(String(50), nullable=False)  # SALES, PURCHASE, PRODUCTION, PAYMENT, DISPATCH, MANUAL
    source_document_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    source_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    narration: Mapped[str] = mapped_column(Text, nullable=False)
    total_debit_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_credit_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    is_posted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Relationships
    lines: Mapped[List["JournalEntryLine"]] = relationship(
        "JournalEntryLine", back_populates="entry", cascade="all, delete-orphan", order_by="JournalEntryLine.id"
    )
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])


class JournalEntryLine(Base):
    __tablename__ = "journal_entry_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    entry_id: Mapped[str] = mapped_column(String(36), ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    debit_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    credit_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    line_narration: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    entry: Mapped["JournalEntry"] = relationship("JournalEntry", back_populates="lines")
    account: Mapped["Account"] = relationship("Account")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # CREATE, UPDATE, DELETE, POST, APPROVE, CANCEL
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # SALES_ORDER, INVOICE, PAYMENT, DISPATCH, PRODUCTION_RUN, PURCHASE
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, server_default=func.now(), nullable=False, index=True)
