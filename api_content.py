"""
Content Workflow Management API Endpoints
"""

from flask import request, jsonify, g
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from models import ContentItem, ContentStatus, TaskPriority, Tag, Approval, Comment


def register_content_routes(app, token_required, log_action):
    """Register content workflow routes"""

    @app.route('/api/content', methods=['GET'])
    @token_required
    def get_content_items():
        """Get all content items with filtering"""
        session = g.session

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        campaign_id = request.args.get('campaign_id')
        status = request.args.get('status')
        content_type = request.args.get('content_type')
        platform = request.args.get('platform')

        query = session.query(ContentItem)

        if campaign_id:
            query = query.filter(ContentItem.campaign_id == campaign_id)

        if status:
            query = query.filter(ContentItem.status == ContentStatus[status.upper()])

        if content_type:
            query = query.filter(ContentItem.content_type == content_type)

        if platform:
            query = query.filter(ContentItem.platform == platform)

        total = query.count()
        content_items = query.order_by(
            ContentItem.scheduled_date.desc()
        ).offset((page - 1) * per_page).limit(per_page).all()

        return jsonify({
            'content_items': [{
                'id': c.id,
                'title': c.title,
                'content_type': c.content_type,
                'platform': c.platform,
                'status': c.status.value,
                'priority': c.priority.value,
                'scheduled_date': c.scheduled_date.isoformat() if c.scheduled_date else None,
                'published_date': c.published_date.isoformat() if c.published_date else None,
                'campaign_id': c.campaign_id
            } for c in content_items],
            'total': total,
            'page': page,
            'per_page': per_page
        }), 200

    @app.route('/api/content', methods=['POST'])
    @token_required
    def create_content_item():
        """Create a new content item"""
        data = request.get_json()
        session = g.session

        try:
            content = ContentItem(
                campaign_id=data.get('campaign_id'),
                client_id=data.get('client_id'),
                title=data['title'],
                content_type=data.get('content_type'),
                platform=data.get('platform'),
                description=data.get('description'),
                content_body=data.get('content_body'),
                status=ContentStatus[data.get('status', 'IDEA').upper()],
                priority=TaskPriority[data.get('priority', 'MEDIUM').upper()],
                creator_id=g.current_user.id,
                scheduled_date=datetime.fromisoformat(data['scheduled_date']) if 'scheduled_date' in data else None,
                assets=data.get('assets', []),
                hashtags=data.get('hashtags', []),
                mentions=data.get('mentions', []),
                custom_fields=data.get('custom_fields')
            )

            session.add(content)
            session.commit()

            log_action('create_content', 'content', content.id, {'title': content.title})

            return jsonify({
                'message': 'Content item created successfully',
                'content': {'id': content.id, 'title': content.title}
            }), 201

        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/content/<int:content_id>', methods=['GET'])
    @token_required
    def get_content_item(content_id):
        """Get detailed content item information"""
        session = g.session

        content = session.query(ContentItem).options(
            joinedload(ContentItem.campaign),
            joinedload(ContentItem.comments),
            joinedload(ContentItem.approvals)
        ).filter_by(id=content_id).first()

        if not content:
            return jsonify({'error': 'Content item not found'}), 404

        return jsonify({
            'id': content.id,
            'title': content.title,
            'content_type': content.content_type,
            'platform': content.platform,
            'description': content.description,
            'content_body': content.content_body,
            'status': content.status.value,
            'priority': content.priority.value,
            'campaign': {
                'id': content.campaign.id,
                'name': content.campaign.name
            } if content.campaign else None,
            'scheduled_date': content.scheduled_date.isoformat() if content.scheduled_date else None,
            'published_date': content.published_date.isoformat() if content.published_date else None,
            'assets': content.assets,
            'hashtags': content.hashtags,
            'mentions': content.mentions,
            'performance_metrics': content.performance_metrics,
            'comments_count': len(content.comments),
            'approvals': [{
                'id': a.id,
                'status': a.status,
                'feedback': a.feedback,
                'approved_at': a.approved_at.isoformat() if a.approved_at else None
            } for a in content.approvals],
            'created_at': content.created_at.isoformat() if content.created_at else None,
            'updated_at': content.updated_at.isoformat() if content.updated_at else None
        }), 200

    @app.route('/api/content/<int:content_id>', methods=['PUT'])
    @token_required
    def update_content_item(content_id):
        """Update content item"""
        data = request.get_json()
        session = g.session

        content = session.query(ContentItem).filter_by(id=content_id).first()
        if not content:
            return jsonify({'error': 'Content item not found'}), 404

        try:
            for field in ['title', 'content_type', 'platform', 'description',
                         'content_body', 'assets', 'hashtags', 'mentions',
                         'performance_metrics', 'custom_fields']:
                if field in data:
                    setattr(content, field, data[field])

            if 'status' in data:
                content.status = ContentStatus[data['status'].upper()]
                if content.status == ContentStatus.PUBLISHED and not content.published_date:
                    content.published_date = datetime.utcnow()

            if 'priority' in data:
                content.priority = TaskPriority[data['priority'].upper()]

            if 'scheduled_date' in data:
                content.scheduled_date = datetime.fromisoformat(data['scheduled_date'])

            content.updated_at = datetime.utcnow()
            session.commit()

            log_action('update_content', 'content', content.id)

            return jsonify({'message': 'Content item updated successfully'}), 200

        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/content/<int:content_id>/approve', methods=['POST'])
    @token_required
    def approve_content(content_id):
        """Approve or reject content"""
        data = request.get_json()
        session = g.session

        content = session.query(ContentItem).filter_by(id=content_id).first()
        if not content:
            return jsonify({'error': 'Content item not found'}), 404

        try:
            approval = Approval(
                content_item_id=content_id,
                reviewer_id=g.current_user.id,
                status=data.get('status', 'approved'),
                feedback=data.get('feedback')
            )

            if data.get('status') == 'approved':
                approval.approved_at = datetime.utcnow()
                content.status = ContentStatus.APPROVED

            session.add(approval)
            session.commit()

            log_action('approve_content', 'content', content_id, {'status': data.get('status')})

            return jsonify({'message': 'Content approval recorded'}), 201

        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/content/<int:content_id>/comments', methods=['GET'])
    @token_required
    def get_content_comments(content_id):
        """Get comments for content item"""
        session = g.session

        comments = session.query(Comment).filter_by(
            content_item_id=content_id
        ).order_by(Comment.created_at.desc()).all()

        return jsonify({
            'comments': [{
                'id': c.id,
                'text': c.text,
                'user': {
                    'id': c.user.id,
                    'first_name': c.user.first_name,
                    'last_name': c.user.last_name
                } if c.user else None,
                'created_at': c.created_at.isoformat() if c.created_at else None
            } for c in comments]
        }), 200

    @app.route('/api/content/<int:content_id>/comments', methods=['POST'])
    @token_required
    def add_content_comment(content_id):
        """Add a comment to content item"""
        data = request.get_json()
        session = g.session

        try:
            comment = Comment(
                content_item_id=content_id,
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

    @app.route('/api/content/calendar', methods=['GET'])
    @token_required
    def get_content_calendar():
        """Get content calendar view"""
        session = g.session

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = session.query(ContentItem).filter(
            ContentItem.scheduled_date.isnot(None)
        )

        if start_date:
            query = query.filter(ContentItem.scheduled_date >= datetime.fromisoformat(start_date))

        if end_date:
            query = query.filter(ContentItem.scheduled_date <= datetime.fromisoformat(end_date))

        content_items = query.order_by(ContentItem.scheduled_date).all()

        return jsonify({
            'calendar': [{
                'id': c.id,
                'title': c.title,
                'content_type': c.content_type,
                'platform': c.platform,
                'status': c.status.value,
                'scheduled_date': c.scheduled_date.isoformat() if c.scheduled_date else None,
                'campaign_id': c.campaign_id
            } for c in content_items]
        }), 200

    @app.route('/api/tags', methods=['GET'])
    @token_required
    def get_tags():
        """Get all tags"""
        session = g.session
        tags = session.query(Tag).all()

        return jsonify({
            'tags': [{
                'id': t.id,
                'name': t.name,
                'category': t.category,
                'color': t.color
            } for t in tags]
        }), 200

    @app.route('/api/tags', methods=['POST'])
    @token_required
    def create_tag():
        """Create a new tag"""
        data = request.get_json()
        session = g.session

        try:
            tag = Tag(
                name=data['name'],
                category=data.get('category'),
                color=data.get('color')
            )

            session.add(tag)
            session.commit()

            return jsonify({
                'message': 'Tag created successfully',
                'tag': {'id': tag.id, 'name': tag.name}
            }), 201

        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
