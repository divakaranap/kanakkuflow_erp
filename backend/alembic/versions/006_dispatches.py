"""Dispatch and finished goods management migration (Phase 6)

Revision ID: 006_dispatches
Revises: 005_sales_orders_and_invoices
Create Date: 2026-11-18 11:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '006_dispatches'
down_revision = '005_sales_orders_and_invoices'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. dispatches table
    op.create_table(
        'dispatches',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('dispatch_number', sa.String(length=50), nullable=False),
        sa.Column('sales_order_id', sa.String(length=36), nullable=False),
        sa.Column('invoice_id', sa.String(length=36), nullable=True),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('dispatch_date', sa.Date(), server_default=sa.func.current_date(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='DRAFT'),
        sa.Column('transporter_name', sa.String(length=100), nullable=True),
        sa.Column('vehicle_number', sa.String(length=50), nullable=True),
        sa.Column('tracking_reference', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('dispatched_by', sa.Integer(), nullable=True),
        sa.Column('dispatched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['sales_order_id'], ['sales_orders.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['invoice_id'], ['sales_invoices.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['dispatched_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dispatches_id'), 'dispatches', ['id'], unique=False)
    op.create_index(op.f('ix_dispatches_dispatch_number'), 'dispatches', ['dispatch_number'], unique=True)
    op.create_index(op.f('ix_dispatches_sales_order_id'), 'dispatches', ['sales_order_id'], unique=False)
    op.create_index(op.f('ix_dispatches_invoice_id'), 'dispatches', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_dispatches_customer_id'), 'dispatches', ['customer_id'], unique=False)
    op.create_index(op.f('ix_dispatches_status'), 'dispatches', ['status'], unique=False)

    # 2. dispatch_items table
    op.create_table(
        'dispatch_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('dispatch_id', sa.String(length=36), nullable=False),
        sa.Column('sales_order_item_id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('quantity_dispatched', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('batch_reference', sa.String(length=50), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=False, server_default='packet'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['dispatch_id'], ['dispatches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sales_order_item_id'], ['sales_order_items.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dispatch_items_id'), 'dispatch_items', ['id'], unique=False)
    op.create_index(op.f('ix_dispatch_items_dispatch_id'), 'dispatch_items', ['dispatch_id'], unique=False)
    op.create_index(op.f('ix_dispatch_items_product_id'), 'dispatch_items', ['product_id'], unique=False)


def downgrade() -> None:
    op.drop_table('dispatch_items')
    op.drop_table('dispatches')
