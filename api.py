"""
Enterprise Marketing Agency Management Platform - Main API
RESTful API for all platform modules with authentication and authorization
"""

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from functools import wraps
import jwt
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import os
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import joinedload

from models import (
    init_db, Base, User, Client, Contact, ClientInteraction, Contract,
    Campaign, ContentItem, Tag, Approval, Task, Invoice, InvoiceLineItem,
    Payment, Expense, TimeEntry, CampaignAnalytics, Comment, Workflow,
    Notification, Integration, AuditLog, UserRole, ClientStatus,
    CampaignStatus, ContentStatus, TaskStatus, TaskPriority,
    InvoiceStatus, PaymentStatus
)

# ================== CONFIG ==================

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'sqlite:///marketing_platform.db')

# Initialize database
engine, Session = init_db(app.config['DATABASE_URL'])


# ================== AUTHENTICATION ==================

def create_token(user_id, username, role):
    """Create JWT token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')


def token_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            if token.startswith('Bearer '):
                token = token[7:]

            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            session = Session()
            current_user = session.query(User).filter_by(id=data['user_id']).first()

            if not current_user or not current_user.is_active:
                return jsonify({'error': 'Invalid token'}), 401

            g.current_user = current_user
            g.session = session

        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            return jsonify({'error': str(e)}), 401

        return f(*args, **kwargs)

    return decorated


def role_required(*roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                return jsonify({'error': 'Authentication required'}), 401

            if g.current_user.role.value not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403

            return f(*args, **kwargs)
        return decorated
    return decorator


def log_action(action, entity_type=None, entity_id=None, details=None):
    """Log user actions for audit trail"""
    try:
        session = g.get('session')
        if session and hasattr(g, 'current_user'):
            audit = AuditLog(
                user_id=g.current_user.id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            session.add(audit)
            session.commit()
    except Exception as e:
        print(f"Audit log error: {e}")


# ================== AUTH ENDPOINTS ==================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    session = Session()

    try:
        # Check if user exists
        if session.query(User).filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400

        if session.query(User).filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400

        # Create user
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            role=UserRole[data.get('role', 'CONTENT_CREATOR').upper()],
            phone=data.get('phone'),
            department=data.get('department')
        )

        session.add(user)
        session.commit()

        token = create_token(user.id, user.username, user.role.value)

        return jsonify({
            'message': 'User created successfully',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role.value
            }
        }), 201

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    session = Session()

    try:
        user = session.query(User).filter_by(username=data['username']).first()

        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401

        if not user.is_active:
            return jsonify({'error': 'Account is inactive'}), 403

        # Update last login
        user.last_login = datetime.utcnow()
        session.commit()

        token = create_token(user.id, user.username, user.role.value)

        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role.value,
                'avatar_url': user.avatar_url
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current user profile"""
    user = g.current_user
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': user.role.value,
        'avatar_url': user.avatar_url,
        'phone': user.phone,
        'department': user.department
    }), 200


# ================== CLIENT MANAGEMENT (CRM) ENDPOINTS ==================

@app.route('/api/clients', methods=['GET'])
@token_required
def get_clients():
    """Get all clients with filtering and pagination"""
    session = g.session

    # Query parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    status = request.args.get('status')
    search = request.args.get('search')

    query = session.query(Client)

    # Apply filters
    if status:
        query = query.filter(Client.status == ClientStatus[status.upper()])

    if search:
        query = query.filter(
            or_(
                Client.name.ilike(f'%{search}%'),
                Client.company.ilike(f'%{search}%'),
                Client.email.ilike(f'%{search}%')
            )
        )

    # Pagination
    total = query.count()
    clients = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'clients': [{
            'id': c.id,
            'name': c.name,
            'company': c.company,
            'status': c.status.value,
            'email': c.email,
            'phone': c.phone,
            'created_at': c.created_at.isoformat() if c.created_at else None
        } for c in clients],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }), 200


