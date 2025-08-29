"""reencrypt existing user data"""

from alembic import op
import sqlalchemy as sa

from app.utils.encryption import encrypt, decrypt

# revision identifiers, used by Alembic.
revision = 'c0eacb8f3a11'
down_revision = 'b60e49215224'
branch_labels = None
depends_on = None


sensitive_fields = [
    'email',
    'full_name',
    'verification_token',
    'mfa_secret',
    'backup_codes',
    'password_reset_token',
    'refresh_token',
]


def upgrade():
    conn = op.get_bind()
    users = conn.execute(
        sa.text(
            'SELECT id, ' + ', '.join(sensitive_fields) + ' FROM users'
        )
    ).fetchall()
    for u in users:
        update = { 'id': u.id }
        for field in sensitive_fields:
            value = getattr(u, field)
            if value:
                update[field] = encrypt(value)
            else:
                update[field] = value
        conn.execute(
            sa.text(
                'UPDATE users SET '
                + ', '.join(f"{f}=:{f}" for f in sensitive_fields)
                + ' WHERE id=:id'
            ),
            update,
        )



def downgrade():
    conn = op.get_bind()
    users = conn.execute(
        sa.text(
            'SELECT id, ' + ', '.join(sensitive_fields) + ' FROM users'
        )
    ).fetchall()
    for u in users:
        update = { 'id': u.id }
        for field in sensitive_fields:
            value = getattr(u, field)
            if value and value.startswith('enc:'):
                update[field] = decrypt(value)
            else:
                update[field] = value
        conn.execute(
            sa.text(
                'UPDATE users SET '
                + ', '.join(f"{f}=:{f}" for f in sensitive_fields)
                + ' WHERE id=:id'
            ),
            update,
        )
