"""
Campaign Management API Endpoints
"""

from flask import request, jsonify, g
from datetime import datetime
from sqlalchemy.orm import joinedload
from models import Campaign, CampaignStatus, CampaignAnalytics, Task


def register_campaign_routes(app, token_required, log_action):
    """Register campaign management routes"""

    @app.route('/api/campaigns', methods=['GET'])
    @token_required
    def get_campaigns():
        """Get all campaigns with filtering"""
        session = g.session

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        client_id = request.args.get('client_id')
        status = request.args.get('status')

        query = session.query(Campaign).options(joinedload(Campaign.client))

        if client_id:
            query = query.filter(Campaign.client_id == client_id)

        if status:
            query = query.filter(Campaign.status == CampaignStatus[status.upper()])

        total = query.count()
        campaigns = query.offset((page - 1) * per_page).limit(per_page).all()

        return jsonify({
            'campaigns': [{
                'id': c.id,
                'name': c.name,
                'client_name': c.client.name if c.client else None,
                'status': c.status.value,
                'campaign_type': c.campaign_type,
                'budget': c.budget,
                'actual_spend': c.actual_spend,
                'start_date': c.start_date.isoformat() if c.start_date else None,
                'end_date': c.end_date.isoformat() if c.end_date else None
            } for c in campaigns],
            'total': total,
            'page': page,
            'per_page': per_page
        }), 200

    @app.route('/api/campaigns', methods=['POST'])
    @token_required
    def create_campaign():
        """Create a new campaign"""
        data = request.get_json()
        session = g.session

        try:
            campaign = Campaign(
                client_id=data['client_id'],
                name=data['name'],
                description=data.get('description'),
                status=CampaignStatus[data.get('status', 'PLANNING').upper()],
                campaign_type=data.get('campaign_type'),
                objectives=data.get('objectives'),
                target_audience=data.get('target_audience'),
                channels=data.get('channels', []),
                start_date=datetime.fromisoformat(data['start_date']) if 'start_date' in data else None,
                end_date=datetime.fromisoformat(data['end_date']) if 'end_date' in data else None,
                budget=data.get('budget'),
                goals=data.get('goals', {}),
                kpis=data.get('kpis', {}),
                tags=data.get('tags', []),
                custom_fields=data.get('custom_fields')
            )

            session.add(campaign)
            session.commit()

            log_action('create_campaign', 'campaign', campaign.id, {'name': campaign.name})

            return jsonify({
                'message': 'Campaign created successfully',
                'campaign': {'id': campaign.id, 'name': campaign.name}
            }), 201

        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/campaigns/<int:campaign_id>', methods=['GET'])
    @token_required
    def get_campaign(campaign_id):
        """Get detailed campaign information"""
        session = g.session

        campaign = session.query(Campaign).options(
            joinedload(Campaign.client),
            joinedload(Campaign.team_members),
            joinedload(Campaign.content_items),
            joinedload(Campaign.tasks)
        ).filter_by(id=campaign_id).first()

        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404

        return jsonify({
            'id': campaign.id,
            'name': campaign.name,
            'description': campaign.description,
            'client': {
                'id': campaign.client.id,
                'name': campaign.client.name
            } if campaign.client else None,
            'status': campaign.status.value,
            'campaign_type': campaign.campaign_type,
            'objectives': campaign.objectives,
            'target_audience': campaign.target_audience,
            'channels': campaign.channels,
            'start_date': campaign.start_date.isoformat() if campaign.start_date else None,
            'end_date': campaign.end_date.isoformat() if campaign.end_date else None,
            'budget': campaign.budget,
            'actual_spend': campaign.actual_spend,
            'goals': campaign.goals,
            'kpis': campaign.kpis,
            'tags': campaign.tags,
            'team_members': [{
                'id': u.id,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'role': u.role.value
            } for u in campaign.team_members],
            'content_items_count': len(campaign.content_items),
            'tasks_count': len(campaign.tasks),
            'created_at': campaign.created_at.isoformat() if campaign.created_at else None
        }), 200

    @app.route('/api/campaigns/<int:campaign_id>', methods=['PUT'])
    @token_required
    def update_campaign(campaign_id):
        """Update campaign information"""
        data = request.get_json()
        session = g.session

        campaign = session.query(Campaign).filter_by(id=campaign_id).first()
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404

        try:
            for field in ['name', 'description', 'campaign_type', 'objectives',
                         'target_audience', 'channels', 'budget', 'actual_spend',
                         'goals', 'kpis', 'tags', 'custom_fields']:
                if field in data:
                    setattr(campaign, field, data[field])

            if 'status' in data:
                campaign.status = CampaignStatus[data['status'].upper()]

            if 'start_date' in data:
                campaign.start_date = datetime.fromisoformat(data['start_date'])

            if 'end_date' in data:
                campaign.end_date = datetime.fromisoformat(data['end_date'])

            campaign.updated_at = datetime.utcnow()
            session.commit()

            log_action('update_campaign', 'campaign', campaign.id)

            return jsonify({'message': 'Campaign updated successfully'}), 200

        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/campaigns/<int:campaign_id>/team', methods=['POST'])
    @token_required
    def add_campaign_team_member(campaign_id):
        """Add a team member to campaign"""
        data = request.get_json()
        session = g.session

        from models import User
        campaign = session.query(Campaign).filter_by(id=campaign_id).first()
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404

        user = session.query(User).filter_by(id=data['user_id']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        try:
            if user not in campaign.team_members:
                campaign.team_members.append(user)
                session.commit()

            return jsonify({'message': 'Team member added successfully'}), 200

        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/campaigns/<int:campaign_id>/analytics', methods=['GET'])
    @token_required
    def get_campaign_analytics(campaign_id):
        """Get campaign analytics and performance metrics"""
        session = g.session

        analytics = session.query(CampaignAnalytics).filter_by(
            campaign_id=campaign_id
        ).order_by(CampaignAnalytics.date.desc()).limit(30).all()

        return jsonify({
            'analytics': [{
                'date': a.date.isoformat() if a.date else None,
                'impressions': a.impressions,
                'reach': a.reach,
                'engagement': a.engagement,
                'clicks': a.clicks,
                'conversions': a.conversions,
                'ctr': a.ctr,
                'conversion_rate': a.conversion_rate,
                'engagement_rate': a.engagement_rate,
                'spend': a.spend,
                'revenue': a.revenue,
                'roi': a.roi
            } for a in analytics]
        }), 200

    @app.route('/api/campaigns/<int:campaign_id>/analytics', methods=['POST'])
    @token_required
    def add_campaign_analytics(campaign_id):
        """Add analytics data for a campaign"""
        data = request.get_json()
        session = g.session

        try:
            analytics = CampaignAnalytics(
                campaign_id=campaign_id,
                date=datetime.fromisoformat(data.get('date', datetime.utcnow().isoformat())),
                impressions=data.get('impressions', 0),
                reach=data.get('reach', 0),
                engagement=data.get('engagement', 0),
                clicks=data.get('clicks', 0),
                conversions=data.get('conversions', 0),
                ctr=data.get('ctr', 0.0),
                conversion_rate=data.get('conversion_rate', 0.0),
                engagement_rate=data.get('engagement_rate', 0.0),
                spend=data.get('spend', 0.0),
                revenue=data.get('revenue', 0.0),
                roi=data.get('roi', 0.0),
                platform_metrics=data.get('platform_metrics', {})
            )

            session.add(analytics)
            session.commit()

            return jsonify({'message': 'Analytics data added successfully'}), 201

        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
