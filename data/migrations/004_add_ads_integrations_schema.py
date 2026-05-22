"""
004_add_ads_integrations_schema

Creates tables for ad integrations, performance data, and attribution
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    # Integrations table
    op.create_table(
        'integrations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('access_token', sa.LargeBinary(), nullable=True),  # Encrypted
        sa.Column('refresh_token', sa.LargeBinary(), nullable=True),  # Encrypted
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'provider', name='uq_user_provider')
    )

    # Ad campaigns table
    op.create_table(
        'ad_campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('integration_id', sa.Integer(), nullable=False),
        sa.Column('external_campaign_id', sa.String(100), nullable=False),
        sa.Column('campaign_name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('budget', sa.Numeric(12, 2), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False, server_default='RUB'),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('synced_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('integration_id', 'external_campaign_id', name='uq_integration_campaign')
    )

    # Ad performance table (daily statistics)
    op.create_table(
        'ad_performance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('impressions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('clicks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('spent', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('conversions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('revenue', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('ctr', sa.Numeric(5, 4), nullable=True),
        sa.Column('cpc', sa.Numeric(10, 2), nullable=True),
        sa.Column('roas', sa.Numeric(5, 2), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('synced_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['campaign_id'], ['ad_campaigns.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('campaign_id', 'date', name='uq_campaign_date')
    )

    # Look-alike audiences table
    op.create_table(
        'lookalike_audiences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('integration_id', sa.Integer(), nullable=False),
        sa.Column('segment_id', sa.String(100), nullable=False),
        sa.Column('segment_name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('size', sa.Integer(), nullable=True),
        sa.Column('seed_size', sa.Integer(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # ML Models table
    op.create_table(
        'ml_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('marketplace', sa.String(50), nullable=False),
        sa.Column('model_path', sa.String(255), nullable=False),
        sa.Column('accuracy', sa.Numeric(5, 4), nullable=True),
        sa.Column('auc_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('feature_count', sa.Integer(), nullable=False),
        sa.Column('trained_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # AI Queries table (for logging and audit)
    op.create_table(
        'ai_queries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('model_used', sa.String(50), nullable=False, server_default='gpt-4o'),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('cost', sa.Numeric(10, 4), nullable=True),
        sa.Column('cached', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Attributed orders table (for order-to-click attribution)
    op.create_table(
        'attributed_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.String(100), nullable=False),
        sa.Column('marketplace', sa.String(50), nullable=False),
        sa.Column('trax_id', sa.String(100), nullable=True),
        sa.Column('click_timestamp', sa.DateTime(), nullable=True),
        sa.Column('order_timestamp', sa.DateTime(), nullable=False),
        sa.Column('order_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('confidence', sa.Numeric(5, 4), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('model_version', sa.String(20), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id', 'marketplace', name='uq_order_marketplace')
    )

    # Create indexes
    op.create_index('ix_integrations_user_provider', 'integrations', ['user_id', 'provider'])
    op.create_index('ix_ad_campaigns_integration', 'ad_campaigns', ['integration_id'])
    op.create_index('ix_ad_performance_campaign_date', 'ad_performance', ['campaign_id', 'date'])
    op.create_index('ix_lookalike_audiences_integration', 'lookalike_audiences', ['integration_id'])
    op.create_index('ix_ai_queries_user', 'ai_queries', ['user_id', 'created_at'])
    op.create_index('ix_attributed_orders_marketplace', 'attributed_orders', ['marketplace', 'order_timestamp'])


def downgrade():
    op.drop_index('ix_attributed_orders_marketplace')
    op.drop_index('ix_ai_queries_user')
    op.drop_index('ix_lookalike_audiences_integration')
    op.drop_index('ix_ad_performance_campaign_date')
    op.drop_index('ix_ad_campaigns_integration')
    op.drop_index('ix_integrations_user_provider')
    op.drop_table('attributed_orders')
    op.drop_table('ai_queries')
    op.drop_table('ml_models')
    op.drop_table('lookalike_audiences')
    op.drop_table('ad_performance')
    op.drop_table('ad_campaigns')
    op.drop_table('integrations')
