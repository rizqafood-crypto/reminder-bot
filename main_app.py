"""
Enterprise Marketing Agency Management Platform - Main Application
Complete integrated platform with all modules
"""

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from functools import wraps
import jwt
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import os

from models import init_db, User, UserRole, AuditLog
from api import (
    app as base_app,
    token_required,
    role_required,
    log_action,
    Session
)

# Import module route registrars
from api_campaigns import register_campaign_routes
from api_content import register_content_routes
from api_finance import register_finance_routes
from api_tasks import register_task_routes

# ================== INITIALIZE APP ==================

app = base_app

# Register all module routes
register_campaign_routes(app, token_required, log_action)
register_content_routes(app, token_required, log_action)
register_finance_routes(app, token_required, log_action)
register_task_routes(app, token_required, log_action)


# ================== DASHBOARD & ANALYTICS ==================

@app.route('/api/dashboard/overview', methods=['GET'])
@token_required
def get_dashboard_overview():
    """Get dashboard overview with key metrics"""
    session = g.session

    from models import Client, Campaign, ContentItem, Task, Invoice
    from sqlalchemy import func

    # Clients stats
    total_clients = session.query(func.count(Client.id)).scalar()
    active_clients = session.query(func.count(Client.id)).filter(
        Client.status.in_(['active'])
    ).scalar()

    # Campaigns stats
    total_campaigns = session.query(func.count(Campaign.id)).scalar()
    active_campaigns = session.query(func.count(Campaign.id)).filter(
        Campaign.status.in_(['in_progress', 'approved'])
    ).scalar()

    # Content stats
    total_content = session.query(func.count(ContentItem.id)).scalar()
    scheduled_content = session.query(func.count(ContentItem.id)).filter(
        ContentItem.status == 'scheduled'
    ).scalar()

    # Tasks stats
    total_tasks = session.query(func.count(Task.id)).scalar()
    pending_tasks = session.query(func.count(Task.id)).filter(
        Task.status.in_(['todo', 'in_progress'])
    ).scalar()

    # Financial stats
    from models import InvoiceStatus
    total_revenue = session.query(func.sum(Invoice.paid_amount)).scalar() or 0
    pending_revenue = session.query(
        func.sum(Invoice.total_amount - Invoice.paid_amount)
    ).filter(Invoice.status != InvoiceStatus.CANCELLED).scalar() or 0

    return jsonify({
        'clients': {
            'total': total_clients,
            'active': active_clients
        },
        'campaigns': {
            'total': total_campaigns,
            'active': active_campaigns
        },
        'content': {
            'total': total_content,
            'scheduled': scheduled_content
        },
        'tasks': {
            'total': total_tasks,
            'pending': pending_tasks
        },
        'financial': {
            'total_revenue': float(total_revenue),
            'pending_revenue': float(pending_revenue)
        }
    }), 200


@app.route('/api/dashboard/activity', methods=['GET'])
@token_required
def get_recent_activity():
    """Get recent activity across the platform"""
    session = g.session

    limit = int(request.args.get('limit', 20))

    activities = session.query(AuditLog).order_by(
        AuditLog.timestamp.desc()
    ).limit(limit).all()

    return jsonify({
        'activities': [{
            'id': a.id,
            'action': a.action,
            'entity_type': a.entity_type,
            'entity_id': a.entity_id,
            'user_id': a.user_id,
            'details': a.details,
            'timestamp': a.timestamp.isoformat() if a.timestamp else None
        } for a in activities]
    }), 200


@app.route('/api/dashboard/team-performance', methods=['GET'])
@token_required
def get_team_performance():
    """Get team performance metrics"""
    session = g.session

    from models import Task, TaskStatus, TimeEntry
    from sqlalchemy import func

    # Tasks completion rate by user
    users = session.query(User).filter(User.is_active == True).all()

    team_data = []
    for user in users:
        total_tasks = session.query(func.count(Task.id)).join(
            Task.assignees
        ).filter(User.id == user.id).scalar()

        completed_tasks = session.query(func.count(Task.id)).join(
            Task.assignees
        ).filter(
            User.id == user.id,
            Task.status == TaskStatus.COMPLETED
        ).scalar()

        total_hours = session.query(func.sum(TimeEntry.hours)).filter(
            TimeEntry.user_id == user.id
        ).scalar() or 0

        team_data.append({
            'user_id': user.id,
            'name': f"{user.first_name} {user.last_name}",
            'role': user.role.value,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'total_hours': float(total_hours)
        })

    return jsonify({'team_performance': team_data}), 200


