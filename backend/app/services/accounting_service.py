from datetime import date, datetime
from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi import HTTPException

from backend.app.models.accounting import (
    Account,
    AccountCategory,
    AccountType,
    JournalEntry,
    JournalEntryLine,
)
from backend.app.models.sales import SalesInvoice
from backend.app.models.payment import CustomerPayment
from backend.app.models.purchase import Purchase
from backend.app.models.production import ProductionRun
from backend.app.models.dispatch import Dispatch
from backend.app.schemas.accounting import (
    JournalEntryCreate,
    TrialBalanceResponse,
    TrialBalanceRow,
    GeneralLedgerResponse,
    GeneralLedgerRow,
)


STANDARD_COA = [
    # Assets
    ("1010", "Cash in Hand", AccountCategory.ASSET, AccountType.CASH_BANK, "Physical cash at factory"),
    ("1020", "Bank Current Account", AccountCategory.ASSET, AccountType.CASH_BANK, "Primary operational bank account"),
    ("1030", "Accounts Receivable (Debtors)", AccountCategory.ASSET, AccountType.ACCOUNTS_RECEIVABLE, "Trade debtors and customer balances"),
    ("1040", "Raw Materials Stock", AccountCategory.ASSET, AccountType.RAW_MATERIAL_INVENTORY, "Inventory of ingredients, spices, oil, flours"),
    ("1050", "Packaging Materials Stock", AccountCategory.ASSET, AccountType.PACKAGING_INVENTORY, "Pouches, corrugated cartons, labels"),
    ("1060", "Finished Goods Stock", AccountCategory.ASSET, AccountType.FINISHED_GOODS_INVENTORY, "Packaged snacks ready for dispatch"),
    ("1071", "Input CGST", AccountCategory.ASSET, AccountType.INPUT_CGST, "Central GST paid on purchases (input tax credit)"),
    ("1072", "Input SGST", AccountCategory.ASSET, AccountType.INPUT_SGST, "State GST paid on purchases (input tax credit)"),
    ("1073", "Input IGST", AccountCategory.ASSET, AccountType.INPUT_IGST, "Integrated GST paid on inter-state purchases"),

    # Liabilities
    ("2010", "Accounts Payable (Creditors)", AccountCategory.LIABILITY, AccountType.ACCOUNTS_PAYABLE, "Trade creditors and supplier dues"),
    ("2021", "Output CGST", AccountCategory.LIABILITY, AccountType.OUTPUT_CGST, "Central GST collected on sales (payable to govt)"),
    ("2022", "Output SGST", AccountCategory.LIABILITY, AccountType.OUTPUT_SGST, "State GST collected on sales (payable to govt)"),
    ("2023", "Output IGST", AccountCategory.LIABILITY, AccountType.OUTPUT_IGST, "Integrated GST collected on inter-state sales"),

    # Equity
    ("3010", "Owner's Capital", AccountCategory.EQUITY, AccountType.OWNERS_CAPITAL, "Equity invested by promoter"),
    ("3020", "Retained Earnings", AccountCategory.EQUITY, AccountType.RETAINED_EARNINGS, "Accumulated operational profits"),

    # Revenue
    ("4010", "Sales Revenue - Manufactured Snacks", AccountCategory.REVENUE, AccountType.SALES_REVENUE, "Domestic revenue from snack sales"),
    ("4020", "Sales Discount Allowed", AccountCategory.REVENUE, AccountType.DISCOUNT_ALLOWED, "Discounts extended to distributors"),

    # Expenses
    ("5010", "Cost of Goods Sold (Raw Materials)", AccountCategory.EXPENSE, AccountType.COGS, "Cost of raw materials consumed in production"),
    ("5020", "Direct Factory Labour", AccountCategory.EXPENSE, AccountType.DIRECT_LABOUR, "Wages paid to frying and packaging staff"),
    ("5030", "Factory Power & Overheads", AccountCategory.EXPENSE, AccountType.FACTORY_OVERHEAD, "Electricity, gas, machine maintenance"),
    ("5040", "Production Yield Variance Expense", AccountCategory.EXPENSE, AccountType.YIELD_VARIANCE_EXPENSE, "Loss/Gain from material yield variances"),
]


