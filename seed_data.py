"""
Seed script to populate the database with sample data
Run this after initializing the database to create demo data
"""

from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from models import (
    init_db, User, Client, Contact, Campaign, ContentItem, Task,
    Invoice, InvoiceLineItem, Payment, Expense, TimeEntry,
    CampaignAnalytics, UserRole, ClientStatus, CampaignStatus,
    ContentStatus, TaskStatus, TaskPriority, InvoiceStatus, PaymentStatus
)

def seed_database():
    """Populate database with sample data"""
    print("Initializing database...")
    engine, Session = init_db()
    session = Session()

    try:
        # Clear existing data (optional)
        print("Clearing existing data...")
        # Uncomment if you want to clear existing data
        # Base.metadata.drop_all(engine)
        # Base.metadata.create_all(engine)

        # Create Users
        print("Creating users...")
        users = [
            User(
                username='admin',
                email='admin@agencyhub.com',
                password_hash=generate_password_hash('admin123'),
                first_name='Admin',
                last_name='User',
                role=UserRole.ADMIN,
                phone='+1234567890',
                department='Management'
            ),
            User(
                username='sarah_manager',
                email='sarah@agencyhub.com',
                password_hash=generate_password_hash('password123'),
                first_name='Sarah',
                last_name='Johnson',
                role=UserRole.MANAGER,
                department='Operations'
            ),
            User(
                username='mike_creator',
                email='mike@agencyhub.com',
                password_hash=generate_password_hash('password123'),
                first_name='Mike',
                last_name='Chen',
                role=UserRole.CONTENT_CREATOR,
                department='Content'
            ),
            User(
                username='emma_designer',
                email='emma@agencyhub.com',
                password_hash=generate_password_hash('password123'),
                first_name='Emma',
                last_name='Davis',
                role=UserRole.DESIGNER,
                department='Creative'
            ),
            User(
                username='john_analyst',
                email='john@agencyhub.com',
                password_hash=generate_password_hash('password123'),
                first_name='John',
                last_name='Smith',
                role=UserRole.ANALYST,
                department='Analytics'
            )
        ]

        for user in users:
            session.add(user)
        session.commit()
        print(f"Created {len(users)} users")

        # Create Clients
        print("Creating clients...")
        clients = [
            Client(
                name='TechStart Inc',
                company='TechStart Innovations',
                industry='Technology',
                status=ClientStatus.ACTIVE,
                email='contact@techstart.com',
                phone='+1555000001',
                website='https://techstart.com',
                city='San Francisco',
                country='USA',
                annual_revenue=5000000,
                company_size='50-100',
                lead_source='Referral',
                created_by=1
            ),
            Client(
                name='Fashion Forward',
                company='Fashion Forward LLC',
                industry='Fashion & Retail',
                status=ClientStatus.ACTIVE,
                email='info@fashionforward.com',
                phone='+1555000002',
                website='https://fashionforward.com',
                city='New York',
                country='USA',
                annual_revenue=3000000,
                company_size='20-50',
                lead_source='Website',
                created_by=1
            ),
            Client(
                name='Healthy Living Co',
                company='Healthy Living Corporation',
                industry='Health & Wellness',
                status=ClientStatus.ACTIVE,
                email='hello@healthyliving.com',
                phone='+1555000003',
                website='https://healthyliving.com',
                city='Los Angeles',
                country='USA',
                annual_revenue=2000000,
                company_size='10-20',
                lead_source='Cold Outreach',
                created_by=2
            ),
            Client(
                name='EduTech Solutions',
                company='EduTech Solutions Inc',
                industry='Education',
                status=ClientStatus.PROSPECT,
                email='contact@edutech.com',
                phone='+1555000004',
                website='https://edutech.com',
                city='Boston',
                country='USA',
                lead_source='LinkedIn',
                created_by=2
            )
        ]

        for client in clients:
            session.add(client)
        session.commit()
        print(f"Created {len(clients)} clients")

        # Create Contacts
        print("Creating contacts...")
        contacts = [
            Contact(client_id=1, first_name='Alice', last_name='Brown',
                   title='Marketing Director', email='alice@techstart.com',
                   phone='+1555000011', is_primary=True),
            Contact(client_id=2, first_name='Bob', last_name='Wilson',
                   title='CEO', email='bob@fashionforward.com',
                   phone='+1555000021', is_primary=True),
            Contact(client_id=3, first_name='Carol', last_name='Martinez',
                   title='VP Marketing', email='carol@healthyliving.com',
                   phone='+1555000031', is_primary=True),
        ]

        for contact in contacts:
            session.add(contact)
        session.commit()
        print(f"Created {len(contacts)} contacts")

        # Create Campaigns
        print("Creating campaigns...")
        campaigns = [
            Campaign(
                client_id=1,
                name='Q4 Product Launch',
                description='Launch campaign for new SaaS product',
                status=CampaignStatus.IN_PROGRESS,
                campaign_type='integrated',
                objectives='Generate 1000 leads and 100 conversions',
                target_audience='B2B tech companies, 100-500 employees',
                channels=['social_media', 'email', 'content_marketing'],
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now() + timedelta(days=60),
                budget=50000,
                actual_spend=25000,
                goals={'leads': 1000, 'conversions': 100},
                kpis={'cpa': 500, 'roi': 3.0}
            ),
            Campaign(
                client_id=2,
                name='Summer Fashion Collection',
                description='Social media campaign for summer collection',
                status=CampaignStatus.IN_PROGRESS,
                campaign_type='social_media',
                objectives='Increase brand awareness and drive sales',
                target_audience='Women 25-45, fashion enthusiasts',
                channels=['instagram', 'facebook', 'tiktok'],
                start_date=datetime.now() - timedelta(days=15),
                end_date=datetime.now() + timedelta(days=75),
                budget=30000,
                actual_spend=12000,
                goals={'engagement': 50000, 'sales': 200000}
            ),
            Campaign(
                client_id=3,
                name='Wellness Challenge Campaign',
                description='30-day wellness challenge promotion',
                status=CampaignStatus.PLANNING,
                campaign_type='content_marketing',
                objectives='Build community and increase app downloads',
                target_audience='Health-conscious individuals 30-55',
                channels=['blog', 'email', 'social_media'],
                start_date=datetime.now() + timedelta(days=14),
                end_date=datetime.now() + timedelta(days=44),
                budget=20000,
                actual_spend=0
            )
        ]

        for campaign in campaigns:
            session.add(campaign)
        session.commit()

        # Add team members to campaigns
        campaigns[0].team_members.extend([users[1], users[2], users[3]])
        campaigns[1].team_members.extend([users[2], users[3]])
        campaigns[2].team_members.extend([users[1], users[2]])
        session.commit()
        print(f"Created {len(campaigns)} campaigns")

        # Create Content Items
        print("Creating content items...")
        content_items = [
            ContentItem(
                campaign_id=1,
                client_id=1,
                title='Product Launch Announcement',
                content_type='post',
                platform='linkedin',
                description='Announce new product launch',
                status=ContentStatus.APPROVED,
                priority=TaskPriority.HIGH,
                creator_id=3,
                scheduled_date=datetime.now() + timedelta(days=2),
                hashtags=['#SaaS', '#ProductLaunch', '#Innovation']
            ),
            ContentItem(
                campaign_id=1,
                client_id=1,
                title='Feature Highlight Video',
                content_type='video',
                platform='youtube',
                description='60-second feature highlights',
                status=ContentStatus.IN_REVIEW,
                priority=TaskPriority.HIGH,
                creator_id=3,
                scheduled_date=datetime.now() + timedelta(days=5)
            ),
            ContentItem(
                campaign_id=2,
                client_id=2,
                title='Summer Collection Showcase',
                content_type='post',
                platform='instagram',
                description='Showcase new summer pieces',
                status=ContentStatus.PUBLISHED,
                priority=TaskPriority.MEDIUM,
                creator_id=3,
                scheduled_date=datetime.now() - timedelta(days=3),
                published_date=datetime.now() - timedelta(days=3),
                hashtags=['#SummerFashion', '#OOTD', '#Style']
            ),
            ContentItem(
                campaign_id=2,
                client_id=2,
                title='Behind the Scenes',
                content_type='story',
                platform='instagram',
                description='BTS of photoshoot',
                status=ContentStatus.SCHEDULED,
                priority=TaskPriority.LOW,
                creator_id=3,
                scheduled_date=datetime.now() + timedelta(days=1)
            )
        ]

        for item in content_items:
            session.add(item)
        session.commit()
        print(f"Created {len(content_items)} content items")

        # Create Tasks
        print("Creating tasks...")
        tasks = [
            Task(
                campaign_id=1,
                title='Design product launch graphics',
                description='Create social media graphics for product launch',
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.HIGH,
                created_by=2,
                due_date=datetime.now() + timedelta(days=3),
                estimated_hours=8
            ),
            Task(
                campaign_id=1,
                title='Write product announcement copy',
                description='Draft announcement copy for all channels',
                status=TaskStatus.COMPLETED,
                priority=TaskPriority.HIGH,
                created_by=2,
                due_date=datetime.now() - timedelta(days=2),
                completed_at=datetime.now() - timedelta(days=3),
                estimated_hours=4,
                actual_hours=4.5
            ),
            Task(
                campaign_id=2,
                title='Schedule Instagram posts',
                description='Schedule posts for next week',
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                created_by=2,
                due_date=datetime.now() + timedelta(days=7),
                estimated_hours=2
            )
        ]

        for task in tasks:
            session.add(task)
        session.commit()

        # Assign users to tasks
        tasks[0].assignees.append(users[3])
        tasks[1].assignees.append(users[2])
        tasks[2].assignees.append(users[2])
        session.commit()
        print(f"Created {len(tasks)} tasks")

        # Create Invoices
        print("Creating invoices...")
        invoice1 = Invoice(
            client_id=1,
            campaign_id=1,
            invoice_number='INV-2024-001',
            title='Q4 Product Launch - Monthly Retainer',
            status=InvoiceStatus.PAID,
            subtotal=10000,
            tax_rate=0.1,
            tax_amount=1000,
            total_amount=11000,
            paid_amount=11000,
            issue_date=datetime.now() - timedelta(days=30),
            due_date=datetime.now() - timedelta(days=15),
            paid_date=datetime.now() - timedelta(days=10),
            currency='USD'
        )
        session.add(invoice1)
        session.flush()

        line_items1 = [
            InvoiceLineItem(
                invoice_id=invoice1.id,
                description='Campaign Management',
                quantity=1,
                unit_price=5000,
                amount=5000
            ),
            InvoiceLineItem(
                invoice_id=invoice1.id,
                description='Content Creation',
                quantity=20,
                unit_price=250,
                amount=5000
            )
        ]
        for item in line_items1:
            session.add(item)

        invoice2 = Invoice(
            client_id=2,
            campaign_id=2,
            invoice_number='INV-2024-002',
            title='Summer Campaign - First Installment',
            status=InvoiceStatus.SENT,
            subtotal=8000,
            tax_rate=0.1,
            tax_amount=800,
            total_amount=8800,
            paid_amount=0,
            issue_date=datetime.now() - timedelta(days=5),
            due_date=datetime.now() + timedelta(days=25),
            currency='USD'
        )
        session.add(invoice2)
        session.flush()

        line_items2 = [
            InvoiceLineItem(
                invoice_id=invoice2.id,
                description='Social Media Management',
                quantity=1,
                unit_price=8000,
                amount=8000
            )
        ]
        for item in line_items2:
            session.add(item)

        session.commit()
        print("Created 2 invoices with line items")

        # Create Payment
        print("Creating payments...")
        payment = Payment(
            invoice_id=invoice1.id,
            amount=11000,
            payment_method='bank_transfer',
            status=PaymentStatus.COMPLETED,
            payment_date=datetime.now() - timedelta(days=10),
            transaction_id='TXN-2024-001'
        )
        session.add(payment)
        session.commit()
        print("Created 1 payment")

        # Create Expenses
        print("Creating expenses...")
        expenses = [
            Expense(
                campaign_id=1,
                client_id=1,
                user_id=2,
                title='Facebook Ads Spend',
                category='advertising',
                amount=5000,
                vendor='Meta',
                is_billable=True,
                expense_date=datetime.now() - timedelta(days=15),
                status='approved'
            ),
            Expense(
                campaign_id=2,
                client_id=2,
                user_id=2,
                title='Stock Photos Purchase',
                category='assets',
                amount=299,
                vendor='Shutterstock',
                is_billable=True,
                expense_date=datetime.now() - timedelta(days=10),
                status='approved'
            )
        ]
        for expense in expenses:
            session.add(expense)
        session.commit()
        print(f"Created {len(expenses)} expenses")

        # Create Time Entries
        print("Creating time entries...")
        time_entries = [
            TimeEntry(
                user_id=3,
                task_id=1,
                campaign_id=1,
                client_id=1,
                description='Worked on product launch graphics',
                hours=4.5,
                date=datetime.now() - timedelta(days=1),
                is_billable=True,
                hourly_rate=100
            ),
            TimeEntry(
                user_id=3,
                task_id=2,
                campaign_id=1,
                client_id=1,
                description='Completed announcement copy',
                hours=4.5,
                date=datetime.now() - timedelta(days=3),
                is_billable=True,
                hourly_rate=100
            )
        ]
        for entry in time_entries:
            session.add(entry)
        session.commit()
        print(f"Created {len(time_entries)} time entries")

        # Create Campaign Analytics
        print("Creating campaign analytics...")
        analytics = [
            CampaignAnalytics(
                campaign_id=1,
                date=datetime.now() - timedelta(days=7),
                impressions=50000,
                reach=35000,
                engagement=2500,
                clicks=1200,
                conversions=45,
                ctr=2.4,
                conversion_rate=3.75,
                engagement_rate=7.14,
                spend=5000,
                revenue=22500,
                roi=4.5
            ),
            CampaignAnalytics(
                campaign_id=2,
                date=datetime.now() - timedelta(days=7),
                impressions=75000,
                reach=50000,
                engagement=4500,
                clicks=800,
                conversions=25,
                ctr=1.07,
                conversion_rate=3.13,
                engagement_rate=9.0,
                spend=3000,
                revenue=12500,
                roi=4.17
            )
        ]
        for analytic in analytics:
            session.add(analytic)
        session.commit()
        print(f"Created {len(analytics)} analytics records")

        print("\n" + "="*60)
        print("Database seeded successfully!")
        print("="*60)
        print("\nDemo Login Credentials:")
        print("-" * 60)
        print("Admin User:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\nManager:")
        print("  Username: sarah_manager")
        print("  Password: password123")
        print("\nContent Creator:")
        print("  Username: mike_creator")
        print("  Password: password123")
        print("="*60)

    except Exception as e:
        session.rollback()
        print(f"\nError seeding database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == '__main__':
    seed_database()
