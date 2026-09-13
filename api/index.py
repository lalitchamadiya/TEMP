import os
import sys
from pathlib import Path

# Add project root directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Hostel_Management_System.settings')

from django.core.wsgi import get_wsgi_application

# Initialize Django WSGI application
app = get_wsgi_application()
