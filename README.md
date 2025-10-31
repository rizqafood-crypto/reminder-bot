# Enterprise Marketing Agency Management Platform

A comprehensive, enterprise-grade management platform designed specifically for marketing agencies. This all-in-one solution streamlines agency operations from client acquisition to campaign execution, content management, finance tracking, and team collaboration.

## Features

### 🎯 Client Management (CRM)
- **Complete Client Profiles**: Store and manage detailed client information including company details, contacts, and interaction history
- **Lead Tracking**: Track leads through the sales funnel from prospect to active client
- **Contact Management**: Manage multiple contacts per client with role assignments
- **Interaction History**: Log all client communications, meetings, calls, and emails
- **Contract Management**: Store and track client contracts with document management

### 📊 Campaign Planning & Management
- **Multi-Channel Campaigns**: Plan and execute campaigns across multiple marketing channels
- **Budget Management**: Set campaign budgets and track actual spend in real-time
- **Team Collaboration**: Assign team members to campaigns with role-based access
- **Goal Setting & KPIs**: Define campaign objectives and track key performance indicators
- **Timeline Management**: Visual timeline views with start and end dates
- **Campaign Analytics**: Real-time performance tracking and ROI measurement

### 📝 Content Workflow Management
- **Content Calendar**: Visual calendar for scheduling content across all platforms
- **Approval Workflows**: Multi-stage approval process with reviewer assignments
- **Asset Management**: Store and organize images, videos, and documents
- **Platform Support**: Create content for Facebook, Instagram, LinkedIn, Twitter, blogs, and more
- **Status Tracking**: Track content from idea to published with status updates
- **Comments & Feedback**: Collaborative commenting system for content review
- **Hashtag & Mention Management**: Organize and track hashtags and social mentions

### 💰 Finance Management
- **Invoicing**: Create professional invoices with line items and tax calculations
- **Payment Tracking**: Record and track payments with multiple payment methods
- **Expense Management**: Track campaign expenses and overhead costs
- **Time Tracking**: Log billable hours per task and campaign
- **Profitability Analysis**: Calculate profit margins and ROI per client/campaign
- **Financial Reports**: Comprehensive financial summaries and reports

### 📈 Analytics & Reporting
- **Campaign Performance**: Track impressions, reach, engagement, clicks, and conversions
- **ROI Analysis**: Calculate and track return on investment for all campaigns
- **Team Performance**: Monitor individual and team productivity metrics
- **Custom Dashboards**: Configurable dashboards with key metrics
- **Client Reporting**: Generate client-ready performance reports
- **Data Visualization**: Charts and graphs for easy data interpretation

### 🤖 Automation & Workflows
- **Automated Workflows**: Create custom workflows triggered by events or schedules
- **Task Automation**: Automate recurring tasks and reminders
- **Notification System**: Real-time notifications for important events
- **Email Alerts**: Automated email notifications for deadlines and updates
- **Workflow Templates**: Pre-built workflow templates for common processes

### 👥 Team Collaboration
- **Task Management**: Create, assign, and track tasks with priorities and deadlines
- **Kanban Boards**: Visual task boards for agile workflow management
- **Comments & Discussions**: Threaded comments on tasks and content
- **Document Sharing**: Share files and assets with team members
- **Role-Based Access**: Granular permissions based on user roles
- **Activity Feed**: Real-time feed of team activities and updates

### 🔌 Integrations
- **Social Media Platforms**: Connect to Facebook, Instagram, LinkedIn, Twitter
- **Analytics Tools**: Integrate with Google Analytics, Facebook Insights
- **Payment Gateways**: Connect to payment processors
- **Cloud Storage**: Integration with cloud storage services
- **API Access**: RESTful API for custom integrations

## Technology Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: SQLAlchemy ORM with SQLite (upgradeable to PostgreSQL)
- **Authentication**: JWT-based authentication
- **API**: RESTful API with comprehensive endpoints

### Frontend
- **Framework**: React 18
- **Routing**: React Router v6
- **State Management**: Zustand
- **UI Components**: Tailwind CSS, Headless UI
- **Data Fetching**: React Query
- **Forms**: React Hook Form
- **Charts**: Recharts
- **Calendar**: React Big Calendar
- **Icons**: Lucide React

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- pip
- npm or yarn

### Backend Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd reminder-bot
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables:
```bash
export SECRET_KEY="your-secret-key-here"
export DATABASE_URL="sqlite:///marketing_platform.db"
# Optional: Set to PostgreSQL for production
# export DATABASE_URL="postgresql://user:password@localhost/dbname"
```

5. Initialize the database:
```bash
python -c "from models import init_db; init_db()"
```

6. Run the backend server:
```bash
python main_app.py
```

The API will be available at `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
echo "VITE_API_URL=http://localhost:5000/api" > .env
```

4. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## API Documentation

### Authentication

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password",
  "first_name": "John",
  "last_name": "Doe",
  "role": "CONTENT_CREATOR"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "secure_password"
}
```

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <token>
```

### Clients

#### List Clients
```http
GET /api/clients?page=1&per_page=20&status=active&search=keyword
Authorization: Bearer <token>
```

