import os
import sys
from pathlib import Path

# Add project root directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Hostel_Management_System.settings')

from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

# Initialize Django WSGI application
app = get_wsgi_application()

# Auto-migrate database & seed modules + superadmin on deployment startup/cold-start
try:
    call_command('migrate', interactive=False)
    call_command('seed_modules')
    call_command('seed_super_admin')
except Exception as e:
    print(f"Auto-setup execution info: {e}")