@app.route('/api/clients', methods=['POST'])
@token_required
def create_client():
    """Create a new client"""
    data = request.get_json()
    session = g.session

    try:
        client = Client(
            name=data['name'],
            company=data.get('company'),
            industry=data.get('industry'),
            status=ClientStatus[data.get('status', 'LEAD').upper()],
            email=data.get('email'),
            phone=data.get('phone'),
            website=data.get('website'),
            address=data.get('address'),
            city=data.get('city'),
            country=data.get('country'),
            annual_revenue=data.get('annual_revenue'),
            company_size=data.get('company_size'),
            lead_source=data.get('lead_source'),
            notes=data.get('notes'),
            custom_fields=data.get('custom_fields'),
            created_by=g.current_user.id
        )

        session.add(client)
        session.commit()

        log_action('create_client', 'client', client.id, {'name': client.name})

        return jsonify({
            'message': 'Client created successfully',
            'client': {'id': client.id, 'name': client.name}
        }), 201

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/clients/<int:client_id>', methods=['GET'])
@token_required
def get_client(client_id):
    """Get detailed client information"""
    session = g.session

    client = session.query(Client).options(
        joinedload(Client.contacts),
        joinedload(Client.campaigns),
        joinedload(Client.contracts)
    ).filter_by(id=client_id).first()

    if not client:
        return jsonify({'error': 'Client not found'}), 404

    return jsonify({
        'id': client.id,
        'name': client.name,
        'company': client.company,
        'industry': client.industry,
        'status': client.status.value,
        'email': client.email,
        'phone': client.phone,
        'website': client.website,
        'address': client.address,
        'city': client.city,
        'country': client.country,
        'annual_revenue': client.annual_revenue,
        'company_size': client.company_size,
        'lead_source': client.lead_source,
        'notes': client.notes,
        'custom_fields': client.custom_fields,
        'created_at': client.created_at.isoformat() if client.created_at else None,
        'contacts': [{
            'id': c.id,
            'first_name': c.first_name,
            'last_name': c.last_name,
            'email': c.email,
            'title': c.title,
            'is_primary': c.is_primary
        } for c in client.contacts],
        'campaigns_count': len(client.campaigns),
        'contracts_count': len(client.contracts)
    }), 200


@app.route('/api/clients/<int:client_id>', methods=['PUT'])
@token_required
def update_client(client_id):
    """Update client information"""
    data = request.get_json()
    session = g.session

    client = session.query(Client).filter_by(id=client_id).first()
    if not client:
        return jsonify({'error': 'Client not found'}), 404

    try:
        # Update fields
        for field in ['name', 'company', 'industry', 'email', 'phone', 'website',
                      'address', 'city', 'country', 'annual_revenue', 'company_size',
                      'lead_source', 'notes', 'custom_fields']:
            if field in data:
                setattr(client, field, data[field])

        if 'status' in data:
            client.status = ClientStatus[data['status'].upper()]

        client.updated_at = datetime.utcnow()
        session.commit()

        log_action('update_client', 'client', client.id, {'name': client.name})

        return jsonify({'message': 'Client updated successfully'}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/clients/<int:client_id>/contacts', methods=['POST'])
@token_required
def add_client_contact(client_id):
    """Add a contact to a client"""
    data = request.get_json()
    session = g.session

    client = session.query(Client).filter_by(id=client_id).first()
    if not client:
        return jsonify({'error': 'Client not found'}), 404

    try:
        contact = Contact(
            client_id=client_id,
            first_name=data['first_name'],
            last_name=data.get('last_name'),
            title=data.get('title'),
            email=data.get('email'),
            phone=data.get('phone'),
            is_primary=data.get('is_primary', False),
            notes=data.get('notes')
        )

        session.add(contact)
        session.commit()

        return jsonify({
            'message': 'Contact added successfully',
            'contact': {'id': contact.id, 'first_name': contact.first_name}
        }), 201

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/clients/<int:client_id>/interactions', methods=['GET'])
@token_required
def get_client_interactions(client_id):
    """Get client interaction history"""
    session = g.session

    interactions = session.query(ClientInteraction).filter_by(
        client_id=client_id
    ).order_by(ClientInteraction.interaction_date.desc()).all()

    return jsonify({
        'interactions': [{
            'id': i.id,
            'interaction_type': i.interaction_type,
            'subject': i.subject,
            'description': i.description,
            'interaction_date': i.interaction_date.isoformat() if i.interaction_date else None,
            'duration_minutes': i.duration_minutes,
            'outcome': i.outcome
        } for i in interactions]
    }), 200


@app.route('/api/clients/<int:client_id>/interactions', methods=['POST'])
@token_required
def add_client_interaction(client_id):
    """Log a new client interaction"""
    data = request.get_json()
    session = g.session

    try:
        interaction = ClientInteraction(
            client_id=client_id,
            user_id=g.current_user.id,
            interaction_type=data.get('interaction_type'),
            subject=data.get('subject'),
            description=data.get('description'),
            duration_minutes=data.get('duration_minutes'),
            outcome=data.get('outcome'),
            next_steps=data.get('next_steps')
        )

        session.add(interaction)
        session.commit()

        return jsonify({'message': 'Interaction logged successfully'}), 201

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500


# Continue in next file due to length...
# This is part 1 of the API
