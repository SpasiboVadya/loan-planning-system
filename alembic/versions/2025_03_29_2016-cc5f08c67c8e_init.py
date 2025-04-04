"""init

Revision ID: cc5f08c67c8e
Revises: 
Create Date: 2025-03-29 20:16:19.341451

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc5f08c67c8e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('dictionary',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_dictionary_id'), 'dictionary', ['id'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('login', sa.String(length=50), nullable=False),
    sa.Column('password', sa.String(length=255), nullable=False),
    sa.Column('registration_date', sa.Date(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('login')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_table('credits',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('issuance_date', sa.DateTime(), nullable=False),
    sa.Column('return_date', sa.DateTime(), nullable=False),
    sa.Column('actual_return_date', sa.DateTime(), nullable=True),
    sa.Column('body', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('percent', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_credits_id'), 'credits', ['id'], unique=False)
    op.create_table('plans',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('period', sa.Date(), nullable=False),
    sa.Column('sum', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['dictionary.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plans_id'), 'plans', ['id'], unique=False)
    op.create_table('payments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sum', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('payment_date', sa.DateTime(), nullable=False),
    sa.Column('credit_id', sa.Integer(), nullable=False),
    sa.Column('type_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['credit_id'], ['credits.id'], ),
    sa.ForeignKeyConstraint(['type_id'], ['dictionary.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_payments_id'), table_name='payments')
    op.drop_table('payments')
    op.drop_index(op.f('ix_plans_id'), table_name='plans')
    op.drop_table('plans')
    op.drop_index(op.f('ix_credits_id'), table_name='credits')
    op.drop_table('credits')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_dictionary_id'), table_name='dictionary')
    op.drop_table('dictionary')
    # ### end Alembic commands ###
