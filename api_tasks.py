"""
Task Management API Endpoints
"""

from flask import request, jsonify, g
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from models import Task, TaskStatus, TaskPriority, User, Comment


def register_task_routes(app, token_required, log_action):
    """Register task management routes"""

    @app.route('/api/tasks', methods=['GET'])
    @token_required
    def get_tasks():
        """Get all tasks with filtering"""
        session = g.session

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        campaign_id = request.args.get('campaign_id')
        assignee_id = request.args.get('assignee_id')
        status = request.args.get('status')
        priority = request.args.get('priority')

        query = session.query(Task).options(joinedload(Task.assignees))

        if campaign_id:
            query = query.filter(Task.campaign_id == campaign_id)

        if status:
            query = query.filter(Task.status == TaskStatus[status.upper()])

        if priority:
            query = query.filter(Task.priority == TaskPriority[priority.upper()])

        if assignee_id:
            query = query.join(Task.assignees).filter(User.id == assignee_id)

        total = query.count()
        tasks = query.order_by(
            Task.due_date.asc().nullslast()
        ).offset((page - 1) * per_page).limit(per_page).all()

        return jsonify({
            'tasks': [{
                'id': t.id,
                'title': t.title,
                'status': t.status.value,
                'priority': t.priority.value,
                'due_date': t.due_date.isoformat() if t.due_date else None,
                'campaign_id': t.campaign_id,
                'assignees': [{
                    'id': u.id,
                    'first_name': u.first_name,
                    'last_name': u.last_name
                } for u in t.assignees],
                'estimated_hours': t.estimated_hours,
                'actual_hours': t.actual_hours
            } for t in tasks],
            'total': total,
            'page': page,
            'per_page': per_page
        }), 200

    @app.route('/api/tasks', methods=['POST'])
    @token_required
    def create_task():
        """Create a new task"""
        data = request.get_json()
        session = g.session

        try:
            task = Task(
                campaign_id=data.get('campaign_id'),
                client_id=data.get('client_id'),
                content_item_id=data.get('content_item_id'),
                title=data['title'],
                description=data.get('description'),
                status=TaskStatus[data.get('status', 'TODO').upper()],
                priority=TaskPriority[data.get('priority', 'MEDIUM').upper()],
                created_by=g.current_user.id,
                due_date=datetime.fromisoformat(data['due_date']) if 'due_date' in data else None,
                start_date=datetime.fromisoformat(data['start_date']) if 'start_date' in data else None,
                estimated_hours=data.get('estimated_hours'),
                parent_task_id=data.get('parent_task_id'),
                tags=data.get('tags', []),
                custom_fields=data.get('custom_fields')
            )

            session.add(task)
            session.flush()

            # Assign users
            if 'assignee_ids' in data:
                for user_id in data['assignee_ids']:
                    user = session.query(User).filter_by(id=user_id).first()
                    if user:
                        task.assignees.append(user)

            session.commit()

            log_action('create_task', 'task', task.id, {'title': task.title})

            return jsonify({
                'message': 'Task created successfully',
                'task': {'id': task.id, 'title': task.title}
            }), 201

        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/tasks/<int:task_id>', methods=['GET'])
    @token_required
    def get_task(task_id):
        """Get detailed task information"""
        session = g.session

        task = session.query(Task).options(
            joinedload(Task.assignees),
            joinedload(Task.campaign),
            joinedload(Task.comments),
            joinedload(Task.subtasks),
            joinedload(Task.time_entries)
        ).filter_by(id=task_id).first()

        if not task:
            return jsonify({'error': 'Task not found'}), 404

        return jsonify({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status.value,
            'priority': task.priority.value,
            'campaign': {
                'id': task.campaign.id,
                'name': task.campaign.name
            } if task.campaign else None,
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'start_date': task.start_date.isoformat() if task.start_date else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'estimated_hours': task.estimated_hours,
            'actual_hours': task.actual_hours,
            'assignees': [{
                'id': u.id,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'email': u.email,
                'avatar_url': u.avatar_url
            } for u in task.assignees],
            'subtasks': [{
                'id': st.id,
                'title': st.title,
                'status': st.status.value
            } for st in task.subtasks],
            'comments_count': len(task.comments),
            'time_logged': sum([te.hours for te in task.time_entries]),
            'tags': task.tags,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'updated_at': task.updated_at.isoformat() if task.updated_at else None
        }), 200

    @app.route('/api/tasks/<int:task_id>', methods=['PUT'])
    @token_required
    def update_task(task_id):
        """Update task"""
        data = request.get_json()
        session = g.session

        task = session.query(Task).filter_by(id=task_id).first()
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        try:
            for field in ['title', 'description', 'estimated_hours', 'actual_hours',
                         'tags', 'custom_fields']:
                if field in data:
                    setattr(task, field, data[field])

            if 'status' in data:
                task.status = TaskStatus[data['status'].upper()]
                if task.status == TaskStatus.COMPLETED and not task.completed_at:
                    task.completed_at = datetime.utcnow()

            if 'priority' in data:
                task.priority = TaskPriority[data['priority'].upper()]

            if 'due_date' in data:
                task.due_date = datetime.fromisoformat(data['due_date']) if data['due_date'] else None

            if 'start_date' in data:
                task.start_date = datetime.fromisoformat(data['start_date']) if data['start_date'] else None

            # Update assignees
            if 'assignee_ids' in data:
                task.assignees.clear()
                for user_id in data['assignee_ids']:
                    user = session.query(User).filter_by(id=user_id).first()
                    if user:
                        task.assignees.append(user)

            task.updated_at = datetime.utcnow()
            session.commit()

            log_action('update_task', 'task', task.id)

            return jsonify({'message': 'Task updated successfully'}), 200

        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/tasks/<int:task_id>/comments', methods=['GET'])
    @token_required
    def get_task_comments(task_id):
        """Get comments for task"""
        session = g.session

        comments = session.query(Comment).filter_by(
            task_id=task_id
        ).order_by(Comment.created_at.desc()).all()

        return jsonify({
            'comments': [{
                'id': c.id,
                'text': c.text,
                'user': {
                    'id': c.user.id,
                    'first_name': c.user.first_name,
                    'last_name': c.user.last_name,
                    'avatar_url': c.user.avatar_url
                } if c.user else None,
                'created_at': c.created_at.isoformat() if c.created_at else None
            } for c in comments]
        }), 200

    @app.route('/api/tasks/<int:task_id>/comments', methods=['POST'])
    @token_required
    def add_task_comment(task_id):
        """Add a comment to task"""
        data = request.get_json()
        session = g.session

        try:
            comment = Comment(
                task_id=task_id,
                user_id=g.current_user.id,
                text=data['text'],
                parent_comment_id=data.get('parent_comment_id'),
                attachments=data.get('attachments', [])
            )

            session.add(comment)
            session.commit()

            return jsonify({
                'message': 'Comment added successfully',
                'comment': {'id': comment.id}
            }), 201

        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/tasks/board', methods=['GET'])
    @token_required
    def get_task_board():
        """Get task board (Kanban view)"""
        session = g.session

        campaign_id = request.args.get('campaign_id')

        query = session.query(Task).options(joinedload(Task.assignees))

        if campaign_id:
            query = query.filter(Task.campaign_id == campaign_id)

        tasks = query.all()

        # Group by status
        board = {
            'todo': [],
            'in_progress': [],
            'review': [],
            'completed': []
        }

        for task in tasks:
            task_data = {
                'id': task.id,
                'title': task.title,
                'priority': task.priority.value,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'assignees': [{
                    'id': u.id,
                    'first_name': u.first_name,
                    'avatar_url': u.avatar_url
                } for u in task.assignees]
            }

            if task.status == TaskStatus.TODO:
                board['todo'].append(task_data)
            elif task.status == TaskStatus.IN_PROGRESS:
                board['in_progress'].append(task_data)
            elif task.status == TaskStatus.REVIEW:
                board['review'].append(task_data)
            elif task.status == TaskStatus.COMPLETED:
                board['completed'].append(task_data)

        return jsonify(board), 200

    @app.route('/api/tasks/my-tasks', methods=['GET'])
    @token_required
    def get_my_tasks():
        """Get tasks assigned to current user"""
        session = g.session

        tasks = session.query(Task).join(
            Task.assignees
        ).filter(
            User.id == g.current_user.id,
            Task.status != TaskStatus.COMPLETED
        ).order_by(Task.due_date.asc().nullslast()).all()

        return jsonify({
            'tasks': [{
                'id': t.id,
                'title': t.title,
                'status': t.status.value,
                'priority': t.priority.value,
                'due_date': t.due_date.isoformat() if t.due_date else None,
                'campaign_id': t.campaign_id
            } for t in tasks]
        }), 200
