"""Inventory ledger, purchases and adjustments migration (Phase 3)

Revision ID: 003_inventory_and_purchases
Revises: 002_master_data
Create Date: 2026-11-18 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '003_inventory_and_purchases'
down_revision = '002_master_data'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Purchases table
    op.create_table(
        'purchases',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('purchase_number', sa.String(length=50), nullable=False),
        sa.Column('supplier_id', sa.String(length=36), nullable=False),
        sa.Column('supplier_invoice_number', sa.String(length=100), nullable=False),
        sa.Column('purchase_date', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='DRAFT'),
        sa.Column('subtotal_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('tax_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('total_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('posted_by', sa.Integer(), nullable=True),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['posted_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_purchases_id'), 'purchases', ['id'], unique=False)
    op.create_index(op.f('ix_purchases_purchase_number'), 'purchases', ['purchase_number'], unique=True)
    op.create_index(op.f('ix_purchases_supplier_id'), 'purchases', ['supplier_id'], unique=False)
    op.create_index(op.f('ix_purchases_supplier_invoice_number'), 'purchases', ['supplier_invoice_number'], unique=False)
    op.create_index(op.f('ix_purchases_status'), 'purchases', ['status'], unique=False)

    # 2. Purchase Lines table
    op.create_table(
        'purchase_lines',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('purchase_id', sa.String(length=36), nullable=False),
        sa.Column('item_type', sa.String(length=20), nullable=False),
        sa.Column('item_id', sa.String(length=36), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('normalized_quantity', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('unit_rate_paise', sa.BigInteger(), nullable=False),
        sa.Column('taxable_value_paise', sa.BigInteger(), nullable=False),
        sa.Column('tax_rate', sa.Numeric(precision=5, scale=4), nullable=False, server_default='0.0500'),
        sa.Column('tax_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('line_total_paise', sa.BigInteger(), nullable=False),
        sa.Column('batch_number', sa.String(length=50), nullable=True),
        sa.Column('manufacturing_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expiry_date', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['purchase_id'], ['purchases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_purchase_lines_id'), 'purchase_lines', ['id'], unique=False)
    op.create_index(op.f('ix_purchase_lines_purchase_id'), 'purchase_lines', ['purchase_id'], unique=False)
    op.create_index(op.f('ix_purchase_lines_item_id'), 'purchase_lines', ['item_id'], unique=False)

    # 3. Stock Movements table (Immutable ledger)
    op.create_table(
        'stock_movements',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('item_type', sa.String(length=20), nullable=False),
        sa.Column('item_id', sa.String(length=36), nullable=False),
        sa.Column('batch_id', sa.String(length=36), nullable=True),
        sa.Column('movement_type', sa.String(length=30), nullable=False),
        sa.Column('qty_delta', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('unit_cost_paise', sa.BigInteger(), nullable=True),
        sa.Column('total_value_paise', sa.BigInteger(), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.String(length=36), nullable=False),
        sa.Column('reference_number', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stock_movements_id'), 'stock_movements', ['id'], unique=False)
    op.create_index(op.f('ix_stock_movements_item_type'), 'stock_movements', ['item_type'], unique=False)
    op.create_index(op.f('ix_stock_movements_item_id'), 'stock_movements', ['item_id'], unique=False)
    op.create_index(op.f('ix_stock_movements_batch_id'), 'stock_movements', ['batch_id'], unique=False)
    op.create_index(op.f('ix_stock_movements_movement_type'), 'stock_movements', ['movement_type'], unique=False)
    op.create_index(op.f('ix_stock_movements_source_type'), 'stock_movements', ['source_type'], unique=False)
    op.create_index(op.f('ix_stock_movements_source_id'), 'stock_movements', ['source_id'], unique=False)
    op.create_index(op.f('ix_stock_movements_created_at'), 'stock_movements', ['created_at'], unique=False)

    # 4. Inventory Balances cache table
    op.create_table(
        'inventory_balances',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('item_type', sa.String(length=20), nullable=False),
        sa.Column('item_id', sa.String(length=36), nullable=False),
        sa.Column('batch_id', sa.String(length=36), nullable=True),
        sa.Column('cached_qty', sa.Numeric(precision=14, scale=4), nullable=False, server_default='0.0000'),
        sa.Column('total_value_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('weighted_avg_rate_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('last_reconciled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('item_type', 'item_id', 'batch_id', name='uq_inventory_balance_item_batch')
    )
    op.create_index(op.f('ix_inventory_balances_id'), 'inventory_balances', ['id'], unique=False)
    op.create_index(op.f('ix_inventory_balances_item_type'), 'inventory_balances', ['item_type'], unique=False)
    op.create_index(op.f('ix_inventory_balances_item_id'), 'inventory_balances', ['item_id'], unique=False)

    # 5. Inventory Adjustments table
    op.create_table(
        'inventory_adjustments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('adjustment_number', sa.String(length=50), nullable=False),
        sa.Column('item_type', sa.String(length=20), nullable=False),
        sa.Column('item_id', sa.String(length=36), nullable=False),
        sa.Column('adjustment_type', sa.String(length=20), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('reference_number', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='DRAFT'),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_adjustments_id'), 'inventory_adjustments', ['id'], unique=False)
    op.create_index(op.f('ix_inventory_adjustments_adjustment_number'), 'inventory_adjustments', ['adjustment_number'], unique=True)
    op.create_index(op.f('ix_inventory_adjustments_item_type'), 'inventory_adjustments', ['item_type'], unique=False)
    op.create_index(op.f('ix_inventory_adjustments_item_id'), 'inventory_adjustments', ['item_id'], unique=False)


def downgrade() -> None:
    op.drop_table('inventory_adjustments')
    op.drop_table('inventory_balances')
    op.drop_table('stock_movements')
    op.drop_table('purchase_lines')
    op.drop_table('purchases')
