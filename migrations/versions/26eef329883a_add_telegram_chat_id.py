"""ADD telegram_chat_id

Revision ID: 26eef329883a
Revises: 2bcb27d32f17
Create Date: 2024-05-12 13:13:33.353661

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26eef329883a'
down_revision: Union[str, None] = '2bcb27d32f17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('telegram_chat_id', sa.String(length=15), nullable=True))
    op.create_unique_constraint(None, 'users', ['telegram_chat_id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='unique')
    op.drop_column('users', 'telegram_chat_id')
    # ### end Alembic commands ###