#### Create Client
```http
POST /api/clients
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Acme Corp",
  "company": "Acme Corporation",
  "industry": "Technology",
  "status": "ACTIVE",
  "email": "contact@acme.com",
  "phone": "+1234567890"
}
```

#### Get Client Details
```http
GET /api/clients/{id}
Authorization: Bearer <token>
```

### Campaigns

#### List Campaigns
```http
GET /api/campaigns?client_id=1&status=in_progress
Authorization: Bearer <token>
```

#### Create Campaign
```http
POST /api/campaigns
Authorization: Bearer <token>
Content-Type: application/json

{
  "client_id": 1,
  "name": "Summer Campaign 2024",
  "campaign_type": "social_media",
  "budget": 50000,
  "start_date": "2024-06-01",
  "end_date": "2024-08-31"
}
```

### Content

#### Get Content Calendar
```http
GET /api/content/calendar?start_date=2024-01-01&end_date=2024-12-31
Authorization: Bearer <token>
```

#### Create Content Item
```http
POST /api/content
Authorization: Bearer <token>
Content-Type: application/json

{
  "campaign_id": 1,
  "title": "Product Launch Post",
  "content_type": "post",
  "platform": "instagram",
  "scheduled_date": "2024-06-15T10:00:00"
}
```

### Tasks

#### Get Task Board (Kanban)
```http
GET /api/tasks/board?campaign_id=1
Authorization: Bearer <token>
```

#### Create Task
```http
POST /api/tasks
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Design Instagram Post",
  "campaign_id": 1,
  "priority": "HIGH",
  "due_date": "2024-06-10",
  "assignee_ids": [1, 2]
}
```

### Finance

#### Create Invoice
```http
POST /api/invoices
Authorization: Bearer <token>
Content-Type: application/json

{
  "client_id": 1,
  "invoice_number": "INV-2024-001",
  "total_amount": 5000,
  "due_date": "2024-07-01",
  "line_items": [
    {
      "description": "Social Media Management",
      "quantity": 1,
      "unit_price": 5000,
      "amount": 5000
    }
  ]
}
```

#### Record Payment
```http
POST /api/payments
Authorization: Bearer <token>
Content-Type: application/json

{
  "invoice_id": 1,
  "amount": 5000,
  "payment_method": "bank_transfer"
}
```

### Dashboard

#### Get Overview
```http
GET /api/dashboard/overview
Authorization: Bearer <token>
```

#### Get Team Performance
```http
GET /api/dashboard/team-performance
Authorization: Bearer <token>
```

## Database Schema

The platform uses a comprehensive relational database with the following main entities:

- **Users**: User accounts with role-based access
- **Clients**: Client information and status
- **Contacts**: Client contact persons
- **Campaigns**: Marketing campaigns
- **ContentItems**: Content pieces for publishing
- **Tasks**: Task management
- **Invoices**: Financial invoicing
- **Payments**: Payment tracking
- **Expenses**: Expense management
- **TimeEntries**: Time tracking
- **Analytics**: Campaign performance data
- **Workflows**: Automation workflows
- **Integrations**: Third-party integrations

See `models.py` for complete schema definitions.

## User Roles

The platform supports the following user roles:

- **ADMIN**: Full system access
- **MANAGER**: Manage teams, clients, and campaigns
- **TEAM_LEAD**: Lead projects and teams
- **CONTENT_CREATOR**: Create and manage content
- **DESIGNER**: Design assets and content
- **ACCOUNT_MANAGER**: Manage client relationships
- **ANALYST**: Access analytics and reports
- **FINANCE**: Manage invoices and payments

## Security

- JWT-based authentication with token expiration
- Password hashing using werkzeug.security
- Role-based access control (RBAC)
- Audit logging for all actions
- SQL injection protection via SQLAlchemy ORM
- CORS configuration for frontend integration

## Production Deployment

### Backend

1. Use PostgreSQL instead of SQLite:
```bash
export DATABASE_URL="postgresql://user:password@host:5432/dbname"
```

2. Set a strong secret key:
```bash
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
```

3. Use a production WSGI server (Gunicorn):
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 main_app:app
```

4. Set up Nginx as reverse proxy
5. Enable HTTPS with SSL certificates
6. Configure environment-specific settings

### Frontend

1. Build the production bundle:
```bash
npm run build
```

2. Serve with Nginx or deploy to:
   - Vercel
   - Netlify
   - AWS S3 + CloudFront
   - Any static hosting service

## Development

### Running Tests
```bash
# Backend tests
pytest

# Frontend tests
npm test
```

### Code Style
```bash
# Backend (PEP 8)
flake8 .

# Frontend (ESLint)
npm run lint
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

Proprietary - All rights reserved

## Support

For support, please contact: support@agencyhub.com

## Roadmap

- [ ] Mobile apps (iOS/Android)
- [ ] Advanced reporting with custom templates
- [ ] AI-powered content suggestions
- [ ] Advanced social media scheduling
- [ ] Client portal for self-service
- [ ] Multi-language support
- [ ] Advanced workflow automation
- [ ] Integration marketplace

## Version History

### v1.0.0 (2024)
- Initial release
- Complete CRM module
- Campaign management
- Content workflow
- Finance management
- Analytics engine
- Team collaboration
- RESTful API
- React frontend

---

Built with ❤️ for marketing agencies worldwide
