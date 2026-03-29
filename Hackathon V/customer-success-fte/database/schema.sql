-- =============================================================================
-- CUSTOMER SUCCESS FTE - CRM/TICKET MANAGEMENT SYSTEM
-- =============================================================================
-- This PostgreSQL schema serves as your complete CRM system for tracking:
-- - Customers (unified across all channels)
-- - Conversations and message history
-- - Support tickets and their lifecycle
-- - Knowledge base for AI responses
-- - Performance metrics and reporting
-- =============================================================================

-- Enable pgvector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- CORE TABLES
-- =============================================================================

-- Customers table (unified across channels)
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Customer identifiers (for cross-channel matching)
CREATE TABLE customer_identifiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    identifier_type VARCHAR(50) NOT NULL,  -- 'email', 'phone', 'whatsapp'
    identifier_value VARCHAR(255) NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(identifier_type, identifier_value)
);

-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    initial_channel VARCHAR(50) NOT NULL,  -- 'email', 'whatsapp', 'web_form'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'closed', 'escalated'
    sentiment_score DECIMAL(3,2),
    resolution_type VARCHAR(50),  -- 'resolved', 'escalated', 'abandoned'
    escalated_to VARCHAR(255),
    metadata JSONB DEFAULT '{}'
);

-- Messages table (with channel tracking)
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL,  -- 'email', 'whatsapp', 'web_form'
    direction VARCHAR(20) NOT NULL,  -- 'inbound', 'outbound'
    role VARCHAR(20) NOT NULL,  -- 'customer', 'agent', 'system'
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tokens_used INTEGER,
    latency_ms INTEGER,
    tool_calls JSONB DEFAULT '[]',
    channel_message_id VARCHAR(255),  -- External ID (Gmail message ID, Twilio SID)
    delivery_status VARCHAR(50) DEFAULT 'pending'  -- 'pending', 'sent', 'delivered', 'failed'
);

-- Tickets table
CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    source_channel VARCHAR(50) NOT NULL,
    category VARCHAR(100),  -- 'general', 'technical', 'billing', 'feedback', 'bug_report'
    priority VARCHAR(20) DEFAULT 'medium',  -- 'low', 'medium', 'high', 'critical'
    status VARCHAR(50) DEFAULT 'open',  -- 'open', 'in_progress', 'resolved', 'escalated', 'closed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT
);

-- Knowledge base entries (with vector embeddings for semantic search)
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),  -- 'getting_started', 'authentication', 'api_reference', 'troubleshooting'
    embedding VECTOR(1536),  -- OpenAI embedding dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Channel configurations
CREATE TABLE channel_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel VARCHAR(50) UNIQUE NOT NULL,  -- 'email', 'whatsapp', 'web_form'
    enabled BOOLEAN DEFAULT TRUE,
    config JSONB NOT NULL,  -- API keys, webhook URLs, etc. (store sensitive data in secrets)
    response_template TEXT,
    max_response_length INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent performance metrics
CREATE TABLE agent_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    channel VARCHAR(50),  -- Optional: channel-specific metrics
    dimensions JSONB DEFAULT '{}',  -- Additional metadata
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Escalations table
CREATE TABLE escalations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID REFERENCES tickets(id) ON DELETE CASCADE,
    reason_code VARCHAR(50) NOT NULL,  -- 'pricing_inquiry', 'refund_request', 'legal_threat', etc.
    urgency VARCHAR(20) DEFAULT 'normal',  -- 'normal', 'high', 'critical'
    assigned_to VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'assigned', 'resolved'
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Customer indexes
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_customers_created_at ON customers(created_at);

-- Customer identifiers indexes
CREATE INDEX idx_customer_identifiers_customer ON customer_identifiers(customer_id);
CREATE INDEX idx_customer_identifiers_value ON customer_identifiers(identifier_value);
CREATE INDEX idx_customer_identifiers_type_value ON customer_identifiers(identifier_type, identifier_value);

