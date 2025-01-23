"""removing extra backref in Blueprint model

Revision ID: 3a5e0f5ff7d0
Revises: 081d3bbf492f
Create Date: 2025-01-22 12:13:08.899526

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a5e0f5ff7d0'
down_revision = '081d3bbf492f'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('blueprints')
    
    op.create_table('blueprints',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('configuration', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('version', sa.String(length=50), nullable=True),
    sa.Column('author', sa.String(length=255), nullable=True),
    )


    # ### end Alembic commands ###


def downgrade():
        op.drop_table('blueprints')