def seed_chart_of_accounts(db: Session) -> None:
    """Seed standard Chart of Accounts if empty."""
    existing_count = db.query(Account).count()
    if existing_count >= len(STANDARD_COA):
        return

    for code, name, cat, acct_type, desc in STANDARD_COA:
        exists = db.query(Account).filter(Account.code == code).first()
        if not exists:
            acct = Account(
                code=code,
                name=name,
                category=cat,
                account_type=acct_type,
                description=desc,
                is_active=True,
            )
            db.add(acct)
    db.commit()


def get_account_by_type(db: Session, acct_type: AccountType) -> Account:
    """Retrieve account by account type, seeding defaults if needed."""
    seed_chart_of_accounts(db)
    account = db.query(Account).filter(Account.account_type == acct_type, Account.is_active.is_(True)).first()
    if not account:
        raise HTTPException(status_code=500, detail=f"Chart of accounts missing active account for type {acct_type}")
    return account


def generate_journal_entry_number(db: Session) -> str:
    """Generate sequential Journal Entry number: JV-YYYYMM-XXXX."""
    today = date.today()
    prefix = f"JV-{today.strftime('%Y%m')}-"
    last_entry = (
        db.query(JournalEntry)
        .filter(JournalEntry.entry_number.like(f"{prefix}%"))
        .order_by(desc(JournalEntry.entry_number))
        .first()
    )
    if last_entry:
        try:
            last_seq = int(last_entry.entry_number.split("-")[-1])
            new_seq = last_seq + 1
        except (ValueError, IndexError):
            new_seq = 1
    else:
        new_seq = 1
    return f"{prefix}{new_seq:04d}"


def create_journal_entry(
    db: Session,
    data: JournalEntryCreate,
    current_user_id: int,
) -> JournalEntry:
    """Create and post a double-entry journal with strict Debit == Credit enforcement."""
    if len(data.lines) < 2:
        raise HTTPException(status_code=400, detail="Journal entry must contain at least 2 lines")

    total_debit = sum(line.debit_paise for line in data.lines)
    total_credit = sum(line.credit_paise for line in data.lines)

    if total_debit <= 0 or total_credit <= 0:
        raise HTTPException(status_code=400, detail="Total debit and credit amounts must be greater than zero")

    if total_debit != total_credit:
        raise HTTPException(
            status_code=400,
            detail=f"Double-entry invariant violated: Total Debits (₹{total_debit/100:.2f}) != Total Credits (₹{total_credit/100:.2f})",
        )

    # Validate accounts
    for line in data.lines:
        acct = db.query(Account).filter(Account.id == str(line.account_id)).first()
        if not acct or not acct.is_active:
            raise HTTPException(status_code=400, detail=f"Invalid or inactive account {line.account_id}")

    entry_num = generate_journal_entry_number(db)
    entry_dt = data.entry_date or date.today()

    entry = JournalEntry(
        entry_number=entry_num,
        entry_date=entry_dt,
        source_module=data.source_module,
        source_document_id=data.source_document_id,
        source_reference=data.source_reference,
        narration=data.narration,
        total_debit_paise=total_debit,
        total_credit_paise=total_credit,
        is_posted=True,
        created_by=current_user_id,
    )
    db.add(entry)
    db.flush()

    for line in data.lines:
        jl = JournalEntryLine(
            entry_id=str(entry.id),
            account_id=str(line.account_id),
            debit_paise=line.debit_paise,
            credit_paise=line.credit_paise,
            line_narration=line.line_narration,
        )
        db.add(jl)

    db.commit()
    db.refresh(entry)
    return entry


# Automatic Journal Event Triggers

