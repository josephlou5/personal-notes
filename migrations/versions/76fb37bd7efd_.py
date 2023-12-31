"""Initial migration

Revision ID: 76fb37bd7efd
Revises: 
Create Date: 2023-11-04 16:42:42.978558

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '76fb37bd7efd'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=30), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('display_name', sa.String(length=100), nullable=False),
    sa.Column('is_admin', sa.Boolean(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('DraftNotes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('recipient_id', sa.Integer(), nullable=True),
    sa.Column('text', sa.String(length=10000), nullable=False),
    sa.ForeignKeyConstraint(['recipient_id'], ['Users.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['Users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('FriendNicknames',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('friend_id', sa.Integer(), nullable=False),
    sa.Column('nickname', sa.String(length=100), nullable=False),
    sa.ForeignKeyConstraint(['friend_id'], ['Users.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['Users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'friend_id')
    )
    op.create_table('FriendRequests',
    sa.Column('sender_id', sa.Integer(), nullable=False),
    sa.Column('recipient_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['recipient_id'], ['Users.id'], ),
    sa.ForeignKeyConstraint(['sender_id'], ['Users.id'], ),
    sa.PrimaryKeyConstraint('sender_id', 'recipient_id')
    )
    op.create_table('Friendships',
    sa.Column('user1_id', sa.Integer(), nullable=False),
    sa.Column('user2_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user1_id'], ['Users.id'], ),
    sa.ForeignKeyConstraint(['user2_id'], ['Users.id'], ),
    sa.PrimaryKeyConstraint('user1_id', 'user2_id')
    )
    op.create_table('Notes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sender_id', sa.Integer(), nullable=False),
    sa.Column('recipient_id', sa.Integer(), nullable=False),
    sa.Column('text', sa.String(length=10000), nullable=False),
    sa.Column('time_sent', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['recipient_id'], ['Users.id'], ),
    sa.ForeignKeyConstraint(['sender_id'], ['Users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('DeletedNotes',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('note_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['note_id'], ['Notes.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['Users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'note_id')
    )
    op.create_table('FavoriteNotes',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('note_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['note_id'], ['Notes.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['Users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'note_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('FavoriteNotes')
    op.drop_table('DeletedNotes')
    op.drop_table('Notes')
    op.drop_table('Friendships')
    op.drop_table('FriendRequests')
    op.drop_table('FriendNicknames')
    op.drop_table('DraftNotes')
    op.drop_table('Users')
    # ### end Alembic commands ###
