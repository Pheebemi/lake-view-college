# cPanel Deployment Guide for Django

This guide will help you deploy your Lake View College Django application to a cPanel-based hosting provider.

## Prerequisites

1. A cPanel hosting account with Python support
2. SSH access to your hosting account
3. Your project code uploaded to a Git repository (GitHub, GitLab, etc.)
4. cPanel must have Python applications enabled

## Important Notes

- cPanel hosting typically uses shared resources, so performance may vary
- Some hosts may not support all Python packages (check with your provider)
- File permissions and ownership are critical in shared hosting
- SQLite may have permission issues; consider using MySQL/PostgreSQL if available

## Step 1: Prepare Your Project

### 1.1 Update Settings for cPanel

Your current `settings.py` is configured for environment variables, which works well with cPanel. However, you may need to adjust some settings.

### 1.2 Create Production Settings

Create a production settings file or update your `.env` file:

```bash
# Copy and modify your environment file
cp env_sample.txt .env.production
```

Edit `.env.production` with production values:

```env
DJANGO_SECRET_KEY=your-very-long-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=lakeview.pythonanywhere.com,www.lakeview.pythonanywhere.com
DATABASE_ENGINE=django.db.backends.sqlite3
DATABASE_NAME=/home/lakeview/lakeview_project/db.sqlite3
STATIC_URL=/static/
STATIC_ROOT=/home/lakeview/public_html/static
MEDIA_URL=/media/
MEDIA_ROOT=/home/lakeview/public_html/media
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=25
EMAIL_USE_TLS=False
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

**Note**: Replace `lakeview` with your actual cPanel username.

### 1.3 Update Requirements

Your `requirements.txt` should work, but some packages might not be available. Check with your hosting provider for supported packages.

## Step 2: Access Your cPanel Account

### 2.1 Log into cPanel

1. Access your cPanel at `https://lakeview.pythonanywhere.com:2083` or through your hosting provider's control panel
2. Use your cPanel username and password to log in

### 2.2 Check Python Support

1. Look for "Python Applications" or "Setup Python App" in your cPanel
2. If not available, contact your hosting provider to enable Python support
3. Check which Python versions are supported (preferably 3.8+)

## Step 3: Set Up Python Application

### 3.1 Create Python Application

1. In cPanel, go to **Python Applications** (or **Setup Python App**)
2. Click **Create Application**
3. Configure:
   - **Python Version**: Choose the highest available (preferably 3.8 or higher)
   - **Application Root**: `/home/lakeview/lakeview_project` (replace `lakeview` with your username)
   - **Application URL**: Leave as default or set to a subdirectory if needed
   - **Passenger Log File**: Leave default
4. Click **Create**

### 3.2 Install Dependencies

1. After creation, you'll see the application details
2. Go to the **Terminal** section or use SSH to access your account
3. Navigate to your application directory:

```bash
cd /home/lakeview/lakeview_project
```

4. Activate the virtual environment (cPanel usually creates this automatically):

```bash
source /home/lakeview/virtualenv/lakeview_project/3.x/bin/activate
# Note: The path may vary based on Python version
```

5. Install your requirements:

```bash
pip install -r requirements.txt
```

## Step 4: Upload Your Code

### 4.1 Using Git (Recommended)

1. In cPanel, go to **Git Version Control**
2. Create a new repository:
   - **Repository Path**: `/home/lakeview/lakeview_project`
   - **Repository URL**: `https://github.com/lakeview/lake-view-college-pro.git`
   - **Repository Name**: `lakeview_project`
3. Click **Create**
4. This will clone your repository into the application directory

### 4.2 Manual Upload via File Manager

1. In cPanel, go to **File Manager**
2. Navigate to `/home/lakeview/`
3. Create a `lakeview_project` directory
4. Upload your project files using the upload feature
5. Extract if uploaded as a zip/tar file

### 4.3 Via SSH/SFTP

1. Use an SFTP client (FileZilla, WinSCP, etc.)
2. Connect to your hosting account:
   - Host: lakeview.pythonanywhere.com
   - Username: your cPanel username
   - Password: your cPanel password
   - Port: 22
3. Upload files to `/home/lakeview/lakeview_project`

## Step 5: Configure Application Structure

### 5.1 Set Up Directory Structure

Your application should be structured like this:

```
/home/lakeview/
├── lakeview_project/          # Your Django project
│   ├── lakeView_project/     # Django settings directory
│   ├── accounts/
│   ├── core/
│   ├── dashboard/
│   ├── staticfiles/          # Will be created by collectstatic
│   ├── media/                # For uploaded files
│   ├── db.sqlite3           # Database file
│   └── requirements.txt
├── public_html/              # Web root directory
│   ├── static/              # Symlinked static files
│   └── media/               # Symlinked media files
└── virtualenv/              # Virtual environments
```

### 5.2 Create Symlinks for Static/Media Files

Create symbolic links from your application to the public directory:

```bash
# Navigate to public_html
cd /home/lakeview/public_html

# Create static directory if it doesn't exist
mkdir -p static
mkdir -p media

# Create symlinks (adjust paths as needed)
ln -s /home/lakeview/lakeview_project/staticfiles static
ln -s /home/lakeview/lakeview_project/media media
```

## Step 6: Configure Passenger WSGI

### 6.1 Create passenger_wsgi.py

In your project root (`/home/lakeview/lakeview_project/`), create `passenger_wsgi.py`:

```python
import os
import sys

# Add your project directory to the sys.path
sys.path.insert(0, '/home/lakeview/lakeview_project')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lakeView_project.settings')

# Load environment variables
# Option 1: Load from .env file
try:
    from dotenv import load_dotenv
    load_dotenv('/home/lakeview/lakeview_project/.env.production')
except ImportError:
    pass

# Option 2: Set environment variables directly
os.environ['DJANGO_SECRET_KEY'] = 'your-secret-key-here'
os.environ['DJANGO_DEBUG'] = 'False'
os.environ['DJANGO_ALLOWED_HOSTS'] = 'lakeview.pythonanywhere.com,www.lakeview.pythonanywhere.com'

# Import Django
import django
django.setup()

# Import the WSGI application
from lakeView_project.wsgi import application
```

### 6.2 Update Application Configuration

1. In cPanel **Python Applications**, click on your application
2. Update the **Application Startup File** to: `passenger_wsgi.py`
3. Make sure the **Application Root** is correct: `/home/lakeview/lakeview_project`
4. Save changes

## Step 7: Database Setup

### 7.1 Using SQLite (Default)

1. Make sure your database file has correct permissions:

```bash
cd /home/lakeview/lakeview_project
chmod 644 db.sqlite3
```

2. If the database doesn't exist yet, Django will create it during migration

### 7.2 Using MySQL (Recommended for cPanel)

If your cPanel has MySQL support:

1. In cPanel, go to **MySQL Databases**
2. Create a new database and user
3. Update your `.env.production` file:

```env
DATABASE_ENGINE=django.db.backends.mysql
DATABASE_NAME=lakeview_django_db
DATABASE_USER=lakeview_dbuser
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=localhost
DATABASE_PORT=3306
```

4. Install MySQL client in your virtual environment:

```bash
pip install mysqlclient
```

## Step 8: Run Initial Setup

### 8.1 Access via SSH/Terminal

1. In cPanel, go to **Terminal** or connect via SSH
2. Navigate to your project:

```bash
cd /home/lakeview/lakeview_project
source /home/lakeview/virtualenv/lakeview_project/3.x/bin/activate
```

### 8.2 Run Migrations

```bash
python manage.py migrate
```

### 8.3 Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 8.4 Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

## Step 9: Configure Domain and SSL

### 9.1 Add Domain

1. In cPanel, go to **Domains**
2. Add your domain as an addon domain if not already configured
3. Point your domain's document root to `/home/lakeview/public_html`

### 9.2 SSL Certificate

1. In cPanel, go to **SSL/TLS Status**
2. Click **Run AutoSSL** to get a free SSL certificate
3. Make sure your domain is included in `ALLOWED_HOSTS`

## Step 10: Test and Troubleshoot

### 10.1 Test Your Application

1. Visit your domain: `https://lakeview.pythonanywhere.com`
2. Check for any errors in the browser
3. Test different pages and functionality

### 10.2 Check Logs

1. In cPanel, go to **Errors** or **Raw Access Logs**
2. Check application-specific logs in your project directory
3. Look for Python application logs

### 10.3 Common Issues and Solutions

#### Permission Errors:
```bash
# Fix permissions for files and directories
find /home/lakeview/lakeview_project -type f -exec chmod 644 {} \;
find /home/lakeview/lakeview_project -type d -exec chmod 755 {} \;

# Fix database permissions
chmod 644 /home/lakeview/lakeview_project/db.sqlite3
```

