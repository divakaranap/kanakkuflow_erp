"""Accounting, journal entries and audit trail migration (Phase 8)

Revision ID: 008_accounting_and_audit
Revises: 007_payments_and_customer_ledger
Create Date: 2026-11-18 12:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '008_accounting_and_audit'
down_revision = '007_payments_and_customer_ledger'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. accounts table (Chart of Accounts)
    op.create_table(
        'accounts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=30), nullable=False),
        sa.Column('account_type', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_accounts_id'), 'accounts', ['id'], unique=False)
    op.create_index(op.f('ix_accounts_code'), 'accounts', ['code'], unique=True)
    op.create_index(op.f('ix_accounts_category'), 'accounts', ['category'], unique=False)
    op.create_index(op.f('ix_accounts_account_type'), 'accounts', ['account_type'], unique=False)

    # 2. journal_entries table
    op.create_table(
        'journal_entries',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('entry_number', sa.String(length=50), nullable=False),
        sa.Column('entry_date', sa.Date(), server_default=sa.func.current_date(), nullable=False),
        sa.Column('source_module', sa.String(length=50), nullable=False),
        sa.Column('source_document_id', sa.String(length=36), nullable=True),
        sa.Column('source_reference', sa.String(length=100), nullable=True),
        sa.Column('narration', sa.Text(), nullable=False),
        sa.Column('total_debit_paise', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('total_credit_paise', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('is_posted', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_journal_entries_id'), 'journal_entries', ['id'], unique=False)
    op.create_index(op.f('ix_journal_entries_entry_number'), 'journal_entries', ['entry_number'], unique=True)
    op.create_index(op.f('ix_journal_entries_entry_date'), 'journal_entries', ['entry_date'], unique=False)
    op.create_index(op.f('ix_journal_entries_source_document_id'), 'journal_entries', ['source_document_id'], unique=False)

    # 3. journal_entry_lines table
    op.create_table(
        'journal_entry_lines',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('entry_id', sa.String(length=36), nullable=False),
        sa.Column('account_id', sa.String(length=36), nullable=False),
        sa.Column('debit_paise', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('credit_paise', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('line_narration', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['entry_id'], ['journal_entries.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_journal_entry_lines_id'), 'journal_entry_lines', ['id'], unique=False)
    op.create_index(op.f('ix_journal_entry_lines_entry_id'), 'journal_entry_lines', ['entry_id'], unique=False)
    op.create_index(op.f('ix_journal_entry_lines_account_id'), 'journal_entry_lines', ['account_id'], unique=False)

    # 4. audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('role', sa.String(length=30), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=100), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_type'), 'audit_logs', ['entity_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('journal_entry_lines')
    op.drop_table('journal_entries')
    op.drop_table('accounts')