# ================== NOTIFICATIONS ==================

@app.route('/api/notifications', methods=['GET'])
@token_required
def get_notifications():
    """Get user notifications"""
    session = g.session

    from models import Notification

    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 50))

    query = session.query(Notification).filter(
        Notification.user_id == g.current_user.id
    )

    if unread_only:
        query = query.filter(Notification.is_read == False)

    notifications = query.order_by(
        Notification.created_at.desc()
    ).limit(limit).all()

    return jsonify({
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'notification_type': n.notification_type,
            'link_url': n.link_url,
            'link_text': n.link_text,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat() if n.created_at else None
        } for n in notifications]
    }), 200


@app.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
@token_required
def mark_notification_read(notification_id):
    """Mark notification as read"""
    session = g.session

    from models import Notification

    notification = session.query(Notification).filter_by(
        id=notification_id,
        user_id=g.current_user.id
    ).first()

    if not notification:
        return jsonify({'error': 'Notification not found'}), 404

    try:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        session.commit()

        return jsonify({'message': 'Notification marked as read'}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500


# ================== USERS & TEAM MANAGEMENT ==================

@app.route('/api/users', methods=['GET'])
@token_required
def get_users():
    """Get all users"""
    session = g.session

    role = request.args.get('role')
    active_only = request.args.get('active_only', 'true').lower() == 'true'

    query = session.query(User)

    if role:
        query = query.filter(User.role == UserRole[role.upper()])

    if active_only:
        query = query.filter(User.is_active == True)

    users = query.all()

    return jsonify({
        'users': [{
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'role': u.role.value,
            'department': u.department,
            'avatar_url': u.avatar_url,
            'is_active': u.is_active
        } for u in users]
    }), 200


@app.route('/api/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(user_id):
    """Get user profile"""
    session = g.session

    user = session.query(User).filter_by(id=user_id).first()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': user.role.value,
        'department': user.department,
        'phone': user.phone,
        'avatar_url': user.avatar_url,
        'is_active': user.is_active,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'created_at': user.created_at.isoformat() if user.created_at else None
    }), 200