def post_sales_invoice_journal(db: Session, invoice: SalesInvoice, user_id: int) -> JournalEntry:
    """
    Automatic Double Entry for Posted Sales Invoice:
    Debit: Accounts Receivable (grand_total_paise)
    Credit: Sales Revenue (taxable_amount_paise)
    Credit: Output CGST (cgst_paise)
    Credit: Output SGST (sgst_paise)
    Credit: Output IGST (igst_paise)
    """
    ar_acct = get_account_by_type(db, AccountType.ACCOUNTS_RECEIVABLE)
    rev_acct = get_account_by_type(db, AccountType.SALES_REVENUE)
    cgst_acct = get_account_by_type(db, AccountType.OUTPUT_CGST)
    sgst_acct = get_account_by_type(db, AccountType.OUTPUT_SGST)
    igst_acct = get_account_by_type(db, AccountType.OUTPUT_IGST)

    lines = [
        JournalEntryLine(account_id=ar_acct.id, debit_paise=invoice.grand_total_paise, credit_paise=0, line_narration="Customer Receivable"),
        JournalEntryLine(account_id=rev_acct.id, debit_paise=0, credit_paise=invoice.taxable_amount_paise, line_narration="Sales Revenue"),
    ]

    if invoice.cgst_paise > 0:
        lines.append(JournalEntryLine(account_id=cgst_acct.id, debit_paise=0, credit_paise=invoice.cgst_paise, line_narration="Output CGST"))
    if invoice.sgst_paise > 0:
        lines.append(JournalEntryLine(account_id=sgst_acct.id, debit_paise=0, credit_paise=invoice.sgst_paise, line_narration="Output SGST"))
    if invoice.igst_paise > 0:
        lines.append(JournalEntryLine(account_id=igst_acct.id, debit_paise=0, credit_paise=invoice.igst_paise, line_narration="Output IGST"))

    tot_debit = sum(l.debit_paise for l in lines)
    tot_credit = sum(l.credit_paise for l in lines)
    assert tot_debit == tot_credit, f"Invoice journal out of balance: {tot_debit} != {tot_credit}"

    entry_num = generate_journal_entry_number(db)
    entry = JournalEntry(
        entry_number=entry_num,
        entry_date=invoice.invoice_date,
        source_module="SALES",
        source_document_id=str(invoice.id),
        source_reference=invoice.invoice_number,
        narration=f"Sales Invoice #{invoice.invoice_number} posted for customer {invoice.customer.customer_name if invoice.customer else 'Customer'}",
        total_debit_paise=tot_debit,
        total_credit_paise=tot_credit,
        is_posted=True,
        created_by=user_id,
        lines=lines,
    )
    db.add(entry)
    db.flush()
    return entry


def post_payment_journal(db: Session, payment: CustomerPayment, user_id: int) -> JournalEntry:
    """
    Automatic Double Entry for Customer Payment:
    Debit: Cash/Bank Account (amount_paise)
    Credit: Accounts Receivable (amount_paise)
    """
    bank_acct = get_account_by_type(db, AccountType.CASH_BANK)
    ar_acct = get_account_by_type(db, AccountType.ACCOUNTS_RECEIVABLE)

    lines = [
        JournalEntryLine(account_id=bank_acct.id, debit_paise=payment.amount_paise, credit_paise=0, line_narration=f"Received via {payment.payment_mode}"),
        JournalEntryLine(account_id=ar_acct.id, debit_paise=0, credit_paise=payment.amount_paise, line_narration="Settlement of customer receivable"),
    ]

    entry_num = generate_journal_entry_number(db)
    entry = JournalEntry(
        entry_number=entry_num,
        entry_date=payment.payment_date,
        source_module="PAYMENT",
        source_document_id=str(payment.id),
        source_reference=payment.payment_number,
        narration=f"Customer receipt #{payment.payment_number} via {payment.payment_mode} (Ref: {payment.reference_number or 'Direct'})",
        total_debit_paise=payment.amount_paise,
        total_credit_paise=payment.amount_paise,
        is_posted=True,
        created_by=user_id,
        lines=lines,
    )
    db.add(entry)
    db.flush()
    return entry


