"""Fix referral system - change referred_by to Foreign Key

Revision ID: fix_referral_system
Revises: 01ae38a3a3d9
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_referral_system'
down_revision = '01ae38a3a3d9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Исправляем реферальную систему"""
    
    # 1. Добавляем новую колонку referred_by_id
    op.add_column('users', sa.Column('referred_by_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_users_referred_by_id'), 'users', ['referred_by_id'], unique=False)
    
    # 2. Создаем Foreign Key constraint
    op.create_foreign_key(
        'fk_users_referred_by_id_users',
        'users', 'users',
        ['referred_by_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # 3. Мигрируем данные из старой колонки в новую
    # Сначала получаем все существующие реферальные связи
    connection = op.get_bind()
    
    # Получаем всех пользователей с referred_by
    result = connection.execute(sa.text("""
        SELECT id, referred_by 
        FROM users 
        WHERE referred_by IS NOT NULL AND referred_by != ''
    """))
    
    # Обновляем referred_by_id для каждого пользователя
    for row in result:
        user_id = row[0]
        referral_code = row[1]
        
        # Находим ID пользователя с таким реферальным кодом
        referrer_result = connection.execute(sa.text("""
            SELECT id FROM users WHERE referral_code = :referral_code
        """), {'referral_code': referral_code})
        
        referrer_row = referrer_result.fetchone()
        if referrer_row:
            referrer_id = referrer_row[0]
            
            # Обновляем referred_by_id
            connection.execute(sa.text("""
                UPDATE users 
                SET referred_by_id = :referrer_id 
                WHERE id = :user_id
            """), {
                'referrer_id': referrer_id,
                'user_id': user_id
            })
    
    # 4. Удаляем старую колонку referred_by
    op.drop_column('users', 'referred_by')


def downgrade() -> None:
    """Откатываем изменения"""
    
    # 1. Добавляем обратно старую колонку referred_by
    op.add_column('users', sa.Column('referred_by', sa.String(length=20), nullable=True))
    
    # 2. Мигрируем данные обратно
    connection = op.get_bind()
    
    # Получаем всех пользователей с referred_by_id
    result = connection.execute(sa.text("""
        SELECT u.id, r.referral_code 
        FROM users u 
        JOIN users r ON u.referred_by_id = r.id
        WHERE u.referred_by_id IS NOT NULL
    """))
    
    # Обновляем referred_by для каждого пользователя
    for row in result:
        user_id = row[0]
        referral_code = row[1]
        
        connection.execute(sa.text("""
            UPDATE users 
            SET referred_by = :referral_code 
            WHERE id = :user_id
        """), {
            'referral_code': referral_code,
            'user_id': user_id
        })
    
    # 3. Удаляем Foreign Key constraint
    op.drop_constraint('fk_users_referred_by_id_users', 'users', type_='foreignkey')
    
    # 4. Удаляем индекс
    op.drop_index(op.f('ix_users_referred_by_id'), table_name='users')
    
    # 5. Удаляем новую колонку referred_by_id
    op.drop_column('users', 'referred_by_id') 