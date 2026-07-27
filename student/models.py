from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
]

STATE_CHOICES = [
    ('Andhra Pradesh', 'Andhra Pradesh'),
    ('Arunachal Pradesh', 'Arunachal Pradesh'),
    ('Assam', 'Assam'),
    ('Bihar', 'Bihar'),
    ('Chhattisgarh', 'Chhattisgarh'),
    ('Goa', 'Goa'),
    ('Gujarat', 'Gujarat'),
    ('Haryana', 'Haryana'),
    ('Himachal Pradesh', 'Himachal Pradesh'),
    ('Jammu and Kashmir', 'Jammu and Kashmir'),
    ('Jharkhand', 'Jharkhand'),
    ('Karnataka', 'Karnataka'),
    ('Kerala', 'Kerala'),
    ('Madhya Pradesh', 'Madhya Pradesh'),
    ('Maharashtra', 'Maharashtra'),
    ('Manipur', 'Manipur'),
    ('Meghalaya', 'Meghalaya'),
    ('Mizoram', 'Mizoram'),
    ('Nagaland', 'Nagaland'),
    ('Odisha', 'Odisha'),
    ('Punjab', 'Punjab'),
    ('Rajasthan', 'Rajasthan'),
    ('Sikkim', 'Sikkim'),
    ('Tamil Nadu', 'Tamil Nadu'),
    ('Telangana', 'Telangana'),
    ('Tripura', 'Tripura'),
    ('Uttar Pradesh', 'Uttar Pradesh'),
    ('Uttarakhand', 'Uttarakhand'),
    ('West Bengal', 'West Bengal'),
    ('Andaman and Nicobar Islands', 'Andaman and Nicobar Islands'),
    ('Chandigarh', 'Chandigarh'),
    ('Dadra and Nagar Haveli', 'Dadra and Nagar Haveli'),
    ('Daman and Diu', 'Daman and Diu'),
    ('Delhi', 'Delhi'),
    ('Lakshadweep', 'Lakshadweep'),
    ('Puducherry', 'Puducherry'),
    ('California', 'California'),
    ('Texas', 'Texas'),
    ('New York', 'New York'),
]

CITY_CHOICES = [
    ('Hyderabad', 'Hyderabad'),
    ('Ahmedabad', 'Ahmedabad'),
    ('Surat', 'Surat'),
    ('Vadodara', 'Vadodara'),
    ('Rajkot', 'Rajkot'),
    ('Bhavnagar', 'Bhavnagar'),
    ('Junagadh', 'Junagadh'),
    ('Jamnagar', 'Jamnagar'),
    ('Gandhinagar', 'Gandhinagar'),
    ('Navsari', 'Navsari'),
    ('Anand', 'Anand'),
    ('Bhuj', 'Bhuj'),
    ('Valsad', 'Valsad'),
    ('Bharuch', 'Bharuch'),
    ('Palanpur', 'Palanpur'),
    ('Porbandar', 'Porbandar'),
    ('Nadiad', 'Nadiad'),
    ('Mehsana', 'Mehsana'),
    ('Surendranagar', 'Surendranagar'),
    ('Virpur', 'Virpur'),
    ('Vapi', 'Vapi'),
    ('Los Angeles', 'Los Angeles'),
    ('New York City', 'New York City'),
]

