"""Editing manually by dropping a table

Revision ID: 701d9e702cc6
Revises: a8c31f6ecd62
Create Date: 2025-01-24 14:08:39.073575

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '701d9e702cc6'
down_revision = 'a8c31f6ecd62'
branch_labels = None
depends_on = None



def upgrade():
    # Drop the existing blueprints table if it exists
    op.drop_table('blueprints')

    # Recreate the blueprints table with the corrected schema
    op.create_table(
        'blueprints',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('configuration', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now(), nullable=True),
        sa.Column('version', sa.String(50), nullable=True),
        sa.Column('author', sa.String(255), nullable=True),
    )


def downgrade():
    # Drop the recreated blueprints table
    op.drop_table('blueprints')

    # Optionally recreate the previous blueprints table if needed
    op.create_table(
        'blueprints',
        sa.Column('id', sa.Integer, nullable=False),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('configuration', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=True),
        sa.Column('version', sa.String(50), nullable=True),
        sa.Column('author', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )