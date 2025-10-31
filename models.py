"""
Enterprise Marketing Agency Management Platform - Database Models
Comprehensive data models for all platform modules
"""

from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime,
    Boolean, Text, ForeignKey, Enum, JSON, Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import enum

Base = declarative_base()

# ================== ENUMS ==================

class UserRole(enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    TEAM_LEAD = "team_lead"
    CONTENT_CREATOR = "content_creator"
    DESIGNER = "designer"
    ACCOUNT_MANAGER = "account_manager"
    ANALYST = "analyst"
    FINANCE = "finance"

class ClientStatus(enum.Enum):
    LEAD = "lead"
    PROSPECT = "prospect"
    ACTIVE = "active"
    INACTIVE = "inactive"
    CHURNED = "churned"

class CampaignStatus(enum.Enum):
    PLANNING = "planning"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ContentStatus(enum.Enum):
    IDEA = "idea"
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    REJECTED = "rejected"

class TaskStatus(enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class InvoiceStatus(enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


# ================== ASSOCIATION TABLES ==================

campaign_team_members = Table(
    'campaign_team_members', Base.metadata,
    Column('campaign_id', Integer, ForeignKey('campaigns.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)

task_assignees = Table(
    'task_assignees', Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)

content_tags = Table(
    'content_tags', Base.metadata,
    Column('content_id', Integer, ForeignKey('content_items.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)


# ================== USER & AUTHENTICATION ==================

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(Enum(UserRole), default=UserRole.CONTENT_CREATOR)
    avatar_url = Column(String(500))
    phone = Column(String(50))
    department = Column(String(100))
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_clients = relationship("Client", back_populates="creator", foreign_keys="Client.created_by")
    assigned_tasks = relationship("Task", secondary=task_assignees, back_populates="assignees")
    campaigns = relationship("Campaign", secondary=campaign_team_members, back_populates="team_members")
    time_entries = relationship("TimeEntry", back_populates="user")
    comments = relationship("Comment", back_populates="user")


# ================== CLIENT MANAGEMENT (CRM) ==================

class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    company = Column(String(255))
    industry = Column(String(100))
    status = Column(Enum(ClientStatus), default=ClientStatus.LEAD)
    email = Column(String(255))
    phone = Column(String(50))
    website = Column(String(500))
    address = Column(Text)
    city = Column(String(100))
    country = Column(String(100))

    # Business details
    annual_revenue = Column(Float)
    company_size = Column(String(50))
    lead_source = Column(String(100))

    # Relationship management
    account_manager_id = Column(Integer, ForeignKey('users.id'))
    created_by = Column(Integer, ForeignKey('users.id'))

    # Notes and metadata
    notes = Column(Text)
    custom_fields = Column(JSON)

    # Timestamps
    acquisition_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", back_populates="created_clients", foreign_keys=[created_by])
    contacts = relationship("Contact", back_populates="client", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="client")
    contracts = relationship("Contract", back_populates="client")
    invoices = relationship("Invoice", back_populates="client")
    interactions = relationship("ClientInteraction", back_populates="client", cascade="all, delete-orphan")


class Contact(Base):
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100))
    title = Column(String(100))
    email = Column(String(255))
    phone = Column(String(50))
    is_primary = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", back_populates="contacts")


class ClientInteraction(Base):
    __tablename__ = 'client_interactions'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    interaction_type = Column(String(50))  # email, call, meeting, etc.
    subject = Column(String(255))
    description = Column(Text)
    interaction_date = Column(DateTime, default=datetime.utcnow)
    duration_minutes = Column(Integer)
    outcome = Column(Text)
    next_steps = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    client = relationship("Client", back_populates="interactions")


class Contract(Base):
    __tablename__ = 'contracts'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    contract_number = Column(String(100), unique=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    contract_value = Column(Float)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String(50), default='active')
    document_url = Column(String(500))
    terms = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", back_populates="contracts")


# ================== CAMPAIGN MANAGEMENT ==================

class Campaign(Base):
    __tablename__ = 'campaigns'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.PLANNING)

    # Campaign details
    campaign_type = Column(String(100))  # social_media, email, content, ppc, etc.
    objectives = Column(Text)
    target_audience = Column(Text)
    channels = Column(JSON)  # List of channels

    # Timeline
    start_date = Column(DateTime)
    end_date = Column(DateTime)

    # Budget
    budget = Column(Float)
    actual_spend = Column(Float, default=0.0)

    # Goals and KPIs
    goals = Column(JSON)
    kpis = Column(JSON)

    # Metadata
    tags = Column(JSON)
    custom_fields = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", back_populates="campaigns")
    team_members = relationship("User", secondary=campaign_team_members, back_populates="campaigns")
    content_items = relationship("ContentItem", back_populates="campaign")
    tasks = relationship("Task", back_populates="campaign")
    analytics = relationship("CampaignAnalytics", back_populates="campaign", cascade="all, delete-orphan")


# ================== CONTENT WORKFLOW ==================

class ContentItem(Base):
    __tablename__ = 'content_items'

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'))
    client_id = Column(Integer, ForeignKey('clients.id'))

    # Content details
    title = Column(String(255), nullable=False)
    content_type = Column(String(100))  # post, article, video, image, story, etc.
    platform = Column(String(100))  # facebook, instagram, linkedin, twitter, blog, etc.
    description = Column(Text)
    content_body = Column(Text)

    # Status and workflow
    status = Column(Enum(ContentStatus), default=ContentStatus.IDEA)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)

    # Assignment
    creator_id = Column(Integer, ForeignKey('users.id'))
    reviewer_id = Column(Integer, ForeignKey('users.id'))

    # Scheduling
    scheduled_date = Column(DateTime)
    published_date = Column(DateTime)

    # Assets
    assets = Column(JSON)  # URLs to images, videos, documents

    # Performance
    performance_metrics = Column(JSON)

    # Metadata
    hashtags = Column(JSON)
    mentions = Column(JSON)
    custom_fields = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="content_items")
    tags_rel = relationship("Tag", secondary=content_tags, back_populates="content_items")
    comments = relationship("Comment", back_populates="content_item", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="content_item", cascade="all, delete-orphan")


class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50))
    color = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    content_items = relationship("ContentItem", secondary=content_tags, back_populates="tags_rel")


class Approval(Base):
    __tablename__ = 'approvals'

    id = Column(Integer, primary_key=True)
    content_item_id = Column(Integer, ForeignKey('content_items.id'), nullable=False)
    reviewer_id = Column(Integer, ForeignKey('users.id'))
    status = Column(String(50))  # pending, approved, rejected, changes_requested
    feedback = Column(Text)
    approved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    content_item = relationship("ContentItem", back_populates="approvals")


# ================== TASK MANAGEMENT ==================

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'))
    client_id = Column(Integer, ForeignKey('clients.id'))
    content_item_id = Column(Integer, ForeignKey('content_items.id'))

    # Task details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)

    # Assignment
    created_by = Column(Integer, ForeignKey('users.id'))

    # Timeline
    due_date = Column(DateTime)
    start_date = Column(DateTime)
    completed_at = Column(DateTime)

    # Estimation
    estimated_hours = Column(Float)
    actual_hours = Column(Float)

    # Dependencies
    parent_task_id = Column(Integer, ForeignKey('tasks.id'))

    # Metadata
    tags = Column(JSON)
    custom_fields = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="tasks")
    assignees = relationship("User", secondary=task_assignees, back_populates="assigned_tasks")
    subtasks = relationship("Task", backref="parent_task", remote_side=[id])
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")
    time_entries = relationship("TimeEntry", back_populates="task")


# ================== FINANCE MANAGEMENT ==================

class Invoice(Base):
    __tablename__ = 'invoices'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'))

    # Invoice details
    invoice_number = Column(String(100), unique=True, nullable=False)
    title = Column(String(255))
    description = Column(Text)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)

    # Financial
    subtotal = Column(Float, default=0.0)
    tax_rate = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0.0)

    # Dates
    issue_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    paid_date = Column(DateTime)

    # Additional info
    notes = Column(Text)
    terms = Column(Text)
    currency = Column(String(10), default='USD')

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice")


class InvoiceLineItem(Base):
    __tablename__ = 'invoice_line_items'

    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    description = Column(String(500), nullable=False)
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    tax_rate = Column(Float, default=0.0)

    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")


class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)

    # Payment details
    amount = Column(Float, nullable=False)
    payment_method = Column(String(100))  # credit_card, bank_transfer, paypal, etc.
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    transaction_id = Column(String(255))

    # Dates
    payment_date = Column(DateTime, default=datetime.utcnow)

    # Additional info
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    invoice = relationship("Invoice", back_populates="payments")


class Expense(Base):
    __tablename__ = 'expenses'

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'))
    client_id = Column(Integer, ForeignKey('clients.id'))
    user_id = Column(Integer, ForeignKey('users.id'))

    # Expense details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # ads, software, services, travel, etc.
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default='USD')

    # Additional info
    vendor = Column(String(255))
    receipt_url = Column(String(500))
    is_billable = Column(Boolean, default=False)
    is_reimbursable = Column(Boolean, default=False)

    # Dates
    expense_date = Column(DateTime, default=datetime.utcnow)

    # Status
    status = Column(String(50), default='pending')  # pending, approved, rejected
    approved_by = Column(Integer, ForeignKey('users.id'))
    approved_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])


class TimeEntry(Base):
    __tablename__ = 'time_entries'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('tasks.id'))
    campaign_id = Column(Integer, ForeignKey('campaigns.id'))
    client_id = Column(Integer, ForeignKey('clients.id'))

    # Time tracking
    description = Column(String(500))
    hours = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

    # Billing
    is_billable = Column(Boolean, default=True)
    hourly_rate = Column(Float)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="time_entries")
    task = relationship("Task", back_populates="time_entries")


# ================== ANALYTICS ==================

class CampaignAnalytics(Base):
    __tablename__ = 'campaign_analytics'

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=False)

    # Date
    date = Column(DateTime, default=datetime.utcnow)

    # Metrics
    impressions = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    engagement = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)

    # Rates
    ctr = Column(Float, default=0.0)  # Click-through rate
    conversion_rate = Column(Float, default=0.0)
    engagement_rate = Column(Float, default=0.0)

    # Financial
    spend = Column(Float, default=0.0)
    revenue = Column(Float, default=0.0)
    roi = Column(Float, default=0.0)
    cpc = Column(Float, default=0.0)  # Cost per click
    cpa = Column(Float, default=0.0)  # Cost per acquisition

    # Platform-specific metrics
    platform_metrics = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="analytics")


# ================== COLLABORATION ==================

class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content_item_id = Column(Integer, ForeignKey('content_items.id'))
    task_id = Column(Integer, ForeignKey('tasks.id'))

    # Comment details
    text = Column(Text, nullable=False)
    parent_comment_id = Column(Integer, ForeignKey('comments.id'))

    # Metadata
    attachments = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="comments")
    content_item = relationship("ContentItem", back_populates="comments")
    task = relationship("Task", back_populates="comments")
    replies = relationship("Comment", backref="parent_comment", remote_side=[id])


# ================== AUTOMATION ==================

class Workflow(Base):
    __tablename__ = 'workflows'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    trigger_type = Column(String(100))  # time, event, manual
    trigger_config = Column(JSON)
    actions = Column(JSON)  # List of actions to perform
    conditions = Column(JSON)  # Conditions to check
    is_active = Column(Boolean, default=True)

    # Statistics
    run_count = Column(Integer, default=0)
    last_run = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Notification details
    title = Column(String(255), nullable=False)
    message = Column(Text)
    notification_type = Column(String(100))  # info, warning, success, error

    # Link
    link_url = Column(String(500))
    link_text = Column(String(255))

    # Status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


# ================== INTEGRATIONS ==================

class Integration(Base):
    __tablename__ = 'integrations'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    platform = Column(String(100))  # facebook, google_ads, mailchimp, etc.
    description = Column(Text)

    # Configuration
    config = Column(JSON)  # API keys, tokens, settings
    credentials = Column(JSON)  # Encrypted credentials

    # Status
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    sync_status = Column(String(100))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100))
    entity_id = Column(Integer)
    details = Column(JSON)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow)


# ================== DATABASE INITIALIZATION ==================

def init_db(database_url='sqlite:///marketing_platform.db'):
    """Initialize the database and create all tables"""
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)


def get_session(database_url='sqlite:///marketing_platform.db'):
    """Get a database session"""
    engine, Session = init_db(database_url)
    return Session()