@app.route('/api/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user(user_id):
    """Update user profile"""
    data = request.get_json()
    session = g.session

    # Only allow users to update themselves unless admin
    if user_id != g.current_user.id and g.current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Insufficient permissions'}), 403

    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    try:
        for field in ['first_name', 'last_name', 'phone', 'department', 'avatar_url']:
            if field in data:
                setattr(user, field, data[field])

        # Only admin can change role and active status
        if g.current_user.role == UserRole.ADMIN:
            if 'role' in data:
                user.role = UserRole[data['role'].upper()]
            if 'is_active' in data:
                user.is_active = data['is_active']

        user.updated_at = datetime.utcnow()
        session.commit()

        log_action('update_user', 'user', user.id)

        return jsonify({'message': 'User updated successfully'}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500


# ================== WORKFLOWS & AUTOMATION ==================

@app.route('/api/workflows', methods=['GET'])
@token_required
def get_workflows():
    """Get all workflows"""
    session = g.session

    from models import Workflow

    workflows = session.query(Workflow).all()

    return jsonify({
        'workflows': [{
            'id': w.id,
            'name': w.name,
            'description': w.description,
            'trigger_type': w.trigger_type,
            'is_active': w.is_active,
            'run_count': w.run_count,
            'last_run': w.last_run.isoformat() if w.last_run else None
        } for w in workflows]
    }), 200


@app.route('/api/workflows', methods=['POST'])
@token_required
@role_required('admin', 'manager')
def create_workflow():
    """Create a new workflow"""
    data = request.get_json()
    session = g.session

    from models import Workflow

    try:
        workflow = Workflow(
            name=data['name'],
            description=data.get('description'),
            trigger_type=data['trigger_type'],
            trigger_config=data.get('trigger_config', {}),
            actions=data.get('actions', []),
            conditions=data.get('conditions', {}),
            is_active=data.get('is_active', True)
        )

        session.add(workflow)
        session.commit()

        log_action('create_workflow', 'workflow', workflow.id, {'name': workflow.name})

        return jsonify({
            'message': 'Workflow created successfully',
            'workflow': {'id': workflow.id, 'name': workflow.name}
        }), 201

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500


# ================== INTEGRATIONS ==================

@app.route('/api/integrations', methods=['GET'])
@token_required
def get_integrations():
    """Get all integrations"""
    session = g.session

    from models import Integration

    integrations = session.query(Integration).all()

    return jsonify({
        'integrations': [{
            'id': i.id,
            'name': i.name,
            'platform': i.platform,
            'description': i.description,
            'is_active': i.is_active,
            'last_sync': i.last_sync.isoformat() if i.last_sync else None,
            'sync_status': i.sync_status
        } for i in integrations]
    }), 200


@app.route('/api/integrations', methods=['POST'])
@token_required
@role_required('admin', 'manager')
def create_integration():
    """Create a new integration"""
    data = request.get_json()
    session = g.session

    from models import Integration

    try:
        integration = Integration(
            name=data['name'],
            platform=data['platform'],
            description=data.get('description'),
            config=data.get('config', {}),
            credentials=data.get('credentials', {}),
            is_active=data.get('is_active', True)
        )

        session.add(integration)
        session.commit()

        log_action('create_integration', 'integration', integration.id, {'name': integration.name})

        return jsonify({
            'message': 'Integration created successfully',
            'integration': {'id': integration.id, 'name': integration.name}
        }), 201

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500


# ================== SEARCH ==================

@app.route('/api/search', methods=['GET'])
@token_required
def global_search():
    """Global search across all entities"""
    session = g.session
    query_string = request.args.get('q', '')

    if len(query_string) < 2:
        return jsonify({'error': 'Query too short'}), 400

    from models import Client, Campaign, ContentItem, Task
    from sqlalchemy import or_

    results = {
        'clients': [],
        'campaigns': [],
        'content': [],
        'tasks': []
    }

    # Search clients
    clients = session.query(Client).filter(
        or_(
            Client.name.ilike(f'%{query_string}%'),
            Client.company.ilike(f'%{query_string}%')
        )
    ).limit(10).all()

    results['clients'] = [{
        'id': c.id,
        'name': c.name,
        'type': 'client'
    } for c in clients]

    # Search campaigns
    campaigns = session.query(Campaign).filter(
        or_(
            Campaign.name.ilike(f'%{query_string}%'),
            Campaign.description.ilike(f'%{query_string}%')
        )
    ).limit(10).all()

    results['campaigns'] = [{
        'id': c.id,
        'name': c.name,
        'type': 'campaign'
    } for c in campaigns]

    # Search content
    content_items = session.query(ContentItem).filter(
        or_(
            ContentItem.title.ilike(f'%{query_string}%'),
            ContentItem.description.ilike(f'%{query_string}%')
        )
    ).limit(10).all()

    results['content'] = [{
        'id': c.id,
        'title': c.title,
        'type': 'content'
    } for c in content_items]

    # Search tasks
    tasks = session.query(Task).filter(
        or_(
            Task.title.ilike(f'%{query_string}%'),
            Task.description.ilike(f'%{query_string}%')
        )
    ).limit(10).all()

    results['tasks'] = [{
        'id': t.id,
        'title': t.title,
        'type': 'task'
    } for t in tasks]

    return jsonify(results), 200


# ================== HEALTH CHECK ==================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200


@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'message': 'Enterprise Marketing Agency Management Platform API',
        'version': '1.0.0',
        'docs': '/api/docs'
    }), 200


# ================== ERROR HANDLERS ==================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ================== MAIN ==================

if __name__ == '__main__':
    # Initialize database
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")

    # Run the application
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'

    print(f"\n{'='*60}")
    print("Enterprise Marketing Agency Management Platform")
    print(f"{'='*60}")
    print(f"Server running on http://0.0.0.0:{port}")
    print(f"Debug mode: {debug}")
    print(f"{'='*60}\n")

    app.run(host='0.0.0.0', port=port, debug=debug)
