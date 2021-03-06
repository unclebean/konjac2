"""add h4_date column for trade table

Revision ID: 28dcaac91018
Revises: 8f78e97382b0
Create Date: 2022-07-23 14:50:16.269019

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '28dcaac91018'
down_revision = '8f78e97382b0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('trade', sa.Column('h4_date', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('trade', 'h4_date')
    # ### end Alembic commands ###