-- Conversations indexes
CREATE INDEX idx_conversations_customer ON conversations(customer_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_channel ON conversations(initial_channel);
CREATE INDEX idx_conversations_started_at ON conversations(started_at);
CREATE INDEX idx_conversations_sentiment ON conversations(sentiment_score);

-- Messages indexes
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_channel ON messages(channel);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_direction ON messages(direction);

-- Tickets indexes
CREATE INDEX idx_tickets_customer ON tickets(customer_id);
CREATE INDEX idx_tickets_conversation ON tickets(conversation_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_channel ON tickets(source_channel);
CREATE INDEX idx_tickets_category ON tickets(category);
CREATE INDEX idx_tickets_created_at ON tickets(created_at);

-- Knowledge base indexes (vector similarity search)
CREATE INDEX idx_knowledge_embedding ON knowledge_base USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_knowledge_category ON knowledge_base(category);
CREATE INDEX idx_knowledge_title ON knowledge_base USING gin (title gin_trgm_ops);

-- Escalations indexes
CREATE INDEX idx_escalations_ticket ON escalations(ticket_id);
CREATE INDEX idx_escalations_status ON escalations(status);
CREATE INDEX idx_escalations_reason ON escalations(reason_code);
CREATE INDEX idx_escalations_created_at ON escalations(created_at);

-- Metrics indexes
CREATE INDEX idx_metrics_name ON agent_metrics(metric_name);
CREATE INDEX idx_metrics_channel ON agent_metrics(channel);
CREATE INDEX idx_metrics_recorded_at ON agent_metrics(recorded_at);

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Auto-update updated_at for knowledge_base
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_knowledge_base_updated_at
    BEFORE UPDATE ON knowledge_base
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Active conversations view
CREATE VIEW active_conversations AS
SELECT
    c.id,
    c.customer_id,
    c.initial_channel,
    c.started_at,
    c.sentiment_score,
    cu.email,
    cu.phone,
    COUNT(m.id) as message_count,
    MAX(m.created_at) as last_message_at
FROM conversations c
JOIN customers cu ON c.customer_id = cu.id
LEFT JOIN messages m ON m.conversation_id = c.id
WHERE c.status = 'active'
GROUP BY c.id, cu.email, cu.phone;

-- Ticket summary by channel (last 24 hours)
CREATE VIEW ticket_summary_24h AS
SELECT
    source_channel,
    status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))) as avg_resolution_time_seconds
FROM tickets
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY source_channel, status;

-- Customer conversation history (unified across channels)
CREATE VIEW customer_history AS
SELECT
    cu.id as customer_id,
    cu.email,
    cu.phone,
    c.id as conversation_id,
    c.initial_channel,
    c.started_at,
    c.status,
    t.id as ticket_id,
    t.category,
    t.status as ticket_status
FROM customers cu
JOIN conversations c ON c.customer_id = cu.id
LEFT JOIN tickets t ON t.conversation_id = c.id
ORDER BY c.started_at DESC;

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Insert default channel configurations
INSERT INTO channel_configs (channel, enabled, config, max_response_length) VALUES
    ('email', TRUE, '{"greeting": "Dear Customer", "closing": "Best regards, TechCorp AI Support Team"}', 2000),
    ('whatsapp', TRUE, '{"greeting": "", "closing": "Reply for more help"}', 1600),
    ('web_form', TRUE, '{"greeting": "", "closing": "Need more help? Reply to this message"}', 1000)
ON CONFLICT (channel) DO NOTHING;

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE customers IS 'Unified customer profile across all communication channels';
COMMENT ON TABLE customer_identifiers IS 'Maps email, phone, WhatsApp IDs to unified customer records';
COMMENT ON TABLE conversations IS 'Conversation threads with cross-channel continuity';
COMMENT ON TABLE messages IS 'All messages with channel metadata and delivery tracking';
COMMENT ON TABLE tickets IS 'Support tickets with lifecycle tracking';
COMMENT ON TABLE knowledge_base IS 'Product documentation with vector embeddings for semantic search';
COMMENT ON TABLE escalations IS 'Human escalations with reason codes and routing';