def post_purchase_journal(db: Session, purchase: Purchase, user_id: int) -> JournalEntry:
    """
    Automatic Double Entry for Posted Supplier Purchase:
    Debit: Raw Material Stock / Packaging Stock (taxable_total_paise)
    Debit: Input CGST + Input SGST / IGST (tax_total_paise)
    Credit: Accounts Payable (grand_total_paise)
    """
    rm_acct = get_account_by_type(db, AccountType.RAW_MATERIAL_INVENTORY)
    ap_acct = get_account_by_type(db, AccountType.ACCOUNTS_PAYABLE)
    cgst_acct = get_account_by_type(db, AccountType.INPUT_CGST)
    sgst_acct = get_account_by_type(db, AccountType.INPUT_SGST)
    igst_acct = get_account_by_type(db, AccountType.INPUT_IGST)

    taxable = purchase.taxable_total_paise or purchase.subtotal_paise
    cgst = purchase.cgst_total_paise or 0
    sgst = purchase.sgst_total_paise or 0
    igst = purchase.igst_total_paise or 0
    grand_total = purchase.grand_total_paise

    lines = [
        JournalEntryLine(account_id=rm_acct.id, debit_paise=taxable, credit_paise=0, line_narration="Material Inventory"),
    ]
    if cgst > 0:
        lines.append(JournalEntryLine(account_id=cgst_acct.id, debit_paise=cgst, credit_paise=0, line_narration="Input CGST"))
    if sgst > 0:
        lines.append(JournalEntryLine(account_id=sgst_acct.id, debit_paise=sgst, credit_paise=0, line_narration="Input SGST"))
    if igst > 0:
        lines.append(JournalEntryLine(account_id=igst_acct.id, debit_paise=igst, credit_paise=0, line_narration="Input IGST"))

    lines.append(JournalEntryLine(account_id=ap_acct.id, debit_paise=0, credit_paise=grand_total, line_narration="Supplier Payable"))

    tot_debit = sum(l.debit_paise for l in lines)
    tot_credit = sum(l.credit_paise for l in lines)
    assert tot_debit == tot_credit, f"Purchase journal out of balance: {tot_debit} != {tot_credit}"

    entry_num = generate_journal_entry_number(db)
    entry = JournalEntry(
        entry_number=entry_num,
        entry_date=purchase.purchase_date,
        source_module="PURCHASE",
        source_document_id=str(purchase.id),
        source_reference=purchase.purchase_number,
        narration=f"Purchase bill #{purchase.purchase_number} from supplier {purchase.supplier.supplier_name if purchase.supplier else 'Supplier'}",
        total_debit_paise=tot_debit,
        total_credit_paise=tot_credit,
        is_posted=True,
        created_by=user_id,
        lines=lines,
    )
    db.add(entry)
    db.flush()
    return entry


def post_production_journal(db: Session, run: ProductionRun, user_id: int) -> JournalEntry:
    """
    Automatic Double Entry for Completed Production Run:
    Debit: Finished Goods Stock (total production cost)
    Credit: Raw Material Stock (actual material cost)
    Credit: Factory Overhead / Direct Labour (overhead cost)
    """
    fg_acct = get_account_by_type(db, AccountType.FINISHED_GOODS_INVENTORY)
    rm_acct = get_account_by_type(db, AccountType.RAW_MATERIAL_INVENTORY)
    oh_acct = get_account_by_type(db, AccountType.FACTORY_OVERHEAD)

    rm_cost = getattr(run, "actual_material_cost_paise", 0) or 0
    oh_cost = getattr(run, "total_overhead_cost_paise", 0) or 0
    tot_cost = getattr(run, "total_production_cost_paise", rm_cost + oh_cost) or (rm_cost + oh_cost)

    if tot_cost <= 0:
        return None

    lines = [
        JournalEntryLine(account_id=fg_acct.id, debit_paise=tot_cost, credit_paise=0, line_narration="Finished Goods produced"),
        JournalEntryLine(account_id=rm_acct.id, debit_paise=0, credit_paise=rm_cost, line_narration="Raw Materials consumed"),
    ]
    if oh_cost > 0:
        lines.append(JournalEntryLine(account_id=oh_acct.id, debit_paise=0, credit_paise=oh_cost, line_narration="Factory overheads applied"))

    tot_debit = sum(l.debit_paise for l in lines)
    tot_credit = sum(l.credit_paise for l in lines)
    assert tot_debit == tot_credit, f"Production journal out of balance: {tot_debit} != {tot_credit}"

    entry_num = generate_journal_entry_number(db)
    entry = JournalEntry(
        entry_number=entry_num,
        entry_date=getattr(run, "run_date", date.today()),
        source_module="PRODUCTION",
        source_document_id=str(run.id),
        source_reference=run.run_number,
        narration=f"Production run #{run.run_number} finished goods capitalization",
        total_debit_paise=tot_debit,
        total_credit_paise=tot_credit,
        is_posted=True,
        created_by=user_id,
        lines=lines,
    )
    db.add(entry)
    db.flush()
    return entry


