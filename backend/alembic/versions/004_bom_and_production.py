"""BOM and production run management migration (Phase 4)

Revision ID: 004_bom_and_production
Revises: 003_inventory_and_purchases
Create Date: 2026-11-18 11:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '004_bom_and_production'
down_revision = '003_inventory_and_purchases'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. BOMs table
    op.create_table(
        'boms',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('bom_code', sa.String(length=50), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('batch_yield_packets', sa.Numeric(precision=14, scale=4), nullable=False, server_default='200.0000'),
        sa.Column('tolerance_pct', sa.Numeric(precision=5, scale=2), nullable=False, server_default='3.00'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='DRAFT'),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('effective_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_boms_id'), 'boms', ['id'], unique=False)
    op.create_index(op.f('ix_boms_bom_code'), 'boms', ['bom_code'], unique=True)
    op.create_index(op.f('ix_boms_product_id'), 'boms', ['product_id'], unique=False)
    op.create_index(op.f('ix_boms_status'), 'boms', ['status'], unique=False)

    # 2. BOM Items table
    op.create_table(
        'bom_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('bom_id', sa.String(length=36), nullable=False),
        sa.Column('item_type', sa.String(length=20), nullable=False),
        sa.Column('item_id', sa.String(length=36), nullable=False),
        sa.Column('quantity_per_batch', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['bom_id'], ['boms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bom_items_id'), 'bom_items', ['id'], unique=False)
    op.create_index(op.f('ix_bom_items_bom_id'), 'bom_items', ['bom_id'], unique=False)
    op.create_index(op.f('ix_bom_items_item_id'), 'bom_items', ['item_id'], unique=False)

    # 3. Production Runs table
    op.create_table(
        'production_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('run_number', sa.String(length=50), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('bom_id', sa.String(length=36), nullable=False),
        sa.Column('bom_version_snapshot', sa.Text(), nullable=False),
        sa.Column('production_date', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('batch_number', sa.String(length=50), nullable=False),
        sa.Column('number_of_batches', sa.Numeric(precision=10, scale=2), nullable=False, server_default='1.00'),
        sa.Column('expected_output', sa.Numeric(precision=14, scale=4), nullable=False, server_default='0.0000'),
        sa.Column('actual_good_output', sa.Numeric(precision=14, scale=4), nullable=False, server_default='0.0000'),
        sa.Column('damaged_packaging', sa.Numeric(precision=14, scale=4), nullable=False, server_default='0.0000'),
        sa.Column('wastage_quantity', sa.Numeric(precision=14, scale=4), nullable=False, server_default='0.0000'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='DRAFT'),
        sa.Column('planned_material_cost_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('actual_material_cost_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('packaging_cost_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('labour_cost_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('utility_cost_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('total_production_cost_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('cost_per_packet_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('cost_per_packet_decimal', sa.Numeric(precision=10, scale=4), nullable=False, server_default='0.0000'),
        sa.Column('variance_status', sa.String(length=20), nullable=False, server_default='NORMAL'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('supervisor_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['bom_id'], ['boms.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['supervisor_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_production_runs_id'), 'production_runs', ['id'], unique=False)
    op.create_index(op.f('ix_production_runs_run_number'), 'production_runs', ['run_number'], unique=True)
    op.create_index(op.f('ix_production_runs_product_id'), 'production_runs', ['product_id'], unique=False)
    op.create_index(op.f('ix_production_runs_bom_id'), 'production_runs', ['bom_id'], unique=False)
    op.create_index(op.f('ix_production_runs_batch_number'), 'production_runs', ['batch_number'], unique=False)
    op.create_index(op.f('ix_production_runs_status'), 'production_runs', ['status'], unique=False)

    # 4. Production Run Materials table
    op.create_table(
        'production_run_materials',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('production_run_id', sa.String(length=36), nullable=False),
        sa.Column('item_type', sa.String(length=20), nullable=False),
        sa.Column('item_id', sa.String(length=36), nullable=False),
        sa.Column('planned_quantity', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('issued_quantity', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('consumed_quantity', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('planned_unit_cost', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('actual_unit_cost', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('material_cost_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('consumption_variance_pct', sa.Numeric(precision=6, scale=2), nullable=False, server_default='0.00'),
        sa.ForeignKeyConstraint(['production_run_id'], ['production_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_production_run_materials_id'), 'production_run_materials', ['id'], unique=False)
    op.create_index(op.f('ix_production_run_materials_production_run_id'), 'production_run_materials', ['production_run_id'], unique=False)
    op.create_index(op.f('ix_production_run_materials_item_id'), 'production_run_materials', ['item_id'], unique=False)

    # 5. Production Run Overheads table
    op.create_table(
        'production_run_overheads',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('production_run_id', sa.String(length=36), nullable=False),
        sa.Column('expense_type', sa.String(length=20), nullable=False),
        sa.Column('amount_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['production_run_id'], ['production_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_production_run_overheads_id'), 'production_run_overheads', ['id'], unique=False)
    op.create_index(op.f('ix_production_run_overheads_production_run_id'), 'production_run_overheads', ['production_run_id'], unique=False)


def downgrade() -> None:
    op.drop_table('production_run_overheads')
    op.drop_table('production_run_materials')
    op.drop_table('production_runs')
    op.drop_table('bom_items')
    op.drop_table('boms')
