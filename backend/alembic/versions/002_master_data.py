"""Master data management migration (Phase 2)

Revision ID: 002_master_data
Revises: 001_initial_users
Create Date: 2026-11-18 10:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '002_master_data'
down_revision = '001_initial_users'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Price Lists
    op.create_table(
        'price_lists',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('customer_type', sa.String(length=20), nullable=False, server_default='ALL'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_price_lists_id'), 'price_lists', ['id'], unique=False)
    op.create_index(op.f('ix_price_lists_name'), 'price_lists', ['name'], unique=True)

    # 2. Customers
    op.create_table(
        'customers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('customer_code', sa.String(length=50), nullable=False),
        sa.Column('customer_name', sa.String(length=150), nullable=False),
        sa.Column('customer_type', sa.String(length=20), nullable=False, server_default='RETAILER'),
        sa.Column('contact_person', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('gstin', sa.String(length=15), nullable=False),
        sa.Column('billing_address', sa.Text(), nullable=False),
        sa.Column('shipping_address', sa.Text(), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('district', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('state_code', sa.String(length=2), nullable=False),
        sa.Column('pincode', sa.String(length=10), nullable=False),
        sa.Column('price_list_id', sa.String(length=36), nullable=True),
        sa.Column('credit_limit_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('assigned_salesman_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['assigned_salesman_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['price_list_id'], ['price_lists.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customers_id'), 'customers', ['id'], unique=False)
    op.create_index(op.f('ix_customers_customer_code'), 'customers', ['customer_code'], unique=True)
    op.create_index(op.f('ix_customers_customer_name'), 'customers', ['customer_name'], unique=False)
    op.create_index(op.f('ix_customers_gstin'), 'customers', ['gstin'], unique=False)

    # 3. Suppliers
    op.create_table(
        'suppliers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('supplier_code', sa.String(length=50), nullable=False),
        sa.Column('supplier_name', sa.String(length=150), nullable=False),
        sa.Column('contact_person', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('gstin', sa.String(length=15), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('state_code', sa.String(length=2), nullable=False),
        sa.Column('pincode', sa.String(length=10), nullable=False),
        sa.Column('payment_terms', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_suppliers_id'), 'suppliers', ['id'], unique=False)
    op.create_index(op.f('ix_suppliers_supplier_code'), 'suppliers', ['supplier_code'], unique=True)
    op.create_index(op.f('ix_suppliers_supplier_name'), 'suppliers', ['supplier_name'], unique=False)

    # 4. Products
    op.create_table(
        'products',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('sku', sa.String(length=50), nullable=False),
        sa.Column('product_name', sa.String(length=150), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('pack_size', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('pack_size_unit', sa.String(length=20), nullable=False),
        sa.Column('hsn_code', sa.String(length=20), nullable=False),
        sa.Column('gst_rate', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('selling_price_paise', sa.BigInteger(), nullable=False),
        sa.Column('base_unit', sa.String(length=20), nullable=False),
        sa.Column('packets_per_carton', sa.Integer(), nullable=False),
        sa.Column('reorder_level', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_index(op.f('ix_products_sku'), 'products', ['sku'], unique=True)
    op.create_index(op.f('ix_products_product_name'), 'products', ['product_name'], unique=False)

    # 5. Price List Items
    op.create_table(
        'price_list_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('price_list_id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('selling_price_paise', sa.BigInteger(), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['price_list_id'], ['price_lists.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('price_list_id', 'product_id', name='uq_price_list_product')
    )
    op.create_index(op.f('ix_price_list_items_id'), 'price_list_items', ['id'], unique=False)

    # 6. Raw Materials
    op.create_table(
        'raw_materials',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('material_code', sa.String(length=50), nullable=False),
        sa.Column('material_name', sa.String(length=150), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('base_unit', sa.String(length=20), nullable=False),
        sa.Column('reorder_level', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_raw_materials_id'), 'raw_materials', ['id'], unique=False)
    op.create_index(op.f('ix_raw_materials_material_code'), 'raw_materials', ['material_code'], unique=True)
    op.create_index(op.f('ix_raw_materials_material_name'), 'raw_materials', ['material_name'], unique=False)

    # 7. Packaging Items
    op.create_table(
        'packaging_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('packaging_code', sa.String(length=50), nullable=False),
        sa.Column('packaging_name', sa.String(length=150), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('base_unit', sa.String(length=20), nullable=False),
        sa.Column('reorder_level', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_packaging_items_id'), 'packaging_items', ['id'], unique=False)
    op.create_index(op.f('ix_packaging_items_packaging_code'), 'packaging_items', ['packaging_code'], unique=True)
    op.create_index(op.f('ix_packaging_items_packaging_name'), 'packaging_items', ['packaging_name'], unique=False)


def downgrade() -> None:
    op.drop_table('packaging_items')
    op.drop_table('raw_materials')
    op.drop_table('price_list_items')
    op.drop_table('products')
    op.drop_table('suppliers')
    op.drop_table('customers')
    op.drop_table('price_lists')
