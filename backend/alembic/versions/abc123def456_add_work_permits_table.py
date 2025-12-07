"""add_work_permits_table

Revision ID: abc123def456
Revises: 62a9378d6bdc
Create Date: 2025-12-06 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'abc123def456'
down_revision = '62a9378d6bdc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаем таблицу work_permits
    op.create_table(
        'work_permits',
        sa.Column('permit_id', sa.Integer(), nullable=False),
        sa.Column('permit_number', sa.String(length=50), nullable=False),
        sa.Column('object_id', sa.Integer(), nullable=False),
        sa.Column('diagnostic_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('issued_date', sa.Date(), nullable=False),
        sa.Column('issued_by', sa.String(length=255), nullable=True),
        sa.Column('closed_date', sa.Date(), nullable=True),
        sa.Column('closed_by', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['object_id'], ['objects.id'], ),
        sa.ForeignKeyConstraint(['diagnostic_id'], ['diagnostics.diag_id'], ),
        sa.PrimaryKeyConstraint('permit_id')
    )
    # Создаем индексы
    op.create_index(op.f('ix_work_permits_permit_id'), 'work_permits', ['permit_id'], unique=False)
    op.create_index(op.f('ix_work_permits_permit_number'), 'work_permits', ['permit_number'], unique=True)
    op.create_index(op.f('ix_work_permits_object_id'), 'work_permits', ['object_id'], unique=False)
    op.create_index(op.f('ix_work_permits_diagnostic_id'), 'work_permits', ['diagnostic_id'], unique=False)
    op.create_index(op.f('ix_work_permits_status'), 'work_permits', ['status'], unique=False)
    op.create_index(op.f('ix_work_permits_issued_date'), 'work_permits', ['issued_date'], unique=False)


def downgrade() -> None:
    # Удаляем индексы
    op.drop_index(op.f('ix_work_permits_issued_date'), table_name='work_permits')
    op.drop_index(op.f('ix_work_permits_status'), table_name='work_permits')
    op.drop_index(op.f('ix_work_permits_diagnostic_id'), table_name='work_permits')
    op.drop_index(op.f('ix_work_permits_object_id'), table_name='work_permits')
    op.drop_index(op.f('ix_work_permits_permit_number'), table_name='work_permits')
    op.drop_index(op.f('ix_work_permits_permit_id'), table_name='work_permits')
    # Удаляем таблицу
    op.drop_table('work_permits')

