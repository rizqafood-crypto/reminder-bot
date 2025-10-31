# Installation Guide

## Quick Start (5 Minutes)

### Step 1: Clone and Setup Backend

```bash
# Clone the repository
git clone <repository-url>
cd reminder-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env and set your SECRET_KEY

# Initialize database and seed with demo data
python seed_data.py
```

### Step 2: Start Backend Server

```bash
# Start the API server
python main_app.py

# Server will run on http://localhost:5000
```

### Step 3: Setup and Start Frontend

```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create environment file
echo "VITE_API_URL=http://localhost:5000/api" > .env

# Start development server
npm run dev

# Frontend will run on http://localhost:5173
```

### Step 4: Login

Open your browser and navigate to http://localhost:5173

**Login with demo credentials:**
- Username: `admin`
- Password: `admin123`

## Detailed Installation

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8 or higher**
  - Check: `python --version`
  - Download: https://www.python.org/downloads/

- **Node.js 16 or higher**
  - Check: `node --version`
  - Download: https://nodejs.org/

- **pip** (usually comes with Python)
  - Check: `pip --version`

- **npm** (comes with Node.js)
  - Check: `npm --version`

### Backend Installation (Detailed)

1. **Create and activate virtual environment:**

```bash
# Create virtual environment
python3 -m venv venv

# Activate on Linux/Mac
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

2. **Install Python dependencies:**

```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**

```bash
# Copy example environment file
cp .env.example .env

# Generate a secure secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Edit .env file and update SECRET_KEY with generated value
```

4. **Initialize database:**

```bash
# Create database tables
python -c "from models import init_db; init_db()"

# Seed with demo data (optional but recommended)
python seed_data.py
```

5. **Run the application:**

```bash
# Development mode
python main_app.py

# Production mode with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 main_app:app
```

### Frontend Installation (Detailed)

1. **Navigate to frontend directory:**

```bash
cd frontend
```

2. **Install Node.js dependencies:**

```bash
npm install
```

3. **Configure environment:**

```bash
# Create .env file
cat > .env << EOF
VITE_API_URL=http://localhost:5000/api
EOF
```

4. **Run development server:**

```bash
npm run dev
```

5. **Build for production:**

```bash
npm run build

# The build will be in frontend/dist
# Serve with any static file server
```

## Database Options

### SQLite (Default - Development)

No additional setup required. The database file will be created automatically at `marketing_platform.db`.

### PostgreSQL (Recommended for Production)

1. **Install PostgreSQL:**
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# Mac (with Homebrew)
brew install postgresql
```

2. **Create database:**
```bash
sudo -u postgres psql
CREATE DATABASE marketing_platform;
CREATE USER marketing_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE marketing_platform TO marketing_user;
\q
```

3. **Update .env file:**
```bash
DATABASE_URL=postgresql://marketing_user:secure_password@localhost:5432/marketing_platform
```

4. **Install PostgreSQL Python adapter:**
```bash
pip install psycopg2-binary
```

## Troubleshooting

### "Module not found" errors

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Port already in use

```bash
# Backend (change port in main_app.py or use environment variable)
PORT=5001 python main_app.py

# Frontend (Vite will automatically try the next available port)
npm run dev
```

### Database errors

```bash
# Delete existing database and recreate
rm marketing_platform.db
python seed_data.py
```

### CORS errors

Make sure the frontend .env file has the correct API URL:
```
VITE_API_URL=http://localhost:5000/api
```

### Node modules issues

```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

## Production Deployment

### Backend on Linux Server

1. **Install system dependencies:**
```bash
sudo apt-get update
sudo apt-get install python3-pip python3-venv nginx postgresql
```

2. **Setup application:**
```bash
cd /var/www/marketing-platform
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

3. **Create systemd service:**
```bash
sudo nano /etc/systemd/system/marketing-platform.service
```

```ini
[Unit]
Description=Marketing Platform API
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/marketing-platform
Environment="PATH=/var/www/marketing-platform/venv/bin"
EnvironmentFile=/var/www/marketing-platform/.env
ExecStart=/var/www/marketing-platform/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 main_app:app

[Install]
WantedBy=multi-user.target
```

4. **Start service:**
```bash
sudo systemctl start marketing-platform
sudo systemctl enable marketing-platform
```

5. **Configure Nginx:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        root /var/www/marketing-platform/frontend/dist;
        try_files $uri /index.html;
    }
}
```

### Frontend Deployment Options

#### Option 1: Vercel
```bash
npm install -g vercel
vercel --prod
```

#### Option 2: Netlify
```bash
npm run build
# Drag and drop the dist folder to Netlify
```

#### Option 3: AWS S3 + CloudFront
```bash
npm run build
aws s3 sync dist/ s3://your-bucket-name
```

#### Option 4: Same server as backend
```bash
npm run build
sudo cp -r dist/* /var/www/marketing-platform/frontend/
```

## Docker Deployment (Coming Soon)

```bash
# Build and run with docker-compose
docker-compose up -d
```

## Updating

```bash
# Pull latest changes
git pull

# Update backend
source venv/bin/activate
pip install -r requirements.txt

# Update frontend
cd frontend
npm install
npm run build

# Restart services
sudo systemctl restart marketing-platform
```

## Getting Help

- Check the [README.md](README.md) for full documentation
- Review error logs in the terminal
- Open an issue on GitHub
- Contact support: support@agencyhub.com

## Next Steps

After installation:

1. **Change default passwords** for all demo users
2. **Configure integrations** for social media platforms
3. **Set up email notifications** (configure SMTP in .env)
4. **Configure backups** for your database
5. **Set up SSL** for production deployment
6. **Review security settings** and update SECRET_KEY
7. **Configure user roles** based on your team structure

---

Congratulations! Your Marketing Agency Management Platform is now installed and ready to use.
