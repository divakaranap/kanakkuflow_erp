"""Payments and customer ledger migration (Phase 7)

Revision ID: 007_payments_and_customer_ledger
Revises: 006_dispatches
Create Date: 2026-11-18 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '007_payments_and_customer_ledger'
down_revision = '006_dispatches'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add payment tracking columns to sales_invoices
    op.add_column('sales_invoices', sa.Column('due_date', sa.Date(), nullable=True))
    op.add_column('sales_invoices', sa.Column('amount_paid_paise', sa.BigInteger(), server_default='0', nullable=False))

    # 2. customer_payments table
    op.create_table(
        'customer_payments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('payment_number', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('payment_date', sa.Date(), server_default=sa.func.current_date(), nullable=False),
        sa.Column('amount_paise', sa.BigInteger(), nullable=False),
        sa.Column('payment_mode', sa.String(length=20), nullable=False),
        sa.Column('reference_number', sa.String(length=100), nullable=True),
        sa.Column('bank_name', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='RECORDED', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customer_payments_id'), 'customer_payments', ['id'], unique=False)
    op.create_index(op.f('ix_customer_payments_payment_number'), 'customer_payments', ['payment_number'], unique=True)
    op.create_index(op.f('ix_customer_payments_customer_id'), 'customer_payments', ['customer_id'], unique=False)
    op.create_index(op.f('ix_customer_payments_status'), 'customer_payments', ['status'], unique=False)

    # 3. payment_allocations table
    op.create_table(
        'payment_allocations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('payment_id', sa.String(length=36), nullable=False),
        sa.Column('invoice_id', sa.String(length=36), nullable=False),
        sa.Column('allocated_amount_paise', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['payment_id'], ['customer_payments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invoice_id'], ['sales_invoices.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_allocations_id'), 'payment_allocations', ['id'], unique=False)
    op.create_index(op.f('ix_payment_allocations_payment_id'), 'payment_allocations', ['payment_id'], unique=False)
    op.create_index(op.f('ix_payment_allocations_invoice_id'), 'payment_allocations', ['invoice_id'], unique=False)

    # 4. customer_ledger_entries table
    op.create_table(
        'customer_ledger_entries',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('entry_date', sa.Date(), server_default=sa.func.current_date(), nullable=False),
        sa.Column('entry_type', sa.String(length=50), nullable=False),
        sa.Column('reference_document_id', sa.String(length=36), nullable=True),
        sa.Column('reference_number', sa.String(length=100), nullable=False),
        sa.Column('debit_paise', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('credit_paise', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('running_balance_paise', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customer_ledger_entries_id'), 'customer_ledger_entries', ['id'], unique=False)
    op.create_index(op.f('ix_customer_ledger_entries_customer_id'), 'customer_ledger_entries', ['customer_id'], unique=False)
    op.create_index(op.f('ix_customer_ledger_entries_entry_date'), 'customer_ledger_entries', ['entry_date'], unique=False)


def downgrade() -> None:
    op.drop_table('customer_ledger_entries')
    op.drop_table('payment_allocations')
    op.drop_table('customer_payments')
    op.drop_column('sales_invoices', 'amount_paid_paise')
    op.drop_column('sales_invoices', 'due_date')
