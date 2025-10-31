"""
Finance Management API Endpoints
"""

from flask import request, jsonify, g
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from models import (
    Invoice, InvoiceLineItem, Payment, Expense, TimeEntry,
    InvoiceStatus, PaymentStatus
)


def register_finance_routes(app, token_required, log_action):
    """Register finance management routes"""

    # ================== INVOICES ==================

    @app.route('/api/invoices', methods=['GET'])
    @token_required
    def get_invoices():
        """Get all invoices with filtering"""
        session = g.session

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        client_id = request.args.get('client_id')
        status = request.args.get('status')

        query = session.query(Invoice).options(joinedload(Invoice.client))

        if client_id:
            query = query.filter(Invoice.client_id == client_id)

        if status:
            query = query.filter(Invoice.status == InvoiceStatus[status.upper()])

        total = query.count()
        invoices = query.order_by(
            Invoice.created_at.desc()
        ).offset((page - 1) * per_page).limit(per_page).all()

        return jsonify({
            'invoices': [{
                'id': i.id,
                'invoice_number': i.invoice_number,
                'client_name': i.client.name if i.client else None,
                'status': i.status.value,
                'total_amount': i.total_amount,
                'paid_amount': i.paid_amount,
                'issue_date': i.issue_date.isoformat() if i.issue_date else None,
                'due_date': i.due_date.isoformat() if i.due_date else None
            } for i in invoices],
            'total': total,
            'page': page,
            'per_page': per_page
        }), 200

    @app.route('/api/invoices', methods=['POST'])
    @token_required
    def create_invoice():
        """Create a new invoice"""
        data = request.get_json()
        session = g.session

        try:
            invoice = Invoice(
                client_id=data['client_id'],
                campaign_id=data.get('campaign_id'),
                invoice_number=data['invoice_number'],
                title=data.get('title'),
                description=data.get('description'),
                status=InvoiceStatus[data.get('status', 'DRAFT').upper()],
                subtotal=data.get('subtotal', 0.0),
                tax_rate=data.get('tax_rate', 0.0),
                tax_amount=data.get('tax_amount', 0.0),
                discount_amount=data.get('discount_amount', 0.0),
                total_amount=data['total_amount'],
                issue_date=datetime.fromisoformat(data.get('issue_date', datetime.utcnow().isoformat())),
                due_date=datetime.fromisoformat(data['due_date']) if 'due_date' in data else None,
                notes=data.get('notes'),
                terms=data.get('terms'),
                currency=data.get('currency', 'USD')
            )

            session.add(invoice)
            session.flush()

            # Add line items
            for item_data in data.get('line_items', []):
                line_item = InvoiceLineItem(
                    invoice_id=invoice.id,
                    description=item_data['description'],
                    quantity=item_data.get('quantity', 1.0),
                    unit_price=item_data['unit_price'],
                    amount=item_data['amount'],
                    tax_rate=item_data.get('tax_rate', 0.0)
                )
                session.add(line_item)

            session.commit()

            log_action('create_invoice', 'invoice', invoice.id, {'invoice_number': invoice.invoice_number})

            return jsonify({
                'message': 'Invoice created successfully',
                'invoice': {
                    'id': invoice.id,
                    'invoice_number': invoice.invoice_number
                }
            }), 201

        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/invoices/<int:invoice_id>', methods=['GET'])
    @token_required
    def get_invoice(invoice_id):
        """Get detailed invoice information"""
        session = g.session

        invoice = session.query(Invoice).options(
            joinedload(Invoice.client),
            joinedload(Invoice.line_items),
            joinedload(Invoice.payments)
        ).filter_by(id=invoice_id).first()

        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404

        return jsonify({
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'client': {
                'id': invoice.client.id,
                'name': invoice.client.name,
                'email': invoice.client.email
            } if invoice.client else None,
            'title': invoice.title,
            'description': invoice.description,
            'status': invoice.status.value,
            'subtotal': invoice.subtotal,
            'tax_rate': invoice.tax_rate,
            'tax_amount': invoice.tax_amount,
            'discount_amount': invoice.discount_amount,
            'total_amount': invoice.total_amount,
            'paid_amount': invoice.paid_amount,
            'issue_date': invoice.issue_date.isoformat() if invoice.issue_date else None,
            'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
            'paid_date': invoice.paid_date.isoformat() if invoice.paid_date else None,
            'notes': invoice.notes,
            'terms': invoice.terms,
            'currency': invoice.currency,
            'line_items': [{
                'id': li.id,
                'description': li.description,
                'quantity': li.quantity,
                'unit_price': li.unit_price,
                'amount': li.amount,
                'tax_rate': li.tax_rate
            } for li in invoice.line_items],
            'payments': [{
                'id': p.id,
                'amount': p.amount,
                'payment_method': p.payment_method,
                'status': p.status.value,
                'payment_date': p.payment_date.isoformat() if p.payment_date else None
            } for p in invoice.payments]
        }), 200

    @app.route('/api/invoices/<int:invoice_id>', methods=['PUT'])
    @token_required
    def update_invoice(invoice_id):
        """Update invoice"""
        data = request.get_json()
        session = g.session

        invoice = session.query(Invoice).filter_by(id=invoice_id).first()
        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404

        try:
            for field in ['title', 'description', 'subtotal', 'tax_rate',
                         'tax_amount', 'discount_amount', 'total_amount',
                         'notes', 'terms']:
                if field in data:
                    setattr(invoice, field, data[field])

            if 'status' in data:
                invoice.status = InvoiceStatus[data['status'].upper()]

            if 'due_date' in data:
                invoice.due_date = datetime.fromisoformat(data['due_date'])

            invoice.updated_at = datetime.utcnow()
            session.commit()

            log_action('update_invoice', 'invoice', invoice.id)

            return jsonify({'message': 'Invoice updated successfully'}), 200

        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500

    # ================== PAYMENTS ==================

    @app.route('/api/payments', methods=['POST'])
    @token_required
    def create_payment():
        """Record a payment"""
        data = request.get_json()
        session = g.session

        invoice = session.query(Invoice).filter_by(id=data['invoice_id']).first()
        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404

        try:
            payment = Payment(
                invoice_id=data['invoice_id'],
                amount=data['amount'],
                payment_method=data.get('payment_method'),
                status=PaymentStatus[data.get('status', 'COMPLETED').upper()],
                transaction_id=data.get('transaction_id'),
                payment_date=datetime.fromisoformat(data.get('payment_date', datetime.utcnow().isoformat())),
                notes=data.get('notes')
            )

            session.add(payment)

            # Update invoice
            invoice.paid_amount += payment.amount
            if invoice.paid_amount >= invoice.total_amount:
                invoice.status = InvoiceStatus.PAID
                invoice.paid_date = payment.payment_date

            session.commit()

            log_action('create_payment', 'payment', payment.id, {
                'invoice_id': invoice.id,
                'amount': payment.amount
            })

            return jsonify({
                'message': 'Payment recorded successfully',
                'payment': {'id': payment.id, 'amount': payment.amount}
            }), 201

        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500

    # ================== EXPENSES ==================

    @app.route('/api/expenses', methods=['GET'])
    @token_required
    def get_expenses():
        """Get all expenses"""
        session = g.session

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        campaign_id = request.args.get('campaign_id')
        category = request.args.get('category')

        query = session.query(Expense)

        if campaign_id:
            query = query.filter(Expense.campaign_id == campaign_id)

        if category:
            query = query.filter(Expense.category == category)

        total = query.count()
        expenses = query.order_by(
            Expense.expense_date.desc()
        ).offset((page - 1) * per_page).limit(per_page).all()

        return jsonify({
            'expenses': [{
                'id': e.id,
                'title': e.title,
                'category': e.category,
                'amount': e.amount,
                'currency': e.currency,
                'vendor': e.vendor,
                'expense_date': e.expense_date.isoformat() if e.expense_date else None,
                'status': e.status,
                'is_billable': e.is_billable
            } for e in expenses],
            'total': total,
            'page': page,
            'per_page': per_page
        }), 200

    @app.route('/api/expenses', methods=['POST'])
    @token_required
    def create_expense():
        """Create a new expense"""
        data = request.get_json()
        session = g.session

        try:
            expense = Expense(
                campaign_id=data.get('campaign_id'),
                client_id=data.get('client_id'),
                user_id=g.current_user.id,
                title=data['title'],
                description=data.get('description'),
                category=data.get('category'),
                amount=data['amount'],
                currency=data.get('currency', 'USD'),
                vendor=data.get('vendor'),
                receipt_url=data.get('receipt_url'),
                is_billable=data.get('is_billable', False),
                is_reimbursable=data.get('is_reimbursable', False),
                expense_date=datetime.fromisoformat(data.get('expense_date', datetime.utcnow().isoformat()))
            )

            session.add(expense)
            session.commit()

            log_action('create_expense', 'expense', expense.id, {'title': expense.title})

            return jsonify({
                'message': 'Expense created successfully',
                'expense': {'id': expense.id, 'title': expense.title}
            }), 201

        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500

    # ================== TIME TRACKING ==================

    @app.route('/api/time-entries', methods=['GET'])
    @token_required
    def get_time_entries():
        """Get time entries"""
        session = g.session

        user_id = request.args.get('user_id', g.current_user.id)
        campaign_id = request.args.get('campaign_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = session.query(TimeEntry).filter(TimeEntry.user_id == user_id)

        if campaign_id:
            query = query.filter(TimeEntry.campaign_id == campaign_id)

        if start_date:
            query = query.filter(TimeEntry.date >= datetime.fromisoformat(start_date))

        if end_date:
            query = query.filter(TimeEntry.date <= datetime.fromisoformat(end_date))

        entries = query.order_by(TimeEntry.date.desc()).all()

        return jsonify({
            'time_entries': [{
                'id': e.id,
                'description': e.description,
                'hours': e.hours,
                'date': e.date.isoformat() if e.date else None,
                'is_billable': e.is_billable,
                'hourly_rate': e.hourly_rate,
                'task_id': e.task_id,
                'campaign_id': e.campaign_id
            } for e in entries]
        }), 200

    @app.route('/api/time-entries', methods=['POST'])
    @token_required
    def create_time_entry():
        """Log time entry"""
        data = request.get_json()
        session = g.session

        try:
            entry = TimeEntry(
                user_id=g.current_user.id,
                task_id=data.get('task_id'),
                campaign_id=data.get('campaign_id'),
                client_id=data.get('client_id'),
                description=data.get('description'),
                hours=data['hours'],
                date=datetime.fromisoformat(data.get('date', datetime.utcnow().isoformat())),
                is_billable=data.get('is_billable', True),
                hourly_rate=data.get('hourly_rate')
            )

            session.add(entry)
            session.commit()

            return jsonify({
                'message': 'Time entry created successfully',
                'entry': {'id': entry.id, 'hours': entry.hours}
            }), 201

        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500

    # ================== FINANCIAL REPORTS ==================

    @app.route('/api/reports/financial-summary', methods=['GET'])
    @token_required
    def get_financial_summary():
        """Get financial summary report"""
        session = g.session

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Invoices summary
        invoice_query = session.query(
            func.count(Invoice.id).label('count'),
            func.sum(Invoice.total_amount).label('total'),
            func.sum(Invoice.paid_amount).label('paid')
        )

        if start_date:
            invoice_query = invoice_query.filter(Invoice.issue_date >= datetime.fromisoformat(start_date))
        if end_date:
            invoice_query = invoice_query.filter(Invoice.issue_date <= datetime.fromisoformat(end_date))

        invoice_stats = invoice_query.first()

        # Expenses summary
        expense_query = session.query(
            func.count(Expense.id).label('count'),
            func.sum(Expense.amount).label('total')
        )

        if start_date:
            expense_query = expense_query.filter(Expense.expense_date >= datetime.fromisoformat(start_date))
        if end_date:
            expense_query = expense_query.filter(Expense.expense_date <= datetime.fromisoformat(end_date))

        expense_stats = expense_query.first()

        return jsonify({
            'invoices': {
                'count': invoice_stats.count or 0,
                'total_amount': float(invoice_stats.total or 0),
                'paid_amount': float(invoice_stats.paid or 0),
                'outstanding': float((invoice_stats.total or 0) - (invoice_stats.paid or 0))
            },
            'expenses': {
                'count': expense_stats.count or 0,
                'total_amount': float(expense_stats.total or 0)
            },
            'profit': float((invoice_stats.paid or 0) - (expense_stats.total or 0))
        }), 200
