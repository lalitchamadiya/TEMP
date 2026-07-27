import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Hostel_Management_System.settings')
django.setup()
from django.urls import reverse
try:
    print("REVERSE module_list:", reverse('module_list'))
except Exception as e:
    print("ERROR module_list:", e)