DEPARTMENT_CHOICES = [
    ('CSE', 'Computer Science and Engineering'),
    ('ECE', 'Electronics and Communication Engineering'),
    ('EEE', 'Electrical and Electronics Engineering'),
    ('ME', 'Mechanical Engineering'),
    ('CE', 'Civil Engineering'),
    ('CHE', 'Chemical Engineering'),
    ('BIO', 'Biotechnology'),
    ('AE', 'Aerospace Engineering'),
    ('IT', 'Information Technology'),
    ('EE', 'Electrical Engineering'),
    ('ARCH', 'Architecture'),
    ('BBA', 'Business Administration'),
    ('MBA', 'Master of Business Administration'),
    ('BSC', 'Bachelor of Science'),
    ('MSC', 'Master of Science'),
    ('PHYS', 'Physics'),
    ('CHEM', 'Chemistry'),
    ('MATH', 'Mathematics'),
    ('BIO', 'Biology'),
    ('ENV', 'Environmental Science'),
    ('LAW', 'Law'),
    ('MED', 'Medicine'),
    ('PHARMA', 'Pharmacy'),
    ('DENT', 'Dentistry'),
    ('NURS', 'Nursing'),
    ('PSY', 'Psychology'),
    ('SOC', 'Sociology'),
    ('ECON', 'Economics'),
    ('ENG', 'English Literature'),
    ('HIST', 'History'),
    ('GEO', 'Geography'),
    ('POLSCI', 'Political Science'),
    ('EDU', 'Education'),
    ('ART', 'Fine Arts'),
    ('MUS', 'Music'),
    ('DANCE', 'Dance'),
    ('THEA', 'Theatre Arts'),
    ('PHIL', 'Philosophy'),
    ('LING', 'Linguistics'),
    ('STAT', 'Statistics'),
    ('ANTH', 'Anthropology'),
    ('JMC', 'Journalism and Mass Communication'),
    ('FASH', 'Fashion Design'),
    ('TOUR', 'Tourism Management'),
    ('HM', 'Hotel Management'),
    ('AGRI', 'Agriculture'),
    ('VET', 'Veterinary Science'),
    ('FORE', 'Forestry'),
    ('HORT', 'Horticulture'),
    ('FISH', 'Fisheries Science'),
    ('ANIM', 'Animal Husbandry'),
    ('RURDEV', 'Rural Development'),
    ('CS', 'Computer Science'),
    ('ENG', 'Engineering'),
]

COURSE_CHOICES = [
    ('B.Tech', 'B.Tech'),
    ('M.Tech', 'M.Tech'),
    ('BA', 'Bachelor of Arts'),
    ('MA', 'Master of Arts'),
    ('BSc', 'Bachelor of Science'),
    ('MSC', 'Master of Science'),
    ('BCA', 'Bachelor of Computer Applications'),
    ('MCA', 'Master of Computer Applications'),
    ('BBA', 'Bachelor of Business Administration'),
    ('MBA', 'Master of Business Administration'),
    ('PhD', 'Doctor of Philosophy'),
    ('BCom', 'Bachelor of Commerce'),
    ('MCom', 'Master of Commerce'),
    ('BBA LLB', 'Bachelor of Business Administration and Bachelor of Laws'),
    ('BSc Nursing', 'Bachelor of Science in Nursing'),
    ('GNM', 'General Nursing and Midwifery'),
    ('BHMS', 'Bachelor of Homeopathic Medicine and Surgery'),
    ('BAMS', 'Bachelor of Ayurvedic Medicine and Surgery'),
    ('CS101', 'Intro to Computer Science'),
    ('ENG101', 'Intro to Engineering'),
]

SEM_CHOICES = [
    ('1', '1st'), ('2', '2nd'), ('3', '3rd'), ('4', '4th'), ('5', '5th'), ('6', '6th'),
]

BLOOD_GROUP_CHOICES = [
    ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
    ('O+', 'O+'), ('O-', 'O-'), ('AB+', 'AB+'), ('AB-', 'AB-'),
]

CATEGORY_CHOICES = [
    ('General', 'General'), ('OBC', 'OBC'), ('SC', 'SC'), ('ST', 'ST'), ('EWS', 'EWS'),
]

NATIONALITY_CHOICES = [
    ('Indian', 'Indian'), ('Other', 'Other'),
]

DIVISION_CHOICES = [
    ('A', 'Division A'), ('B', 'Division B'), ('C', 'Division C'), ('D', 'Division D'),
]

STATUS_CHOICES = [
    ('Active', 'Active'), ('Pending', 'Pending'), ('Inactive', 'Inactive'), ('On Leave', 'On Leave'),
]

