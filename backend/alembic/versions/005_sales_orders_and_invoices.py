"""Sales order and GST invoice migration (Phase 5)

Revision ID: 005_sales_orders_and_invoices
Revises: 004_bom_and_production
Create Date: 2026-11-18 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '005_sales_orders_and_invoices'
down_revision = '004_bom_and_production'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. sales_orders table
    op.create_table(
        'sales_orders',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('order_number', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('order_date', sa.Date(), server_default=sa.func.current_date(), nullable=False),
        sa.Column('delivery_date', sa.Date(), nullable=True),
        sa.Column('place_of_supply_state_code', sa.String(length=10), nullable=False),
        sa.Column('customer_gstin', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='DRAFT'),
        sa.Column('subtotal_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('discount_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('taxable_amount_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('cgst_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('sgst_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('igst_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('total_tax_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('grand_total_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sales_orders_id'), 'sales_orders', ['id'], unique=False)
    op.create_index(op.f('ix_sales_orders_order_number'), 'sales_orders', ['order_number'], unique=True)
    op.create_index(op.f('ix_sales_orders_customer_id'), 'sales_orders', ['customer_id'], unique=False)
    op.create_index(op.f('ix_sales_orders_status'), 'sales_orders', ['status'], unique=False)

    # 2. sales_order_items table
    op.create_table(
        'sales_order_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('sales_order_id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('ordered_quantity', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('fulfilled_quantity', sa.Numeric(precision=14, scale=4), nullable=False, server_default='0.0000'),
        sa.Column('unit_price_paise', sa.BigInteger(), nullable=False),
        sa.Column('discount_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('gst_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('taxable_amount_paise', sa.BigInteger(), nullable=False),
        sa.Column('cgst_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('sgst_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('igst_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('line_total_paise', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['sales_order_id'], ['sales_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sales_order_items_id'), 'sales_order_items', ['id'], unique=False)
    op.create_index(op.f('ix_sales_order_items_sales_order_id'), 'sales_order_items', ['sales_order_id'], unique=False)
    op.create_index(op.f('ix_sales_order_items_product_id'), 'sales_order_items', ['product_id'], unique=False)

    # 3. sales_invoices table
    op.create_table(
        'sales_invoices',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('invoice_number', sa.String(length=50), nullable=False),
        sa.Column('sales_order_id', sa.String(length=36), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('invoice_date', sa.Date(), server_default=sa.func.current_date(), nullable=False),
        sa.Column('place_of_supply_state_code', sa.String(length=10), nullable=False),
        sa.Column('seller_gstin', sa.String(length=20), nullable=False),
        sa.Column('buyer_gstin', sa.String(length=20), nullable=True),
        sa.Column('taxable_amount_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('cgst_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('sgst_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('igst_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('total_tax_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('grand_total_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='DRAFT'),
        sa.Column('pdf_path', sa.String(length=255), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['sales_order_id'], ['sales_orders.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sales_invoices_id'), 'sales_invoices', ['id'], unique=False)
    op.create_index(op.f('ix_sales_invoices_invoice_number'), 'sales_invoices', ['invoice_number'], unique=True)
    op.create_index(op.f('ix_sales_invoices_sales_order_id'), 'sales_invoices', ['sales_order_id'], unique=False)
    op.create_index(op.f('ix_sales_invoices_customer_id'), 'sales_invoices', ['customer_id'], unique=False)
    op.create_index(op.f('ix_sales_invoices_status'), 'sales_invoices', ['status'], unique=False)

    # 4. sales_invoice_items table
    op.create_table(
        'sales_invoice_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('invoice_id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=True),
        sa.Column('product_name', sa.String(length=255), nullable=False),
        sa.Column('hsn_code', sa.String(length=20), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False, server_default='packet'),
        sa.Column('unit_price_paise', sa.BigInteger(), nullable=False),
        sa.Column('taxable_value_paise', sa.BigInteger(), nullable=False),
        sa.Column('gst_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('cgst_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('sgst_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('igst_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('line_total_paise', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['sales_invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sales_invoice_items_id'), 'sales_invoice_items', ['id'], unique=False)
    op.create_index(op.f('ix_sales_invoice_items_invoice_id'), 'sales_invoice_items', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_sales_invoice_items_product_id'), 'sales_invoice_items', ['product_id'], unique=False)


def downgrade() -> None:
    op.drop_table('sales_invoice_items')
    op.drop_table('sales_invoices')
    op.drop_table('sales_order_items')
    op.drop_table('sales_orders')
