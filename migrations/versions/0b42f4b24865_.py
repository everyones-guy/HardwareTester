"""Add firmware and dashboard updates

Revision ID: 0b42f4b24865
Revises: dd707bccdeda
Create Date: 2025-01-13 20:20:37.227787

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0b42f4b24865'
down_revision = 'dd707bccdeda'
branch_labels = None
depends_on = None


def upgrade():
    # Create the `firmwares` table
    op.create_table(
        'firmwares',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hash', sa.String(length=64), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('mdf', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hash')
    )

    # Create the `device_firmware_history` table
    op.create_table(
        'device_firmware_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('firmware_id', sa.Integer(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['firmware_id'], ['firmwares.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Add columns to the `dashboard_data` table
    op.add_column('dashboard_data', sa.Column('user_id', sa.Integer(), nullable=False))
    op.add_column('dashboard_data', sa.Column('title', sa.String(length=255), nullable=False))
    op.add_column('dashboard_data', sa.Column('type', sa.String(length=50), nullable=False))
    op.add_column('dashboard_data', sa.Column('created_at', sa.DateTime(), default=sa.func.now()))
    op.add_column('dashboard_data', sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()))

    # Add foreign key constraint for `user_id` in `dashboard_data`
    op.create_foreign_key(
        'fk_dashboard_data_user_id',
        'dashboard_data',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    # Drop foreign key constraint for `user_id` in `dashboard_data`
    op.drop_constraint('fk_dashboard_data_user_id', 'dashboard_data', type_='foreignkey')

    # Remove columns from the `dashboard_data` table
    op.drop_column('dashboard_data', 'updated_at')
    op.drop_column('dashboard_data', 'created_at')
    op.drop_column('dashboard_data', 'type')
    op.drop_column('dashboard_data', 'title')
    op.drop_column('dashboard_data', 'user_id')

    # Drop the `device_firmware_history` table
    op.drop_table('device_firmware_history')

    # Drop the `firmwares` table
    op.drop_table('firmwares')