class Student(models.Model):
    GENDER_CHOICES = GENDER_CHOICES
    STATE_CHOICES = STATE_CHOICES
    CITY_CHOICES = CITY_CHOICES
    DEPARTMENT_CHOICES = DEPARTMENT_CHOICES
    COURSE_CHOICES = COURSE_CHOICES
    SEM_CHOICES = SEM_CHOICES
    BLOOD_GROUP_CHOICES = BLOOD_GROUP_CHOICES
    CATEGORY_CHOICES = CATEGORY_CHOICES
    NATIONALITY_CHOICES = NATIONALITY_CHOICES
    DIVISION_CHOICES = DIVISION_CHOICES
    STATUS_CHOICES = STATUS_CHOICES

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    hostel = models.ForeignKey('authentication.Hostel', on_delete=models.CASCADE, related_name='students', null=True, blank=True)

    student_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    roll = models.CharField(max_length=50, blank=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    dob = models.DateField(blank=True, null=True)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True)
    nationality = models.CharField(max_length=50, choices=NATIONALITY_CHOICES, default='Indian')
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)

    # Parents Information
    father_name = models.CharField(max_length=100, blank=True, null=True)
    mother_name = models.CharField(max_length=100, blank=True, null=True)
    guardian_name = models.CharField(max_length=100, blank=True, null=True)
    guardian_phone = models.CharField(max_length=20, blank=True, null=True)
    guardian_occupation = models.CharField(max_length=100, blank=True, null=True)
    parent_email = models.EmailField(blank=True, null=True)

    # Academic Information
    course = models.CharField(max_length=50, choices=COURSE_CHOICES, blank=True)
    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, blank=True)
    semester = models.CharField(max_length=2, choices=SEM_CHOICES, blank=True)
    division = models.CharField(max_length=5, choices=DIVISION_CHOICES, blank=True)
    admission_date = models.DateField(blank=True, null=True)
    admission_number = models.CharField(max_length=50, blank=True)
    academic_year = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')

    # Address
    address = models.TextField(blank=True) # Address Line 1
    address_line_2 = models.TextField(blank=True)
    state = models.CharField(max_length=50, choices=STATE_CHOICES, blank=True)
    city = models.CharField(max_length=50, choices=CITY_CHOICES, blank=True)
    country = models.CharField(max_length=50, default='India', blank=True)
    pincode = models.CharField(max_length=10, blank=True)

    # Emergency Contact
    emergency_name = models.CharField(max_length=100, blank=True)
    emergency_relation = models.CharField(max_length=50, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    emergency_alt_phone = models.CharField(max_length=20, blank=True)

    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'student'

    def __str__(self):
        return f'{self.name} ({self.email})'

    @property
    def enrollmentNumber(self):
        return self.roll

    @property
    def firstname(self):
        return (self.name or '').split(' ', 1)[0]

    @property
    def lastname(self):
        parts = (self.name or '').split(' ', 1)
        return parts[1] if len(parts) > 1 else ''

    @property
    def is_active(self):
        return self.status == 'Active'

    @property
    def bed_set(self):
        return self.allocated_beds

class Attendance(models.Model):
    ATTENDANCE_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
        ('On Leave', 'On Leave'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=ATTENDANCE_CHOICES, default='Present')
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.name} - {self.date} - {self.status}"


# Django Signals for lifecycle events
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group

@receiver(pre_delete, sender=Student)
def deallocate_student_before_delete(sender, instance, **kwargs):
    from django.apps import apps
    try:
        Bed = apps.get_model('room', 'Bed')
        # Reset any beds assigned to this student, resetting payment fields
        Bed.objects.filter(student=instance).update(
            student=None,
            paid_amount=0,
            remaining_amount=0,
            total_amount=0
        )
    except LookupError:
        pass

@receiver(post_save, sender=Student)
def create_student_user_account(sender, instance, created, **kwargs):
    from authentication.models import Role, UserProfile

    if created:
        user = instance.user
        if not user:
            username = instance.roll.strip() if (instance.roll and instance.roll.strip()) else f"std_{instance.student_id}"
            email = instance.email
            
            # Ensure we don't crash on existing username or email
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='User1234'
                )
                # Add to Students group
                group, _ = Group.objects.get_or_create(name='Students')
                user.groups.add(group)
                
                # Link back using update (to avoid post_save recursion)
                Student.objects.filter(pk=instance.pk).update(user=user)
                
        # Ensure the UserProfile with Student role exists for this user
        if user:
            student_role = Role.objects.filter(name='Student').first()
            UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': student_role}
            )
