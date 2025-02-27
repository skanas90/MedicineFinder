"""Add availability, distance, and timings to Pharmacy model

Revision ID: 2023_10_06_01
Revises: 
Create Date: 2023-10-06 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2023_10_06_01'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to the Pharmacy table
    op.add_column('pharmacy', sa.Column('availability', sa.String(length=50), nullable=True))
    op.add_column('pharmacy', sa.Column('distance', sa.Float(), nullable=True))
    op.add_column('pharmacy', sa.Column('timings', sa.String(length=100), nullable=True))
   


def downgrade():
    # Remove the columns if we need to downgrade
    op.drop_column('pharmacy', 'availability')
    op.drop_column('pharmacy', 'distance')
    op.drop_column('pharmacy', 'timings')
