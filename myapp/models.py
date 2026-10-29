from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Area(models.Model):
    RISK_LEVEL_CHOICES = (
        ('LOW', 'Low Risk'),
        ('MODERATE', 'Moderate Risk'),
        ('HIGH', 'High Risk'),
        ('CRITICAL', 'Critical Risk'),
    )
    name = models.CharField(max_length=150, unique=True)
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    max_crowd_capacity = models.PositiveIntegerField(help_text="Safe maximum crowd limit")
    current_risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, default='LOW')
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Location(models.Model):
    date = models.DateField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    LOGIN = models.ForeignKey(User, on_delete=models.CASCADE)




class User_Table(models.Model):
    LOGIN = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='registered_users')
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    place = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)




class EmergencyDepartment(models.Model):
    LOGIN = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dept_profile')
    department_name = models.CharField(max_length=200)
    department_code = models.CharField(max_length=50, unique=True)
    contact_number = models.CharField(max_length=15)
    helpline_number = models.CharField(max_length=15)
    department_email = models.CharField(max_length=105)
    office_address = models.TextField()
    assigned_areas = models.ManyToManyField(Area, related_name='assigned_departments', blank=True)
    is_active = models.BooleanField(default=True)




class VolunteerProfile(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    AVAILABILITY_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('ON_DUTY', 'On Duty'),
        ('OFFLINE', 'Offline'),
    )
    LOGIN = models.OneToOneField(User, on_delete=models.CASCADE, related_name='volunteer_profile')
    emergency_department = models.ForeignKey(
        EmergencyDepartment, on_delete=models.SET_NULL, null=True, blank=True, related_name='volunteers'
    )

    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    place = models.CharField(max_length=200)
    photo = models.FileField(upload_to='volunteer_photo/')
    id_proof = models.FileField(upload_to='volunteer_ids/')
    approval_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='OFFLINE')
    join_at = models.DateTimeField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)




class CCTVCamera(models.Model):
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='cameras')
    camera_identifier = models.CharField(max_length=100, unique=True)
    location_details = models.CharField(max_length=255, help_text="Specific junction or entry point")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CrowdDensityLog(models.Model):
    STATUS_CHOICES = (
        ('NORMAL', 'Normal'),
        ('MODERATE', 'Moderate'),
        ('HIGH', 'High Density'),
        ('CRITICAL', 'Overcrowded / Stampede Risk'),
    )
    camera = models.ForeignKey(CCTVCamera, on_delete=models.CASCADE, related_name='density_logs')
    estimated_crowd_count = models.PositiveIntegerField()
    density_map_image = models.ImageField(upload_to='density_maps/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NORMAL')
    recorded_at = models.DateTimeField(auto_now_add=True)



class AnomalyDetectionLog(models.Model):
    ANOMALY_CHOICES = (
        ('STAMPEDE_RUSH', 'Sudden Stampede / Rush'),
        ('ABNORMAL_ACCUMULATION', 'Sudden Crowd Accumulation'),
        ('REVERSE_FLOW', 'Unusual Movement / Counter-Flow'),
        ('TURBULENCE', 'Crowd Turbulence / Panic Movement'),
        ('PROLONGED_CONGESTION', 'Prolonged Bottleneck Congestion'),
    )
    camera = models.ForeignKey(CCTVCamera, on_delete=models.CASCADE, related_name='anomaly_logs')
    anomaly_type = models.CharField(max_length=50, choices=ANOMALY_CHOICES)
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Reconstruction error or model confidence score"
    )
    frame_snapshot = models.ImageField(upload_to='anomalies/')
    video_clip = models.FileField(upload_to='anomaly_clips/', null=True, blank=True)
    detected_at = models.DateTimeField(auto_now_add=True)




class EmergencyAlert(models.Model):
    SEVERITY_CHOICES = (
        ('MEDIUM', 'Medium Attention'),
        ('HIGH', 'High Emergency'),
        ('CRITICAL', 'Critical Red Alert'),
    )
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('UNDER_CONTROL', 'Under Control'),
        ('RESOLVED', 'Resolved'),
    )
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='emergency_alerts')
    emergency_department = models.ForeignKey(
        EmergencyDepartment, on_delete=models.SET_NULL, null=True, blank=True, related_name='department_alerts'
    )
    density_log = models.ForeignKey(CrowdDensityLog, on_delete=models.SET_NULL, null=True, blank=True)
    anomaly_log = models.ForeignKey(AnomalyDetectionLog, on_delete=models.SET_NULL, null=True, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='HIGH')
    title = models.CharField(max_length=200)
    description = models.TextField()
    public_instructions = models.TextField(help_text="Safety guidelines and evacuation instructions for users")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)




class EmergencyTask(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Volunteer Response'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    )
    alert = models.ForeignKey(EmergencyAlert, on_delete=models.CASCADE, related_name='tasks')
    department = models.ForeignKey(EmergencyDepartment, on_delete=models.CASCADE, related_name='assigned_tasks')
    volunteer = models.ForeignKey(VolunteerProfile, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    instruction = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    assigned_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)


class GroundReport(models.Model):
    task = models.ForeignKey(
        EmergencyTask, on_delete=models.SET_NULL, null=True, blank=True, related_name='ground_reports'
    )
    volunteer = models.ForeignKey(VolunteerProfile, on_delete=models.CASCADE, related_name='reports')
    situation_update = models.TextField()
    attached_image = models.ImageField(upload_to='ground_reports/', null=True, blank=True)
    reported_at = models.DateTimeField(auto_now_add=True)






class Feedback(models.Model):
    user = models.ForeignKey(User_Table, on_delete=models.CASCADE, related_name='feedbacks')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)


class Complaint(models.Model):
    user = models.ForeignKey(User_Table, on_delete=models.CASCADE, related_name='complaints')
    subject = models.CharField(max_length=200)
    description = models.TextField()
    admin_response = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, default='Pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)



class Report_Emergency(models.Model):


    USER = models.ForeignKey(User_Table, on_delete=models.CASCADE, related_name='user')
    title = models.CharField(max_length=200)
    description = models.TextField()
    public_instructions = models.TextField(help_text="Safety guidelines and evacuation instructions for users")
    status = models.CharField(max_length=20, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)


class EmergencyInstruction(models.Model):
    title = models.CharField(max_length=200)
    instruction_type = models.CharField(max_length=30, default='GENERAL_ADVISORY')
    severity_level = models.CharField(max_length=20, default='MEDIUM')
    emergency_department = models.ForeignKey(EmergencyDepartment, on_delete=models.SET_NULL, null=True, blank=True)
    summary = models.CharField(max_length=300)
    detailed_steps = models.TextField()
    do_list = models.TextField(blank=True, null=True)
    dont_list = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