# Reporting: Trial Balance & General Ledger

def get_trial_balance(db: Session, as_of: Optional[date] = None) -> TrialBalanceResponse:
    """Calculate Trial Balance across all Chart of Accounts accounts."""
    seed_chart_of_accounts(db)
    target_date = as_of or date.today()

    accounts = db.query(Account).filter(Account.is_active.is_(True)).order_by(Account.code.asc()).all()

    tb_rows = []
    grand_total_debit = 0
    grand_total_credit = 0

    for acct in accounts:
        line_sums = (
            db.query(
                func.coalesce(func.sum(JournalEntryLine.debit_paise), 0).label("tot_debit"),
                func.coalesce(func.sum(JournalEntryLine.credit_paise), 0).label("tot_credit"),
            )
            .join(JournalEntry, JournalEntry.id == JournalEntryLine.entry_id)
            .filter(
                JournalEntryLine.account_id == str(acct.id),
                JournalEntry.entry_date <= target_date,
                JournalEntry.is_posted.is_(True),
            )
            .first()
        )

        tot_deb = line_sums.tot_debit if line_sums else 0
        tot_cred = line_sums.tot_credit if line_sums else 0

        # Calculate Net Debit or Net Credit based on normal balance category
        net_deb = max(0, tot_deb - tot_cred)
        net_cred = max(0, tot_cred - tot_deb)

        grand_total_debit += net_deb
        grand_total_credit += net_cred

        tb_rows.append(
            TrialBalanceRow(
                account_id=str(acct.id),
                account_code=acct.code,
                account_name=acct.name,
                category=acct.category,
                account_type=acct.account_type,
                total_debit_paise=tot_deb,
                total_credit_paise=tot_cred,
                net_debit_paise=net_deb,
                net_credit_paise=net_cred,
            )
        )

    difference = abs(grand_total_debit - grand_total_credit)
    is_balanced = (difference == 0)

    return TrialBalanceResponse(
        as_of_date=target_date,
        is_balanced=is_balanced,
        grand_total_debit_paise=grand_total_debit,
        grand_total_credit_paise=grand_total_credit,
        difference_paise=difference,
        accounts=tb_rows,
    )


def get_general_ledger(db: Session, account_id: str) -> GeneralLedgerResponse:
    """Chronological General Ledger statement for an account with running balance."""
    acct = db.query(Account).filter(Account.id == str(account_id)).first()
    if not acct:
        raise HTTPException(status_code=404, detail="Account not found")

    lines = (
        db.query(JournalEntryLine)
        .join(JournalEntry, JournalEntry.id == JournalEntryLine.entry_id)
        .filter(JournalEntryLine.account_id == str(acct.id), JournalEntry.is_posted.is_(True))
        .order_by(JournalEntry.entry_date.asc(), JournalEntry.created_at.asc(), JournalEntryLine.id.asc())
        .all()
    )

    rows = []
    running = 0
    total_debit = 0
    total_credit = 0

    # Normal balance: ASSET and EXPENSE increase with DEBIT (+Debit -Credit)
    # LIABILITY, EQUITY, REVENUE increase with CREDIT (+Credit -Debit)
    is_debit_normal = acct.category in [AccountCategory.ASSET, AccountCategory.EXPENSE]

    for line in lines:
        entry = line.entry
        total_debit += line.debit_paise
        total_credit += line.credit_paise

        if is_debit_normal:
            running += (line.debit_paise - line.credit_paise)
        else:
            running += (line.credit_paise - line.debit_paise)

        rows.append(
            GeneralLedgerRow(
                id=line.id,
                entry_id=entry.id,
                entry_number=entry.entry_number,
                entry_date=entry.entry_date,
                source_module=entry.source_module,
                source_reference=entry.source_reference,
                narration=entry.narration,
                line_narration=line.line_narration,
                debit_paise=line.debit_paise,
                credit_paise=line.credit_paise,
                running_balance_paise=running,
            )
        )

    return GeneralLedgerResponse(
        account_id=str(acct.id),
        account_code=acct.code,
        account_name=acct.name,
        category=acct.category,
        total_debit_paise=total_debit,
        total_credit_paise=total_credit,
        closing_balance_paise=running,
        rows=rows,
    )
