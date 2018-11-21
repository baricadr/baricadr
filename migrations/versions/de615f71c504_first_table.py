"""first table

Revision ID: de615f71c504
Revises: 
Create Date: 2018-11-21 11:58:06.371780

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'de615f71c504'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pull_task',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('path', sa.Text(), nullable=True),
    sa.Column('task_id', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pull_task_path'), 'pull_task', ['path'], unique=True)
    op.create_index(op.f('ix_pull_task_task_id'), 'pull_task', ['task_id'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_pull_task_task_id'), table_name='pull_task')
    op.drop_index(op.f('ix_pull_task_path'), table_name='pull_task')
    op.drop_table('pull_task')
    # ### end Alembic commands ###