#### Import Errors:
- Check if all packages in `requirements.txt` are installed
- Some packages may not be available on shared hosting

#### Static Files Not Loading:
- Verify symlinks are created correctly
- Run `collectstatic` again
- Check file permissions on static files

#### Database Connection Issues:
- For SQLite: Check file permissions and path
- For MySQL: Verify database credentials and user privileges

## Step 11: File Permissions

Proper file permissions are crucial in shared hosting:

```bash
# Set correct ownership (replace lakeview with your username)
chown -R lakeview:lakeview /home/lakeview/lakeview_project

# Set directory permissions
find /home/lakeview/lakeview_project -type d -exec chmod 755 {} \;

# Set file permissions
find /home/lakeview/lakeview_project -type f -exec chmod 644 {} \;

# Make manage.py executable
chmod 755 /home/lakeview/lakeview_project/manage.py
```

## Step 12: Maintenance and Updates

### 12.1 Updating Your Application

1. Make changes locally and push to your Git repository
2. In cPanel **Git Version Control**, click **Pull or Deploy** for your repository
3. Or manually pull changes via SSH:

```bash
cd /home/lakeview/lakeview_project
git pull origin main
```

4. Install new requirements if needed:

```bash
source /home/lakeview/virtualenv/lakeview_project/3.x/bin/activate
pip install -r requirements.txt
```

5. Run migrations:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

6. Restart the application in cPanel **Python Applications**

### 12.2 Backup Strategy

1. **Database**: Use cPanel **Backup** tools for MySQL databases
2. **Files**: Regularly download important files via File Manager or SFTP
3. **Git**: Your repository serves as a backup of your code

## Security Considerations

### 12.1 Environment Variables

Never commit sensitive information to version control. Use:

1. `.env.production` file (keep it secure)
2. Environment variables set in `passenger_wsgi.py`
3. cPanel environment variables (if supported)

### 12.2 File Permissions

- Keep sensitive files (`.env`, database files) with restricted permissions
- Avoid world-writable files and directories
- Regularly audit permissions

### 12.3 Updates

- Keep Django and packages updated
- Monitor for security updates
- Use HTTPS for all connections

## Performance Optimization

### 13.1 Static Files

- Use a CDN if available through your host
- Enable compression in cPanel
- Optimize images before upload

### 13.2 Caching

- Use Django's caching framework
- Enable browser caching for static files
- Consider Redis if available

### 13.3 Database

- Use database indexes for frequently queried fields
- Optimize queries in your Django views
- Consider database connection pooling

## Support and Resources

### 13.1 Hosting Provider Support

- Contact your hosting provider for cPanel-specific issues
- Ask about Python version support and limitations
- Inquire about available resources and upgrade options

### 13.2 Django Resources

- Django Deployment Documentation: https://docs.djangoproject.com/en/5.1/howto/deployment/
- cPanel Python Documentation: Check your provider's documentation

### 13.3 Monitoring

- Use Django's logging to monitor errors
- Check cPanel resource usage regularly
- Monitor application performance and response times

## Quick Reference Commands

```bash
# Activate virtual environment (adjust path for your Python version)
source /home/lakeview/virtualenv/lakeview_project/3.x/bin/activate

# Navigate to project
cd /home/lakeview/lakeview_project

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser

# Check for deployment issues
python manage.py check --deploy

# Clear cache
python manage.py clear_cache

# Fix permissions
find . -type f -exec chmod 644 {} \;
find . -type d -exec chmod 755 {} \;
```

## Alternative: Subdirectory Deployment

If you want to deploy to a subdirectory (e.g., `lakeview.pythonanywhere.com/django-app`):

1. Update `passenger_wsgi.py` to handle URL prefixes
2. Configure cPanel to serve from a subdirectory
3. Update `STATIC_URL` and `MEDIA_URL` accordingly

## Troubleshooting Checklist

- [ ] Python application created in cPanel
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] Code uploaded correctly
- [ ] `passenger_wsgi.py` configured
- [ ] Environment variables set
- [ ] Database configured and migrated
- [ ] Static files collected and symlinked
- [ ] File permissions correct
- [ ] Domain configured with SSL
- [ ] Application restarted after changes

This guide should get your Django application running smoothly on cPanel hosting!