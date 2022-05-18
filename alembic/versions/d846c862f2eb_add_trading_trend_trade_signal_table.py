"""add trading_trend & trade & signal table

Revision ID: d846c862f2eb
Revises: 
Create Date: 2022-05-16 13:51:56.140082

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd846c862f2eb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('trade',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('symbol', sa.String(), nullable=True),
    sa.Column('strategy', sa.String(), nullable=True),
    sa.Column('trend', sa.String(), nullable=True),
    sa.Column('entry_signal', sa.String(), nullable=True),
    sa.Column('entry_date', sa.DateTime(), nullable=True),
    sa.Column('opened_position', sa.Float(), nullable=True),
    sa.Column('exit_signal', sa.String(), nullable=True),
    sa.Column('exit_date', sa.DateTime(), nullable=True),
    sa.Column('closed_position', sa.Float(), nullable=True),
    sa.Column('result', sa.Float(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('create_date', sa.DateTime(), nullable=True),
    sa.Column('quantity', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('trading_trend',
    sa.Column('symbol', sa.String(), nullable=False),
    sa.Column('trend_name', sa.String(), nullable=False),
    sa.Column('trend', sa.String(), nullable=True),
    sa.Column('timeframe', sa.String(), nullable=True),
    sa.Column('update_date', sa.Date(), nullable=False),
    sa.Column('update_time', sa.Time(), nullable=False),
    sa.PrimaryKeyConstraint('symbol', 'trend_name', 'update_date', 'update_time')
    )
    op.create_table('signal',
    sa.Column('symbol', sa.String(), nullable=False),
    sa.Column('indicator', sa.String(), nullable=False),
    sa.Column('indicator_value', sa.String(), nullable=True),
    sa.Column('trade_signal', sa.String(), nullable=True),
    sa.Column('trade_status', sa.String(), nullable=False),
    sa.Column('trade_id', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['trade_id'], ['trade.id'], ),
    sa.PrimaryKeyConstraint('symbol', 'indicator', 'trade_status', 'trade_id')
    )
    op.create_index(op.f('ix_signal_trade_id'), 'signal', ['trade_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_signal_trade_id'), table_name='signal')
    op.drop_table('signal')
    op.drop_table('trading_trend')
    op.drop_table('trade')
    # ### end Alembic commands ###