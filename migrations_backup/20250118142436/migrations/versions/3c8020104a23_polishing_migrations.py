"""polishing migrations

Revision ID: 3c8020104a23
Revises: 2f84cc0c5a15
Create Date: 2025-01-18 14:14:52.079072

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3c8020104a23'
down_revision = '2f84cc0c5a15'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('dashboard_data', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'users', ['user_id'], ['id'])

    with op.batch_alter_table('device_firmware_history', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key(None, 'devices', ['device_id'], ['id'])
        batch_op.create_foreign_key(None, 'firmwares', ['firmware_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('device_firmware_history', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key(None, 'firmwares', ['firmware_id'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'devices', ['device_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('dashboard_data', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')

    # ### end Alembic commands ###
