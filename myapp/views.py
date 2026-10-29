from time import timezone

from django.contrib.auth import logout, authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required

# Create your views here.
from myapp.models import *


def logout_page(request):
    logout(request)
    return redirect('/myapp/login_page/')

def login_page(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        ob = authenticate(request, username=username, password=password)

        if ob is not None:

            if ob.groups.filter(name="admin").exists():
                login(request, ob)
                return redirect('/myapp/admin_home/')

            elif ob.groups.filter(name="Emergency").exists():
                login(request, ob)
                return redirect('/myapp/department_home/')


            else:
                messages.warning(
                    request,
                    'Invalid Username and password'
                )
                return redirect('/myapp/login_page/')

        messages.warning(
            request,
            'Invalid Person'
        )
        return redirect('/myapp/login_page/')
    return render(request, 'loginpage.html')


def public_page(request):
    return render(request,'public_page.html')

@login_required(login_url='/myapp/login_page/')
def admin_home(request):
    return render(request,'admin/admin_home.html')

@login_required(login_url='/myapp/login_page/')
def admin_home_sub(request):
    return render(request,'admin/admin_home sub.html')


@login_required(login_url='/myapp/login_page/')
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        if not user.check_password(old_password):
            messages.error(request, 'Old password is incorrect')
            return redirect('/myapp/change_password/')

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match')
            return redirect('/myapp/change_password/')

        if len(new_password) < 8:
            messages.error(request, 'Password must contain at least 8 characters')
            return redirect('/myapp/change_password/')

        user.set_password(new_password)
        user.save()

        update_session_auth_hash(request, user)

        messages.success(request, 'Password changed successfully')
        return redirect('/myapp/login_page/')

    return render(request, 'admin/change_password.html')





import requests


from django.http import JsonResponse
from django.views.decorators.http import require_GET



@require_GET
def area_search_location(request):
    query = request.GET.get("q", "").strip()

    if len(query) < 3:
        return JsonResponse({"results": []})

    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": query,
                "format": "jsonv2",
                "addressdetails": 1,
                "countrycodes": "in",
                "limit": 5,
                "accept-language": "en",
            },
            headers={
                # Replace with a real project contact if possible.
                "User-Agent": "DjangoAreaManagement/1.0"
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        results = []

        for item in data:
            address = item.get("address", {})

            city = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
                or ""
            )

            district = (
                address.get("state_district")
                or address.get("county")
                or ""
            )

            results.append({
                "name": (
                    item.get("name")
                    or item.get("display_name", "").split(",")[0]
                ),
                "formatted": item.get("display_name", ""),
                "city": city,
                "district": district,
                "state": address.get("state", ""),
                "pincode": address.get("postcode", ""),
                "latitude": item.get("lat", ""),
                "longitude": item.get("lon", ""),
            })

        return JsonResponse({"results": results})

    except (requests.RequestException, ValueError):
        return JsonResponse(
            {"error": "Location search failed. Please try again later."},
            status=502,
        )


def admin_manage_area(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        city = request.POST.get("city", "").strip()
        district = request.POST.get("district", "").strip()
        state = request.POST.get("state", "").strip()
        pincode = request.POST.get("pincode", "").strip()
        latitude = request.POST.get("latitude", "").strip()
        longitude = request.POST.get("longitude", "").strip()
        capacity = request.POST.get("max_crowd_capacity", "").strip()
        risk = request.POST.get("current_risk_level", "LOW")
        description = request.POST.get("description", "").strip()

        if not name:
            messages.error(request, "Please select a place.")
        elif not latitude or not longitude:
            messages.error(
                request, "Please search and select a location first."
            )
        elif Area.objects.filter(name__iexact=name).exists():
            messages.error(request, f'Area "{name}" already exists!')
        else:
            try:
                Area.objects.create(
                    name=name,
                    city=city,
                    district=district,
                    state=state,
                    pincode=pincode,
                    latitude=float(latitude),
                    longitude=float(longitude),
                    max_crowd_capacity=int(capacity),
                    current_risk_level=risk,
                    description=description,
                )
                messages.success(request, "New area added successfully!")
                return redirect("admin_manage_area")

            except (ValueError, TypeError):
                messages.error(
                    request,
                    "Please enter a valid crowd capacity and location."
                )

    search_query = request.GET.get("search", "").strip()

    areas = Area.objects.all().order_by("-created_at")

    if search_query:
        areas = areas.filter(
            Q(name__icontains=search_query)
            | Q(city__icontains=search_query)
            | Q(district__icontains=search_query)
        )

    return render(
        request,
        "admin/manage_area.html",
        {
            "areas": areas,
            "search_query": search_query,
        },
    )




from django.shortcuts import render, redirect, get_object_or_404




def admin_edit_area(request, area_id):
    area = get_object_or_404(Area, id=area_id)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        city = request.POST.get("city", "").strip()
        district = request.POST.get("district", "").strip()
        state = request.POST.get("state", "").strip()
        pincode = request.POST.get("pincode", "").strip()
        latitude = request.POST.get("latitude", "").strip()
        longitude = request.POST.get("longitude", "").strip()
        capacity = request.POST.get(
            "max_crowd_capacity", ""
        ).strip()
        risk = request.POST.get(
            "current_risk_level", "LOW"
        )
        description = request.POST.get(
            "description", ""
        ).strip()

        if not name:
            messages.error(request, "Place name is required.")

        elif not latitude or not longitude:
            messages.error(
                request,
                "Please search and select a location first."
            )

        elif Area.objects.filter(
            name__iexact=name
        ).exclude(id=area.id).exists():
            messages.error(
                request,
                f'Area "{name}" already exists!'
            )

        else:
            try:
                area.name = name
                area.city = city
                area.district = district
                area.state = state
                area.pincode = pincode
                area.latitude = float(latitude)
                area.longitude = float(longitude)
                area.max_crowd_capacity = int(capacity)
                area.current_risk_level = risk
                area.description = description

                area.save()

                messages.success(
                    request,
                    f'Area "{area.name}" updated successfully!'
                )
                return redirect("admin_manage_area")

            except (ValueError, TypeError):
                messages.error(
                    request,
                    "Enter valid latitude, longitude and crowd capacity."
                )

    return render(
        request,
        "admin/edit_area.html",
        {"area": area}
    )


def admin_delete_area(request, area_id):
    area = get_object_or_404(Area, id=area_id)
    area_name = area.name
    area.delete()
    messages.success(request, f'Area "{area_name}" deleted successfully!')
    return redirect('/myapp/admin_manage_area/')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum
from .models import User_Table, Area

def manage_users(request):
    search_query = request.GET.get('search', '').strip()
    area_filter = request.GET.get('area', '').strip()

    users = User_Table.objects.select_related('area', 'LOGIN').all()

    if search_query:
        users = users.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(place__icontains=search_query)
        )

    if area_filter:
        users = users.filter(area_id=area_filter)

    areas = Area.objects.all().order_by('name')

    context = {
        'users': users,
        'areas': areas,
        'search_query': search_query,
        'selected_area': area_filter,
        'total_count': users.count()
    }
    return render(request, 'admin/manage_users.html', context)


import re
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.db.models import Q
from .models import EmergencyDepartment, Area


def generate_department_code_from_name(dept_name):

    words = re.findall(r'[A-Za-z0-9]+', dept_name)

    if len(words) >= 2:
        prefix = "".join([w[0].upper() for w in words[:4]])
    elif words:
        prefix = words[0][:3].upper()
    else:
        prefix = "ED"

    while True:
        random_digits = random.randint(100000, 999999)
        code = f"{prefix}-{random_digits}"
        if not EmergencyDepartment.objects.filter(department_code=code).exists():
            return code


def manage_departments(request):
    areas = Area.objects.all().order_by('name')
    search_query = request.GET.get('search', '').strip()

    if request.method == 'POST':
        department_name = request.POST.get('department_name', '').strip()
        contact_number = request.POST.get('contact_number', '').strip()
        helpline_number = request.POST.get('helpline_number', '').strip()
        office_address = request.POST.get('office_address', '').strip()
        department_email = request.POST.get('department_email', '').strip()
        selected_areas = request.POST.getlist('assigned_areas')

        if User.objects.filter(username=department_email).exists():
            messages.error(request, f'Username "{department_email}" already exists.')
            return redirect('/myapp/manage_departments/')

        if User.objects.filter(email=department_email).exists():
            messages.error(request, f'Email "{department_email}" already exists.')
            return redirect('/myapp/manage_departments/')

        auto_department_code = generate_department_code_from_name(department_name)

        user = User.objects.create_user(
            username=department_email,
            password=contact_number,
            email=department_email
        )

        group, _ = Group.objects.get_or_create(name="Emergency")
        user.groups.add(group)

        dept = EmergencyDepartment(
            LOGIN=user,
            department_name=department_name,
            department_code=auto_department_code,
            contact_number=contact_number,
            helpline_number=helpline_number,
            office_address=office_address,
            department_email=department_email,
            is_active=True
        )
        dept.save()

        if selected_areas:
            dept.assigned_areas.set(selected_areas)

        messages.success(request,
                         f'Department "{department_name}" added successfully with Code: {auto_department_code}')
        return redirect('/myapp/manage_departments/')

    departments = EmergencyDepartment.objects.select_related('LOGIN').prefetch_related('assigned_areas').all()
    if search_query:
        departments = departments.filter(
            Q(department_name__icontains=search_query) |
            Q(department_code__icontains=search_query) |
            Q(contact_number__icontains=search_query) |
            Q(LOGIN__email__icontains=search_query)
        )

    context = {
        'areas': areas,
        'departments': departments,
        'search_query': search_query,
        'total_count': departments.count(),
    }
    return render(request, 'admin/manage_departments.html', context)

def edit_department(request, dept_id):
    dept = get_object_or_404(EmergencyDepartment, id=dept_id)
    areas = Area.objects.all().order_by('name')

    if request.method == 'POST':
        department_name = request.POST.get('department_name', '').strip()
        contact_number = request.POST.get('contact_number', '').strip()
        helpline_number = request.POST.get('helpline_number', '').strip()
        office_address = request.POST.get('office_address', '').strip()
        department_email = request.POST.get('department_email', '').strip()
        is_active = request.POST.get('is_active') == 'True'
        selected_areas = request.POST.getlist('assigned_areas')

        if User.objects.filter(email=department_email).exclude(id=dept.LOGIN.id).exists():
            messages.error(request, f'Email "{department_email}" is already in use by another user.')
            return redirect(f'/myapp/edit_department/{dept.id}/')

        dept.LOGIN.email = department_email
        dept.LOGIN.username = department_email
        dept.LOGIN.save()

        dept.department_name = department_name
        dept.contact_number = contact_number
        dept.helpline_number = helpline_number
        dept.office_address = office_address
        dept.is_active = is_active
        dept.save()

        dept.assigned_areas.set(selected_areas)

        messages.success(request, f'Department "{department_name}" updated successfully.')
        return redirect('/myapp/manage_departments/')

    assigned_area_ids = dept.assigned_areas.values_list('id', flat=True)

    context = {
        'dept': dept,
        'areas': areas,
        'assigned_area_ids': assigned_area_ids,
    }
    return render(request, 'admin/edit_department.html', context)

def delete_department(request, dept_id):
    dept = get_object_or_404(EmergencyDepartment, id=dept_id)
    dept_name = dept.department_name

    if dept.LOGIN:
        dept.LOGIN.delete()
    else:
        dept.delete()

    messages.success(request, f'Department "{dept_name}" deleted successfully.')
    return redirect('/myapp/manage_departments/')




def manage_volunteers(request):
    departments = EmergencyDepartment.objects.filter(is_active=True).prefetch_related('assigned_areas').order_by(
        'department_name')

    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    dept_filter = request.GET.get('dept', '').strip()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        place = request.POST.get('place', '').strip()
        dept_id = request.POST.get('emergency_department')
        approval_status = request.POST.get('approval_status', 'APPROVED')
        availability_status = request.POST.get('availability_status', 'AVAILABLE')
        photo = request.FILES.get('photo')
        id_proof = request.FILES.get('id_proof')

        if User.objects.filter(username=email).exists():
            messages.error(request, f'Username / Email "{email}" already exists.')
            return redirect('/myapp/manage_volunteers/')

        if User.objects.filter(email=email).exists():
            messages.error(request, f'Email "{email}" is already registered.')
            return redirect('/myapp/manage_volunteers/')

        user = User.objects.create_user(
            username=email,
            password=phone,
            email=email
        )

        group, _ = Group.objects.get_or_create(name="Volunteer")
        user.groups.add(group)

        vol = VolunteerProfile(
            LOGIN=user,
            name=name,
            email=email,
            phone=phone,
            place=place,
            emergency_department_id=dept_id if dept_id else None,
            approval_status=approval_status,
            availability_status=availability_status,
            join_at=timezone.now(),
            photo=photo,
            id_proof=id_proof
        )
        vol.save()

        messages.success(request, f'Volunteer "{name}" added successfully.')
        return redirect('/myapp/manage_volunteers/')

    volunteers = VolunteerProfile.objects.select_related('LOGIN', 'emergency_department').prefetch_related(
        'emergency_department__assigned_areas').all()

    if search_query:
        volunteers = volunteers.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(place__icontains=search_query) |
            Q(emergency_department__department_name__icontains=search_query)
        )

    if status_filter:
        volunteers = volunteers.filter(approval_status=status_filter)

    if dept_filter:
        volunteers = volunteers.filter(emergency_department_id=dept_filter)

    context = {
        'volunteers': volunteers,
        'departments': departments,
        'search_query': search_query,
        'status_filter': status_filter,
        'dept_filter': dept_filter,
        'total_count': volunteers.count(),
    }
    return render(request, 'admin/manage_volunteers.html', context)


def edit_volunteer(request, vol_id):
    vol = get_object_or_404(VolunteerProfile, id=vol_id)
    departments = EmergencyDepartment.objects.filter(is_active=True).prefetch_related('assigned_areas').order_by(
        'department_name')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        place = request.POST.get('place', '').strip()
        dept_id = request.POST.get('emergency_department')
        approval_status = request.POST.get('approval_status')
        availability_status = request.POST.get('availability_status')

        if User.objects.filter(email=email).exclude(id=vol.LOGIN.id).exists():
            messages.error(request, f'Email "{email}" is already used by another account.')
            return redirect(f'/myapp/edit_volunteer/{vol.id}/')

        vol.LOGIN.email = email
        vol.LOGIN.username = email
        vol.LOGIN.save()

        vol.name = name
        vol.email = email
        vol.phone = phone
        vol.place = place
        vol.emergency_department_id = dept_id if dept_id else None
        vol.approval_status = approval_status
        vol.availability_status = availability_status

        if request.FILES.get('photo'):
            vol.photo = request.FILES.get('photo')

        if request.FILES.get('id_proof'):
            vol.id_proof = request.FILES.get('id_proof')

        vol.save()

        messages.success(request, f'Volunteer "{name}" updated successfully.')
        return redirect('/myapp/manage_volunteers/')

    context = {
        'vol': vol,
        'departments': departments,
    }
    return render(request, 'admin/edit_volunteer.html', context)


def delete_volunteer(request, vol_id):
    vol = get_object_or_404(VolunteerProfile, id=vol_id)
    name = vol.name
    if vol.LOGIN:
        vol.LOGIN.delete()
    else:
        vol.delete()
    messages.success(request, f'Volunteer "{name}" deleted successfully.')
    return redirect('/myapp/manage_volunteers/')


import re
import random
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
from .models import CCTVCamera, Area


def generate_camera_identifier(area_name):
    words = re.findall(r'[A-Za-z0-9]+', area_name)
    prefix = "".join([w[0].upper() for w in words[:3]]) if words else "ZONE"
    while True:
        digits = random.randint(1000, 9999)
        identifier = f"CAM-{prefix}-{digits}"
        if not CCTVCamera.objects.filter(camera_identifier=identifier).exists():
            return identifier


def search_camera_sublocation(request):

    area_id = request.GET.get('area_id', '').strip()
    query = request.GET.get('q', '').strip()

    if not query or len(query) < 2:
        return JsonResponse({'results': []})

    area_context = ""
    viewbox_param = ""

    if area_id:
        try:
            area = Area.objects.get(id=area_id)
            parts = [query]
            if area.name and area.name.lower() not in query.lower():
                parts.append(area.name)
            if hasattr(area, 'district') and area.district:
                parts.append(area.district)
            if hasattr(area, 'state') and area.state:
                parts.append(area.state)

            search_query = ", ".join(parts)

            if area.latitude and area.longitude:
                lat = float(area.latitude)
                lon = float(area.longitude)
                delta = 0.15
                viewbox_param = f"&viewbox={lon-delta},{lat+delta},{lon+delta},{lat-delta}&bounded=1"
        except Area.DoesNotExist:
            search_query = query
    else:
        search_query = query

    url = f"https://nominatim.openstreetmap.org/search?q={search_query}&format=json&addressdetails=1&limit=5&countrycodes=in{viewbox_param}"
    headers = {'User-Agent': 'CrowdSenseSurveillance/1.0'}

    try:
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        results = []
        for item in data:
            results.append({
                'display_name': item.get('display_name'),
                'name': item.get('name') or item.get('display_name').split(',')[0],
                'latitude': item.get('lat'),
                'longitude': item.get('lon')
            })
        return JsonResponse({'results': results})
    except Exception:
        return JsonResponse({'results': []})


def manage_cameras(request):
    areas = Area.objects.all().order_by('name')
    search_query = request.GET.get('search', '').strip()

    if request.method == 'POST':
        area_id = request.POST.get('area')
        location_details = request.POST.get('location_details', '').strip()
        lat = request.POST.get('latitude', '').strip()
        lon = request.POST.get('longitude', '').strip()

        area = get_object_or_404(Area, id=area_id)
        camera_id = generate_camera_identifier(area.name)

        camera = CCTVCamera(
            area=area,
            camera_identifier=camera_id,
            location_details=location_details,
            latitude=lat if lat else area.latitude,
            longitude=lon if lon else area.longitude
        )
        camera.save()

        messages.success(request, f'CCTV Unit "{camera_id}" enrolled successfully.')
        return redirect('/myapp/manage_cameras/')

    cameras = CCTVCamera.objects.select_related('area').all().order_by('-created_at')
    if search_query:
        cameras = cameras.filter(
            Q(camera_identifier__icontains=search_query) |
            Q(location_details__icontains=search_query) |
            Q(area__name__icontains=search_query)
        )

    context = {
        'cameras': cameras,
        'areas': areas,
        'search_query': search_query,
        'total_count': cameras.count(),
    }
    return render(request, 'admin/manage_cameras.html', context)




def edit_camera(request, cam_id):
    cam = get_object_or_404(CCTVCamera, id=cam_id)
    areas = Area.objects.all().order_by('name')

    if request.method == 'POST':
        area_id = request.POST.get('area')
        location_details = request.POST.get('location_details', '').strip()
        lat = request.POST.get('latitude', '').strip()
        lon = request.POST.get('longitude', '').strip()

        area = get_object_or_404(Area, id=area_id)

        cam.area = area
        cam.location_details = location_details
        cam.latitude = lat if lat else area.latitude
        cam.longitude = lon if lon else area.longitude
        cam.save()

        messages.success(request, f'CCTV Unit "{cam.camera_identifier}" updated successfully.')
        return redirect('/myapp/manage_cameras/')

    context = {
        'cam': cam,
        'areas': areas,
    }
    return render(request, 'admin/edit_camera.html', context)


def delete_camera(request, cam_id):
    cam = get_object_or_404(CCTVCamera, id=cam_id)
    identifier = cam.camera_identifier
    cam.delete()
    messages.success(request, f'CCTV Unit "{identifier}" removed successfully.')
    return redirect('/myapp/manage_cameras/')


from django.db.models import Max, Avg
from django.utils.dateparse import parse_date

def density_reports(request):
    camera_filter = request.GET.get('camera', '').strip()
    status_filter = request.GET.get('status', '').strip()
    area_filter = request.GET.get('area', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    logs = CrowdDensityLog.objects.select_related('camera', 'camera__area').order_by('-recorded_at')

    if area_filter:
        logs = logs.filter(camera__area_id=area_filter)

    if camera_filter:
        logs = logs.filter(camera_id=camera_filter)

    if status_filter:
        logs = logs.filter(status=status_filter)

    if date_from:
        d_from = parse_date(date_from)
        if d_from:
            logs = logs.filter(recorded_at__date__gte=d_from)

    if date_to:
        d_to = parse_date(date_to)
        if d_to:
            logs = logs.filter(recorded_at__date__lte=d_to)

    total_logs = logs.count()
    peak_count = logs.aggregate(Max('estimated_crowd_count'))['estimated_crowd_count__max'] or 0
    avg_count = int(logs.aggregate(Avg('estimated_crowd_count'))['estimated_crowd_count__avg'] or 0)
    critical_alerts = logs.filter(status='CRITICAL').count()

    status_counts = {
        'NORMAL': logs.filter(status='NORMAL').count(),
        'MODERATE': logs.filter(status='MODERATE').count(),
        'HIGH': logs.filter(status='HIGH').count(),
        'CRITICAL': logs.filter(status='CRITICAL').count(),
    }

    cameras = CCTVCamera.objects.select_related('area').all().order_by('camera_identifier')
    areas = Area.objects.all().order_by('name')

    context = {
        'logs': logs[:150],
        'cameras': cameras,
        'areas': areas,
        'camera_filter': camera_filter,
        'status_filter': status_filter,
        'area_filter': area_filter,
        'date_from': date_from,
        'date_to': date_to,
        'total_logs': total_logs,
        'peak_count': peak_count,
        'avg_count': avg_count,
        'critical_alerts': critical_alerts,
        'status_counts': status_counts,
    }
    return render(request, 'admin/density_reports.html', context)




def view_anomalies(request):
    type_filter = request.GET.get('type', '').strip()
    area_filter = request.GET.get('area', '').strip()
    camera_filter = request.GET.get('camera', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    logs = AnomalyDetectionLog.objects.select_related('camera', 'camera__area').order_by('-detected_at')

    if type_filter:
        logs = logs.filter(anomaly_type=type_filter)

    if area_filter:
        logs = logs.filter(camera__area_id=area_filter)

    if camera_filter:
        logs = logs.filter(camera_id=camera_filter)

    if date_from:
        d_from = parse_date(date_from)
        if d_from:
            logs = logs.filter(detected_at__date__gte=d_from)

    if date_to:
        d_to = parse_date(date_to)
        if d_to:
            logs = logs.filter(detected_at__date__lte=d_to)

    total_anomalies = logs.count()
    peak_confidence = logs.aggregate(Max('confidence_score'))['confidence_score__max'] or 0.0
    avg_confidence = logs.aggregate(Avg('confidence_score'))['confidence_score__avg'] or 0.0

    high_threat_count = logs.filter(anomaly_type__in=['STAMPEDE_RUSH', 'TURBULENCE']).count()

    cameras = CCTVCamera.objects.select_related('area').all().order_by('camera_identifier')
    areas = Area.objects.all().order_by('name')

    context = {
        'logs': logs[:150],
        'cameras': cameras,
        'areas': areas,
        'type_filter': type_filter,
        'area_filter': area_filter,
        'camera_filter': camera_filter,
        'date_from': date_from,
        'date_to': date_to,
        'total_anomalies': total_anomalies,
        'peak_confidence': peak_confidence,
        'avg_confidence': avg_confidence,
        'high_threat_count': high_threat_count,
        'anomaly_choices': AnomalyDetectionLog.ANOMALY_CHOICES,
    }
    return render(request, 'admin/view_anomalies.html', context)


def view_alerts(request):
    status_filter = request.GET.get('status', '').strip()
    severity_filter = request.GET.get('severity', '').strip()
    area_filter = request.GET.get('area', '').strip()
    dept_filter = request.GET.get('dept', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    alerts = EmergencyAlert.objects.select_related(
        'area', 'emergency_department', 'density_log', 'anomaly_log', 'density_log__camera', 'anomaly_log__camera'
    ).order_by('-created_at')

    if status_filter:
        alerts = alerts.filter(status=status_filter)
    if severity_filter:
        alerts = alerts.filter(severity=severity_filter)
    if area_filter:
        alerts = alerts.filter(area_id=area_filter)
    if dept_filter:
        alerts = alerts.filter(emergency_department_id=dept_filter)
    if date_from:
        d_from = parse_date(date_from)
        if d_from:
            alerts = alerts.filter(created_at__date__gte=d_from)
    if date_to:
        d_to = parse_date(date_to)
        if d_to:
            alerts = alerts.filter(created_at__date__lte=d_to)

    total_alerts = alerts.count()
    active_critical = alerts.filter(status='ACTIVE', severity='CRITICAL').count()
    active_count = alerts.filter(status='ACTIVE').count()
    under_control_count = alerts.filter(status='UNDER_CONTROL').count()
    resolved_count = alerts.filter(status='RESOLVED').count()

    areas = Area.objects.all().order_by('name')
    departments = EmergencyDepartment.objects.filter(is_active=True).order_by('department_name')

    context = {
        'alerts': alerts[:150],
        'areas': areas,
        'departments': departments,
        'status_filter': status_filter,
        'severity_filter': severity_filter,
        'area_filter': area_filter,
        'dept_filter': dept_filter,
        'date_from': date_from,
        'date_to': date_to,
        'total_alerts': total_alerts,
        'active_critical': active_critical,
        'active_count': active_count,
        'under_control_count': under_control_count,
        'resolved_count': resolved_count,
        'severity_choices': EmergencyAlert.SEVERITY_CHOICES,
        'status_choices': EmergencyAlert.STATUS_CHOICES,
    }
    return render(request, 'admin/view_alerts.html', context)


def update_alert_status(request, alert_id):
    if request.method == 'POST':
        alert = get_object_or_404(EmergencyAlert, id=alert_id)
        new_status = request.POST.get('status')
        if new_status in dict(EmergencyAlert.STATUS_CHOICES):
            alert.status = new_status
            alert.save()
            messages.success(request, f'Alert "{alert.title}" status changed to {alert.get_status_display()}.')
        else:
            messages.error(request, 'Invalid alert status selected.')
    return redirect(request,'/myapp/view_alerts/')


def view_complaints(request):
    status_filter = request.GET.get('status', '').strip()
    search_query = request.GET.get('search', '').strip()

    complaints = Complaint.objects.select_related('user', 'user__area').order_by('-submitted_at')

    if status_filter:
        complaints = complaints.filter(status=status_filter)

    if search_query:
        complaints = complaints.filter(
            Q(subject__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(user__name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__phone__icontains=search_query)
        )

    total_complaints = complaints.count()
    pending_count = Complaint.objects.filter(status='Pending').count()
    replied_count = Complaint.objects.filter(status='Replied').count()

    context = {
        'complaints': complaints[:150],
        'status_filter': status_filter,
        'search_query': search_query,
        'total_complaints': total_complaints,
        'pending_count': pending_count,
        'replied_count': replied_count,
    }
    return render(request, 'admin/view_complaints.html', context)

from django.utils import timezone
def reply_complaint(request, complaint_id):
    if request.method == 'POST':
        complaint = get_object_or_404(Complaint, id=complaint_id)
        admin_reply = request.POST.get('admin_response', '').strip()

        if not admin_reply:
            messages.error(request, 'Reply text cannot be empty.')
            return redirect('/myapp/view_complaints/')

        complaint.admin_response = admin_reply
        complaint.status = 'Replied'
        complaint.resolved_at = timezone.now()
        complaint.save()

        messages.success(request, f'Reply sent to {complaint.user.name} and status updated to Replied.')
    return redirect('/myapp/view_complaints/')




def view_feedback(request):
    rating_filter = request.GET.get('rating', '').strip()
    search_query = request.GET.get('search', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    feedbacks = Feedback.objects.select_related('user', 'user__area').order_by('-submitted_at')

    if rating_filter:
        feedbacks = feedbacks.filter(rating=rating_filter)

    if search_query:
        feedbacks = feedbacks.filter(
            Q(subject__icontains=search_query) |
            Q(message__icontains=search_query) |
            Q(user__name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )

    if date_from:
        d_from = parse_date(date_from)
        if d_from:
            feedbacks = feedbacks.filter(submitted_at__date__gte=d_from)

    if date_to:
        d_to = parse_date(date_to)
        if d_to:
            feedbacks = feedbacks.filter(submitted_at__date__lte=d_to)

    total_feedbacks = feedbacks.count()
    avg_score = feedbacks.aggregate(Avg('rating'))['rating__avg'] or 0.0

    star_distribution = []
    for star in range(5, 0, -1):
        count = feedbacks.filter(rating=star).count()
        percentage = round((count / total_feedbacks * 100), 1) if total_feedbacks > 0 else 0.0
        star_distribution.append({
            'stars': star,
            'count': count,
            'percentage': percentage
        })

    high_ratings = feedbacks.filter(rating__gte=4).count()
    satisfaction_rate = round((high_ratings / total_feedbacks * 100), 1) if total_feedbacks > 0 else 0.0

    context = {
        'feedbacks': feedbacks[:150],
        'total_feedbacks': total_feedbacks,
        'avg_score': round(avg_score, 1),
        'satisfaction_rate': satisfaction_rate,
        'star_distribution': star_distribution,
        'rating_filter': rating_filter,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'admin/view_feedback.html', context)




# department===========================


@login_required
def department_home(request):
    dept = get_object_or_404(EmergencyDepartment.objects.prefetch_related('assigned_areas'), LOGIN=request.user)

    assigned_areas = dept.assigned_areas.all()
    assigned_area_ids = assigned_areas.values_list('id', flat=True)

    total_areas_count = assigned_areas.count()

    volunteers = VolunteerProfile.objects.filter(emergency_department=dept)
    total_vols = volunteers.count()
    on_duty_vols = volunteers.filter(availability_status='ON_DUTY').count()
    available_vols = volunteers.filter(availability_status='AVAILABLE').count()

    active_alerts = EmergencyAlert.objects.filter(
        Q(emergency_department=dept) | Q(area_id__in=assigned_area_ids),
        status__in=['ACTIVE', 'UNDER_CONTROL']
    ).select_related('area', 'anomaly_log').order_by('-created_at')

    recent_density_logs = CrowdDensityLog.objects.filter(
        camera__area_id__in=assigned_area_ids
    ).select_related('camera', 'camera__area').order_by('-recorded_at')[:8]

    recent_anomalies = AnomalyDetectionLog.objects.filter(
        camera__area_id__in=assigned_area_ids
    ).select_related('camera', 'camera__area').order_by('-detected_at')[:6]

    resolved_incidents = EmergencyAlert.objects.filter(
        Q(emergency_department=dept) | Q(area_id__in=assigned_area_ids),
        status='RESOLVED'
    ).select_related('area').order_by('-updated_at')[:5]

    context = {
        'dept': dept,
        'assigned_areas': assigned_areas,
        'total_areas_count': total_areas_count,
        'total_vols': total_vols,
        'on_duty_vols': on_duty_vols,
        'available_vols': available_vols,
        'active_alerts': active_alerts,
        'recent_density_logs': recent_density_logs,
        'recent_anomalies': recent_anomalies,
        'resolved_incidents': resolved_incidents,
    }
    return render(request, 'dept/department_home.html', context)




def dept_manage_instructions(request):
    dept = get_object_or_404(
        EmergencyDepartment.objects.prefetch_related('assigned_areas'),
        LOGIN_id=request.user.id
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_instruction':
            title = request.POST.get('title', '').strip()
            instruction_type = request.POST.get('instruction_type', 'GENERAL_ADVISORY').strip()
            severity_level = request.POST.get('severity_level', 'MEDIUM').strip()
            summary = request.POST.get('summary', '').strip()
            detailed_steps = request.POST.get('detailed_steps', '').strip()
            do_list = request.POST.get('do_list', '').strip()
            dont_list = request.POST.get('dont_list', '').strip()

            if not title or not summary or not detailed_steps:
                messages.error(request, 'Please complete the title, summary, and detailed protocol steps.')
            else:
                EmergencyInstruction.objects.create(
                    emergency_department=dept,
                    title=title,
                    instruction_type=instruction_type,
                    severity_level=severity_level,
                    summary=summary,
                    detailed_steps=detailed_steps,
                    do_list=do_list or None,
                    dont_list=dont_list or None,
                )
                messages.success(request, f'Tactical SOP "{title}" published successfully.')
                return redirect('/myapp/dept_manage_instructions/')

    severity_filter = request.GET.get('severity', '').strip()
    type_filter = request.GET.get('type', '').strip()
    search_query = request.GET.get('search', '').strip()

    instructions = EmergencyInstruction.objects.filter(
        emergency_department=dept
    ).order_by('-created_at')

    if severity_filter:
        instructions = instructions.filter(severity_level=severity_filter)
    if type_filter:
        instructions = instructions.filter(instruction_type=type_filter)
    if search_query:
        instructions = instructions.filter(
            Q(title__icontains=search_query) |
            Q(summary__icontains=search_query) |
            Q(detailed_steps__icontains=search_query)
        )

    total_count = EmergencyInstruction.objects.filter(emergency_department=dept).count()
    critical_count = EmergencyInstruction.objects.filter(emergency_department=dept, severity_level='CRITICAL').count()
    high_count = EmergencyInstruction.objects.filter(emergency_department=dept, severity_level='HIGH').count()

    context = {
        'dept': dept,
        'instructions': instructions,
        'total_count': total_count,
        'critical_count': critical_count,
        'high_count': high_count,
        'severity_filter': severity_filter,
        'type_filter': type_filter,
        'search_query': search_query,
    }
    return render(request, 'dept/dept_manage_instructions.html', context)


def dept_delete_instruction(request, instruction_id):
    dept = get_object_or_404(EmergencyDepartment, LOGIN_id=request.user.id)
    instruction = get_object_or_404(EmergencyInstruction, id=instruction_id, emergency_department=dept)

    if request.method == 'POST':
        title = instruction.title
        instruction.delete()
        messages.success(request, f'Directive "{title}" was permanently purged.')

    return redirect('/myapp/dept_manage_instructions/')



def dept_view_user_reports(request):
    dept = get_object_or_404(
        EmergencyDepartment.objects.prefetch_related('assigned_areas'),
        LOGIN_id=request.user.id
    )

    assigned_areas = dept.assigned_areas.all()

    status_filter = request.GET.get('status', '').strip()
    area_filter = request.GET.get('area', '').strip()
    search_query = request.GET.get('search', '').strip()
    date_filter = request.GET.get('date', '').strip()

    reports_qs = Report_Emergency.objects.filter(
        USER__area__in=assigned_areas
    ).select_related('USER', 'USER__area').order_by('-created_at')

    if status_filter:
        reports_qs = reports_qs.filter(status=status_filter)
    if area_filter:
        reports_qs = reports_qs.filter(USER__area_id=area_filter)
    if date_filter:
        d = parse_date(date_filter)
        if d:
            reports_qs = reports_qs.filter(created_at__date=d)
    if search_query:
        reports_qs = reports_qs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(USER__name__icontains=search_query) |
            Q(USER__phone__icontains=search_query)
        )

    base_dept_reports = Report_Emergency.objects.filter(USER__area__in=assigned_areas)
    total_reports = base_dept_reports.count()
    active_reports = base_dept_reports.filter(status='ACTIVE').count()
    under_control_reports = base_dept_reports.filter(status='UNDER_CONTROL').count()
    resolved_reports = base_dept_reports.filter(status='RESOLVED').count()

    context = {
        'dept': dept,
        'assigned_areas': assigned_areas,
        'reports': reports_qs[:100],
        'total_reports': total_reports,
        'active_reports': active_reports,
        'under_control_reports': under_control_reports,
        'resolved_reports': resolved_reports,
        'status_filter': status_filter,
        'area_filter': area_filter,
        'search_query': search_query,
        'date_filter': date_filter,
    }
    return render(request, 'dept/dept_view_user_reports.html', context)


def dept_update_user_report_status(request, report_id):
    dept = get_object_or_404(EmergencyDepartment, LOGIN_id=request.user.id)
    assigned_areas = dept.assigned_areas.all()

    report = get_object_or_404(
        Report_Emergency,
        id=report_id,
        USER__area__in=assigned_areas
    )

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'acknowledge':
            report.status = 'UNDER_CONTROL'
            report.save()
            messages.success(request, f'Incident reported by {report.USER.name} acknowledged and placed under control.')
        elif action == 'resolve':
            report.status = 'RESOLVED'
            report.save()
            messages.success(request, f'Incident reported by {report.USER.name} marked as resolved.')

    return redirect('/myapp/dept_view_user_reports/')

@login_required
def dept_view_profile(request):
    dept = get_object_or_404(
        EmergencyDepartment.objects.prefetch_related('assigned_areas'),
        LOGIN_id=request.user.id
    )

    assigned_areas = dept.assigned_areas.all()
    assigned_area_ids = assigned_areas.values_list('id', flat=True)

    volunteer_count = VolunteerProfile.objects.filter(emergency_department=dept).count()
    active_emergencies_count = EmergencyAlert.objects.filter(
        emergency_department=dept,
        status__in=['ACTIVE', 'UNDER_CONTROL']
    ).count()

    context = {
        'dept': dept,
        'assigned_areas': assigned_areas,
        'volunteer_count': volunteer_count,
        'active_emergencies_count': active_emergencies_count,
    }
    return render(request, 'dept/dept_view_profile.html', context)


@login_required(login_url='/myapp/login_page/')
def dept_change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        if not user.check_password(old_password):
            messages.error(request, 'Old password is incorrect')
            return redirect('/myapp/dept_change_password/')

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match')
            return redirect('/myapp/dept_change_password/')

        if len(new_password) < 8:
            messages.error(request, 'Password must contain at least 8 characters')
            return redirect('/myapp/dept_change_password/')

        user.set_password(new_password)
        user.save()

        update_session_auth_hash(request, user)

        messages.success(request, 'Password changed successfully')
        return redirect('/myapp/login_page/')

    return render(request, 'dept/change_password.html')



from django.db.models import Count, Q
@login_required
def dept_view_areas(request):
    dept = get_object_or_404(
        EmergencyDepartment.objects.prefetch_related(
            'assigned_areas',
            'assigned_areas__cameras'
        ),
        LOGIN_id=request.user.id
    )

    search_query = request.GET.get('search', '').strip()
    risk_filter = request.GET.get('risk', '').strip()

    areas = dept.assigned_areas.annotate(
        camera_count=Count('cameras')
    ).all().order_by('name')

    if search_query:
        areas = areas.filter(
            Q(name__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(district__icontains=search_query)
        )

    if risk_filter:
        areas = areas.filter(current_risk_level=risk_filter)

    total_assigned_areas = dept.assigned_areas.count()
    high_risk_count = dept.assigned_areas.filter(current_risk_level__in=['HIGH', 'Critical', 'High']).count()

    context = {
        'dept': dept,
        'areas': areas,
        'total_assigned_areas': total_assigned_areas,
        'high_risk_count': high_risk_count,
        'search_query': search_query,
        'risk_filter': risk_filter,
    }
    return render(request, 'dept/dept_view_areas.html', context)




@login_required
def dept_live_density_console(request):
    dept = get_object_or_404(
        EmergencyDepartment.objects.prefetch_related('assigned_areas'),
        LOGIN_id=request.user.id
    )

    assigned_areas = dept.assigned_areas.all()
    assigned_area_ids = assigned_areas.values_list('id', flat=True)

    area_filter = request.GET.get('area', '').strip()
    status_filter = request.GET.get('status', '').strip()

    base_logs = CrowdDensityLog.objects.filter(
        camera__area_id__in=assigned_area_ids
    ).select_related('camera', 'camera__area')

    if area_filter:
        base_logs = base_logs.filter(camera__area_id=area_filter)
    if status_filter:
        base_logs = base_logs.filter(status=status_filter)

    cameras = CCTVCamera.objects.filter(
        area_id__in=assigned_area_ids
    ).select_related('area').order_by('camera_identifier')

    active_camera_feeds = []
    total_live_crowd_count = 0

    for cam in cameras:
        latest_log = CrowdDensityLog.objects.filter(camera=cam).order_by('-recorded_at').first()
        if latest_log:
            total_live_crowd_count += latest_log.estimated_crowd_count
        active_camera_feeds.append({
            'camera': cam,
            'log': latest_log,
        })

    sector_analytics = []
    for area in assigned_areas:
        area_cams = cameras.filter(area=area)
        area_count = 0
        latest_logs = []
        for c in area_cams:
            l = CrowdDensityLog.objects.filter(camera=c).order_by('-recorded_at').first()
            if l:
                area_count += l.estimated_crowd_count
                latest_logs.append(l)

        load_percentage = round((area_count / area.max_crowd_capacity * 100), 1) if area.max_crowd_capacity else 0

        sector_analytics.append({
            'area': area,
            'camera_count': area_cams.count(),
            'current_headcount': area_count,
            'capacity': area.max_crowd_capacity,
            'load_percentage': min(load_percentage, 100.0),
            'raw_percentage': load_percentage,
        })

    total_allocated_capacity = assigned_areas.aggregate(Sum('max_crowd_capacity'))['max_crowd_capacity__sum'] or 1
    overall_load_percentage = round((total_live_crowd_count / total_allocated_capacity * 100), 1)
    critical_alerts = base_logs.filter(status='CRITICAL').count()

    stream_logs = base_logs.order_by('-recorded_at')[:80]

    context = {
        'dept': dept,
        'assigned_areas': assigned_areas,
        'cameras': cameras,
        'active_camera_feeds': active_camera_feeds,
        'sector_analytics': sector_analytics,
        'stream_logs': stream_logs,
        'total_live_crowd_count': total_live_crowd_count,
        'total_allocated_capacity': total_allocated_capacity,
        'overall_load_percentage': overall_load_percentage,
        'critical_alerts': critical_alerts,
        'area_filter': area_filter,
        'status_filter': status_filter,
    }
    return render(request, 'dept/dept_live_density_console.html', context)


@login_required
def dept_density_maps(request):
    dept = get_object_or_404(
        EmergencyDepartment.objects.prefetch_related('assigned_areas'),
        LOGIN_id=request.user.id
    )

    assigned_areas = dept.assigned_areas.all()
    assigned_area_ids = assigned_areas.values_list('id', flat=True)

    area_filter = request.GET.get('area', '').strip()
    status_filter = request.GET.get('status', '').strip()
    camera_filter = request.GET.get('camera', '').strip()

    maps_query = CrowdDensityLog.objects.filter(
        camera__area_id__in=assigned_area_ids,
        density_map_image__isnull=False
    ).exclude(density_map_image='').select_related('camera', 'camera__area').order_by('-recorded_at')

    if area_filter:
        maps_query = maps_query.filter(camera__area_id=area_filter)

    if camera_filter:
        maps_query = maps_query.filter(camera_id=camera_filter)

    if status_filter:
        maps_query = maps_query.filter(status=status_filter)

    cameras = CCTVCamera.objects.filter(area_id__in=assigned_area_ids).select_related('area').order_by('camera_identifier')

    total_maps = maps_query.count()
    critical_maps = maps_query.filter(status='CRITICAL').count()
    high_maps = maps_query.filter(status='HIGH').count()
    moderate_maps = maps_query.filter(status='MODERATE').count()

    context = {
        'dept': dept,
        'assigned_areas': assigned_areas,
        'cameras': cameras,
        'density_maps': maps_query[:60],
        'total_maps': total_maps,
        'critical_maps': critical_maps,
        'high_maps': high_maps,
        'moderate_maps': moderate_maps,
        'area_filter': area_filter,
        'camera_filter': camera_filter,
        'status_filter': status_filter,
    }
    return render(request, 'dept/dept_density_maps.html', context)




@login_required
def dept_view_crowd_count(request):
    dept = get_object_or_404(
        EmergencyDepartment.objects.prefetch_related('assigned_areas'),
        LOGIN_id=request.user.id
    )

    assigned_areas = dept.assigned_areas.all()
    assigned_area_ids = assigned_areas.values_list('id', flat=True)

    area_filter = request.GET.get('area', '').strip()
    camera_filter = request.GET.get('camera', '').strip()
    status_filter = request.GET.get('status', '').strip()
    date_filter = request.GET.get('date', '').strip()

    logs = CrowdDensityLog.objects.filter(
        camera__area_id__in=assigned_area_ids
    ).select_related('camera', 'camera__area').order_by('-recorded_at')

    if area_filter:
        logs = logs.filter(camera__area_id=area_filter)
    if camera_filter:
        logs = logs.filter(camera_id=camera_filter)
    if status_filter:
        logs = logs.filter(status=status_filter)
    if date_filter:
        d = parse_date(date_filter)
        if d:
            logs = logs.filter(recorded_at__date=d)

    sector_headcounts = []
    total_live_jurisdiction_headcount = 0

    for area in assigned_areas:
        area_cams = CCTVCamera.objects.filter(area=area)
        current_sector_headcount = 0

        for cam in area_cams:
            latest_cam_log = CrowdDensityLog.objects.filter(camera=cam).order_by('-recorded_at').first()
            if latest_cam_log:
                current_sector_headcount += latest_cam_log.estimated_crowd_count

        total_live_jurisdiction_headcount += current_sector_headcount
        capacity = area.max_crowd_capacity or 1
        load_pct = round((current_sector_headcount / capacity) * 100, 1)

        sector_headcounts.append({
            'area': area,
            'current_headcount': current_sector_headcount,
            'capacity': area.max_crowd_capacity,
            'load_pct': load_pct,
            'progress_width': min(load_pct, 100.0),
            'camera_count': area_cams.count(),
        })

    total_allocated_capacity = assigned_areas.aggregate(Sum('max_crowd_capacity'))['max_crowd_capacity__sum'] or 1
    overall_load_factor = round((total_live_jurisdiction_headcount / total_allocated_capacity) * 100, 1)
    peak_count_log = logs.aggregate(Max('estimated_crowd_count'))['estimated_crowd_count__max'] or 0
    average_log_count = int(logs.aggregate(Avg('estimated_crowd_count'))['estimated_crowd_count__avg'] or 0)

    cameras = CCTVCamera.objects.filter(area_id__in=assigned_area_ids).select_related('area').order_by(
        'camera_identifier')

    context = {
        'dept': dept,
        'assigned_areas': assigned_areas,
        'cameras': cameras,
        'logs': logs[:100],  # Latest 100 records
        'sector_headcounts': sector_headcounts,
        'total_live_jurisdiction_headcount': total_live_jurisdiction_headcount,
        'total_allocated_capacity': total_allocated_capacity,
        'overall_load_factor': overall_load_factor,
        'peak_count_log': peak_count_log,
        'average_log_count': average_log_count,
        'area_filter': area_filter,
        'camera_filter': camera_filter,
        'status_filter': status_filter,
        'date_filter': date_filter,
    }
    return render(request, 'dept/dept_view_crowd_count.html', context)



@login_required
def dept_high_density(request):
    dept = get_object_or_404(
        EmergencyDepartment.objects.prefetch_related('assigned_areas'),
        LOGIN_id=request.user.id
    )

    assigned_areas = dept.assigned_areas.all()
    assigned_area_ids = assigned_areas.values_list('id', flat=True)

    area_filter = request.GET.get('area', '').strip()
    status_filter = request.GET.get('status', '').strip()

    high_density_logs = CrowdDensityLog.objects.filter(
        camera__area_id__in=assigned_area_ids,
        status__in=['HIGH', 'CRITICAL']
    ).select_related('camera', 'camera__area').order_by('-recorded_at')

    if area_filter:
        high_density_logs = high_density_logs.filter(camera__area_id=area_filter)

    if status_filter:
        high_density_logs = high_density_logs.filter(status=status_filter)

    critical_logs_count = high_density_logs.filter(status='CRITICAL').count()
    high_logs_count = high_density_logs.filter(status='HIGH').count()

    critical_zones = []
    for area in assigned_areas:
        area_cameras = CCTVCamera.objects.filter(area=area)
        current_headcount = 0
        latest_status = 'NORMAL'

        for cam in area_cameras:
            latest_log = CrowdDensityLog.objects.filter(camera=cam).order_by('-recorded_at').first()
            if latest_log:
                current_headcount += latest_log.estimated_crowd_count
                if latest_log.status == 'CRITICAL':
                    latest_status = 'CRITICAL'
                elif latest_log.status == 'HIGH' and latest_status != 'CRITICAL':
                    latest_status = 'HIGH'

        capacity = area.max_crowd_capacity or 1
        utilization_rate = round((current_headcount / capacity) * 100, 1)

        if utilization_rate >= 70.0 or latest_status in ['HIGH', 'CRITICAL']:
            critical_zones.append({
                'area': area,
                'camera_count': area_cameras.count(),
                'current_headcount': current_headcount,
                'capacity': area.max_crowd_capacity,
                'utilization_rate': utilization_rate,
                'progress_width': min(utilization_rate, 100.0),
                'risk_status': latest_status,
            })

    critical_zones.sort(key=lambda x: x['utilization_rate'], reverse=True)

    context = {
        'dept': dept,
        'assigned_areas': assigned_areas,
        'high_density_logs': high_density_logs[:100],
        'critical_zones': critical_zones,
        'critical_logs_count': critical_logs_count,
        'high_logs_count': high_logs_count,
        'area_filter': area_filter,
        'status_filter': status_filter,
    }
    return render(request, 'dept/dept_high_density.html', context)




@login_required
def dept_view_anomalies(request):
    dept = get_object_or_404(
        EmergencyDepartment.objects.prefetch_related('assigned_areas'),
        LOGIN_id=request.user.id
    )

    assigned_areas = dept.assigned_areas.all()
    assigned_area_ids = assigned_areas.values_list('id', flat=True)

    type_filter = request.GET.get('type', '').strip()
    area_filter = request.GET.get('area', '').strip()
    camera_filter = request.GET.get('camera', '').strip()
    date_filter = request.GET.get('date', '').strip()

    anomalies = AnomalyDetectionLog.objects.filter(
        camera__area_id__in=assigned_area_ids
    ).select_related('camera', 'camera__area').order_by('-detected_at')

    if type_filter:
        anomalies = anomalies.filter(anomaly_type=type_filter)
    if area_filter:
        anomalies = anomalies.filter(camera__area_id=area_filter)
    if camera_filter:
        anomalies = anomalies.filter(camera_id=camera_filter)
    if date_filter:
        d = parse_date(date_filter)
        if d:
            anomalies = anomalies.filter(detected_at__date=d)

    total_anomalies = anomalies.count()
    peak_confidence = anomalies.aggregate(Max('confidence_score'))['confidence_score__max'] or 0.0
    avg_confidence = anomalies.aggregate(Avg('confidence_score'))['confidence_score__avg'] or 0.0

    threat_events_count = anomalies.filter(anomaly_type__in=['STAMPEDE_RUSH', 'TURBULENCE']).count()

    cameras = CCTVCamera.objects.filter(area_id__in=assigned_area_ids).select_related('area').order_by('camera_identifier')

    context = {
        'dept': dept,
        'assigned_areas': assigned_areas,
        'cameras': cameras,
        'anomalies': anomalies[:100],
        'total_anomalies': total_anomalies,
        'threat_events_count': threat_events_count,
        'peak_confidence': peak_confidence,
        'avg_confidence': avg_confidence,
        'type_filter': type_filter,
        'area_filter': area_filter,
        'camera_filter': camera_filter,
        'date_filter': date_filter,
        'anomaly_choices': AnomalyDetectionLog.ANOMALY_CHOICES,
    }
    return render(request, 'dept/dept_view_anomalies.html', context)




@login_required
def dept_receive_alerts(request):
    dept = get_object_or_404(
        EmergencyDepartment.objects.prefetch_related('assigned_areas'),
        LOGIN_id=request.user.id
    )

    assigned_areas = dept.assigned_areas.all()
    assigned_area_ids = assigned_areas.values_list('id', flat=True)

    status_filter = request.GET.get('status', '').strip()
    severity_filter = request.GET.get('severity', '').strip()
    area_filter = request.GET.get('area', '').strip()
    date_filter = request.GET.get('date', '').strip()

    alerts = EmergencyAlert.objects.filter(
        Q(emergency_department=dept) | Q(area_id__in=assigned_area_ids)
    ).select_related(
        'area', 'emergency_department', 'density_log', 'anomaly_log',
        'density_log__camera', 'anomaly_log__camera'
    ).order_by('-created_at')

    if status_filter:
        alerts = alerts.filter(status=status_filter)
    if severity_filter:
        alerts = alerts.filter(severity=severity_filter)
    if area_filter:
        alerts = alerts.filter(area_id=area_filter)
    if date_filter:
        d = parse_date(date_filter)
        if d:
            alerts = alerts.filter(created_at__date=d)

    total_received = alerts.count()
    active_critical = alerts.filter(status='ACTIVE', severity='CRITICAL').count()
    active_total = alerts.filter(status='ACTIVE').count()
    under_control_total = alerts.filter(status='UNDER_CONTROL').count()
    resolved_total = alerts.filter(status='RESOLVED').count()

    context = {
        'dept': dept,
        'assigned_areas': assigned_areas,
        'alerts': alerts[:100],  # Latest 100 emergency alerts
        'total_received': total_received,
        'active_critical': active_critical,
        'active_total': active_total,
        'under_control_total': under_control_total,
        'resolved_total': resolved_total,
        'status_filter': status_filter,
        'severity_filter': severity_filter,
        'area_filter': area_filter,
        'date_filter': date_filter,
        'severity_choices': EmergencyAlert.SEVERITY_CHOICES,
        'status_choices': EmergencyAlert.STATUS_CHOICES,
    }
    return render(request, 'dept/dept_receive_alerts.html', context)


@login_required
def dept_acknowledge_alert(request, alert_id):
    dept = get_object_or_404(EmergencyDepartment, LOGIN_id=request.user.id)
    assigned_area_ids = dept.assigned_areas.values_list('id', flat=True)

    alert = get_object_or_404(
        EmergencyAlert,
        Q(emergency_department=dept) | Q(area_id__in=assigned_area_ids),
        id=alert_id
    )

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'acknowledge':
            alert.status = 'UNDER_CONTROL'
            if not alert.emergency_department:
                alert.emergency_department = dept
            alert.save()
            messages.success(request, f'Alert "{alert.title}" acknowledged. Status set to Under Control.')
        elif action == 'resolve':
            alert.status = 'RESOLVED'
            alert.save()
            messages.success(request, f'Alert "{alert.title}" marked as Resolved.')

    return redirect('/myapp/dept_receive_alerts/')



@login_required
def dept_assigned_volunteers(request):
    dept=EmergencyDepartment.objects.get(LOGIN_id=request.user.id)


    status_filter = request.GET.get('status', '').strip()
    search_query = request.GET.get('search', '').strip()

    volunteers = VolunteerProfile.objects.filter(emergency_department__LOGIN_id=request.user.id)

    if status_filter:
        volunteers = volunteers.filter(availability_status=status_filter)

    if search_query:
        volunteers = volunteers.filter(
            Q(user__name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__phone__icontains=search_query) |
            Q(user__place__icontains=search_query)
        )

    total_volunteers = VolunteerProfile.objects.filter(emergency_department=dept).count()
    on_duty_count = VolunteerProfile.objects.filter(emergency_department=dept, availability_status='ON_DUTY').count()
    available_count = VolunteerProfile.objects.filter(emergency_department=dept, availability_status='AVAILABLE').count()
    off_duty_count = VolunteerProfile.objects.filter(emergency_department=dept, availability_status='OFF_DUTY').count()

    context = {
        'dept': dept,
        'volunteers': volunteers[:120],
        'total_volunteers': total_volunteers,
        'on_duty_count': on_duty_count,
        'available_count': available_count,
        'off_duty_count': off_duty_count,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'dept/dept_assigned_volunteers.html', context)




from django.db.models import Q

@login_required
def dept_assign_tasks(request):
    dept = get_object_or_404(
        EmergencyDepartment.objects.prefetch_related('assigned_areas'),
        LOGIN_id=request.user.id
    )
    assigned_area_ids = dept.assigned_areas.values_list('id', flat=True)

    if request.method == 'POST':
        alert_id = request.POST.get('alert_id')
        volunteer_id = request.POST.get('volunteer_id')
        title = request.POST.get('title', '').strip()
        instruction = request.POST.get('instruction', '').strip()

        if not (alert_id and volunteer_id and title and instruction):
            messages.error(request, 'Please complete all required fields.')
            return redirect('/myapp/dept_assign_tasks/')

        alert = get_object_or_404(
            EmergencyAlert,
            Q(emergency_department=dept) | Q(area_id__in=assigned_area_ids),
            id=alert_id
        )
        volunteer = get_object_or_404(
            VolunteerProfile,
            emergency_department=dept,
            id=volunteer_id
        )

        EmergencyTask.objects.create(
            alert=alert,
            department=dept,
            volunteer=volunteer,
            title=title,
            instruction=instruction,
            status='PENDING'
        )

        if volunteer.availability_status == 'AVAILABLE':
            volunteer.availability_status = 'ON_DUTY'
            volunteer.save()

        messages.success(request, f'Task successfully assigned to volunteer {volunteer.name}.')
        return redirect('/myapp/dept_assign_tasks/')

    selected_alert_id = request.GET.get('alert_id', '').strip()
    selected_volunteer_id = request.GET.get('volunteer_id', '').strip()

    active_alerts = EmergencyAlert.objects.filter(
        Q(emergency_department=dept) | Q(area_id__in=assigned_area_ids),
        status__in=['ACTIVE', 'UNDER_CONTROL']
    ).select_related('area').order_by('-created_at')

    # Fixed: Query VolunteerProfile directly without 'user'
    volunteers = VolunteerProfile.objects.filter(
        emergency_department=dept
    ).order_by('availability_status', 'name')

    # Fixed: Task select_related references 'volunteer' directly
    assigned_tasks = EmergencyTask.objects.filter(
        department=dept
    ).select_related('alert', 'alert__area', 'volunteer').order_by('-assigned_at')[:60]

    context = {
        'dept': dept,
        'active_alerts': active_alerts,
        'volunteers': volunteers,
        'assigned_tasks': assigned_tasks,
        'selected_alert_id': selected_alert_id,
        'selected_volunteer_id': selected_volunteer_id,
    }
    return render(request, 'dept/dept_assign_tasks.html', context)



from django.db.models import Q, F
from django.utils.dateparse import parse_date
@login_required
def dept_previous_incidents(request):
    dept = get_object_or_404(
        EmergencyDepartment.objects.prefetch_related('assigned_areas'),
        LOGIN_id=request.user.id
    )

    assigned_areas = dept.assigned_areas.all()
    assigned_area_ids = assigned_areas.values_list('id', flat=True)

    severity_filter = request.GET.get('severity', '').strip()
    area_filter = request.GET.get('area', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    search_query = request.GET.get('search', '').strip()

    resolved_alerts = EmergencyAlert.objects.filter(
        Q(emergency_department=dept) | Q(area_id__in=assigned_area_ids),
        status='RESOLVED'
    ).select_related(
        'area', 'emergency_department', 'density_log', 'anomaly_log',
        'density_log__camera', 'anomaly_log__camera'
    ).prefetch_related('tasks').order_by('-updated_at')

    if severity_filter:
        resolved_alerts = resolved_alerts.filter(severity=severity_filter)
    if area_filter:
        resolved_alerts = resolved_alerts.filter(area_id=area_filter)
    if search_query:
        resolved_alerts = resolved_alerts.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(public_instructions__icontains=search_query)
        )
    if date_from:
        d_from = parse_date(date_from)
        if d_from:
            resolved_alerts = resolved_alerts.filter(created_at__date__gte=d_from)
    if date_to:
        d_to = parse_date(date_to)
        if d_to:
            resolved_alerts = resolved_alerts.filter(created_at__date__lte=d_to)

    # Historical Metrics
    total_resolved = resolved_alerts.count()
    critical_resolved = resolved_alerts.filter(severity='CRITICAL').count()
    high_resolved = resolved_alerts.filter(severity='HIGH').count()
    medium_resolved = resolved_alerts.filter(severity='MEDIUM').count()

    context = {
        'dept': dept,
        'assigned_areas': assigned_areas,
        'resolved_alerts': resolved_alerts[:120],  # Latest 120 resolved incidents
        'total_resolved': total_resolved,
        'critical_resolved': critical_resolved,
        'high_resolved': high_resolved,
        'medium_resolved': medium_resolved,
        'severity_filter': severity_filter,
        'area_filter': area_filter,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
        'severity_choices': EmergencyAlert.SEVERITY_CHOICES,
    }
    return render(request, 'dept/dept_previous_incidents.html', context)




from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count
from django.utils.dateparse import parse_date
from .models import EmergencyDepartment, EmergencyTask, EmergencyAlert, GroundReport

def dept_monitor_volunteer_response(request):
    dept = get_object_or_404(
        EmergencyDepartment.objects.prefetch_related('assigned_areas'),
        LOGIN_id=request.user.id
    )

    status_filter = request.GET.get('status', '').strip()
    alert_filter = request.GET.get('alert', '').strip()
    search_query = request.GET.get('search', '').strip()
    date_filter = request.GET.get('date', '').strip()

    # 1. Base Queryset for Tasks
    dept_tasks_qs = EmergencyTask.objects.filter(department=dept)

    tasks = dept_tasks_qs.select_related(
        'alert', 'alert__area', 'volunteer'
    ).prefetch_related(
        'ground_reports'
    ).order_by('-assigned_at')

    # 2. Filters
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if alert_filter:
        tasks = tasks.filter(alert_id=alert_filter)
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) |
            Q(volunteer__name__icontains=search_query) |
            Q(volunteer__phone__icontains=search_query) |
            Q(instruction__icontains=search_query)
        )
    if date_filter:
        d = parse_date(date_filter)
        if d:
            tasks = tasks.filter(assigned_at__date=d)

    # 3. Optimized Counts (Single Query with Aggregate)
    task_counts = dept_tasks_qs.aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status='PENDING')),
        active=Count('id', filter=Q(status__in=['ACCEPTED', 'IN_PROGRESS'])),
        completed=Count('id', filter=Q(status='COMPLETED')),
        declined=Count('id', filter=Q(status='DECLINED')),
    )

    # 4. Recent Reports (task__department വഴിയാണ് ഫിൽട്ടർ ചെയ്യേണ്ടത്)
    recent_reports = GroundReport.objects.filter(
        task__department=dept
    ).select_related(
        'task', 'volunteer', 'task__alert', 'task__alert__area'
    ).order_by('-reported_at')[:10]

    # 5. Department Alerts
    department_alerts = EmergencyAlert.objects.filter(
        Q(emergency_department=dept) | Q(area__in=dept.assigned_areas.all())
    ).distinct().order_by('-created_at')

    context = {
        'dept': dept,
        'tasks': tasks[:100],
        'recent_reports': recent_reports,
        'department_alerts': department_alerts,
        'total_tasks': task_counts['total'],
        'pending_tasks': task_counts['pending'],
        'active_deployments': task_counts['active'],
        'completed_tasks': task_counts['completed'],
        'declined_tasks': task_counts['declined'],
        'status_filter': status_filter,
        'alert_filter': alert_filter,
        'search_query': search_query,
        'date_filter': date_filter,
        'status_choices': EmergencyTask.STATUS_CHOICES,
    }
    return render(request, 'dept/dept_monitor_volunteer_response.html', context)












# flutter===========================





from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def app_login(request):

    # Check POST method
    if request.method != "POST":
        return JsonResponse({
            "status": "error",
            "message": "POST method required"
        }, status=405)

    # Get username and password
    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")

    # Validate input
    if not username or not password:
        return JsonResponse({
            "status": "error",
            "message": "Username and password are required"
        }, status=400)

    # Authenticate user
    user = authenticate(
        request,
        username=username,
        password=password
    )

    # Check authentication
    if user is None:
        return JsonResponse({
            "status": "error",
            "message": "Invalid username or password"
        }, status=401)

    # Check Users group
    is_users_group = user.groups.filter(
        name="Users"
    ).exists()

    # Check Volunteer group
    is_volunteer_group = user.groups.filter(
        name="Volunteer"
    ).exists()

    # Assign user type
    if is_users_group:
        user_type = "Users"

    elif is_volunteer_group:
        user_type = "Volunteer"

    else:
        return JsonResponse({
            "status": "error",
            "message": "User is not assigned to Users or Volunteer group"
        }, status=403)

    login(request, user)

    return JsonResponse({
        "status": "ok",
        "message": "Login successful",
        "lid": str(user.id),
        "username": user.username,
        "type": user_type
    }, status=200)


@csrf_exempt

def user_view_area(request):
    l=[]
    a=Area.objects.all()
    for i in a:
        l.append({
            'id':i.id,
            'name':i.name,
            'city':i.city,
            'district':i.district,
            'state':i.state,
            'pincode':str(i.pincode),
            'latitude':str(i.latitude),
            'longitude':str(i.longitude),
            'max_crowd_capacity':str(i.max_crowd_capacity),
            'current_risk_level':str(i.current_risk_level),
            'description':str(i.description),
        })

    print(l,'data====')
    return JsonResponse({'status':'ok','data':l})

@csrf_exempt

def user_register(request):
    name = request.POST['area']
    area = request.POST['region']
    place = request.POST['place']
    phone = request.POST['phone']
    email = request.POST['email']
    username = request.POST['username']
    password = request.POST['password']
    latitude = request.POST.get('latitude') or None
    longitude = request.POST.get('longitude') or None

    if User.objects.filter(username=username).exists():
        return JsonResponse({'status': 'no'})

    if User.objects.filter(email=email).exists():
        return JsonResponse({'status': 'no'})

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email
    )

    group = Group.objects.get(name="Users")
    user.groups.add(group)

    ert = User_Table()
    ert.LOGIN = user
    ert.area = Area.objects.get(id=area)
    ert.name = name
    ert.email = email
    ert.place = place
    ert.latitude = latitude
    ert.longitude = longitude
    ert.phone = phone
    ert.save()

    return JsonResponse({'status': 'ok'})


@csrf_exempt

def user_change_password(request):
    id = request.POST['lid']
    current_password = request.POST['old_password']
    new_password = request.POST['new_password']
    confirm_password = request.POST['confirm_password']
    res = User.objects.get(id=id)
    if res.check_password(current_password):
        if new_password == confirm_password:
            res.set_password(new_password)
            res.save()
            return JsonResponse({'status': 'ok'})
        else:
            return JsonResponse({'status': 'no'})
    else:
        return JsonResponse({'status': 'no'})




@csrf_exempt
def user_view_profile(request):
    lid = request.POST['lid']

    print(lid)
    print(lid,'login id===')
    profile = User_Table.objects.get(LOGIN_id=lid)

    print(profile,'profile data')

    return JsonResponse({
        'status': 'ok',
        'name': profile.name or '',
        'phone': profile.phone or '',
        'email': profile.email or '',
        'place': profile.place or '',
        'area_id': str(profile.area.id) if profile.area else '',
        'area_name': str(profile.area.name) if profile.area else 'Not Assigned',
        'latitude': str(profile.latitude) if profile.latitude is not None else '',
        'longitude': str(profile.longitude) if profile.longitude is not None else '',
    })



@csrf_exempt
def user_edit_profile(request):

    lid = request.POST.get('lid')
    name = request.POST.get('area')       # Name of the user
    area_id = request.POST.get('region')  # Area ForeignKey ID
    place = request.POST.get('place')
    phone = request.POST.get('phone')
    email = request.POST.get('email')
    lat = request.POST.get('latitude')
    lon = request.POST.get('longitude')

    profile = User_Table.objects.get(LOGIN_id=lid)
    profile.name = name
    profile.place = place
    profile.phone = phone
    profile.email = email

    if area_id:
        try:
            profile.area = Area.objects.get(id=area_id)
        except Area.DoesNotExist:
            pass

    if lat and lon:
        profile.latitude = lat
        profile.longitude = lon

    profile.save()
    return JsonResponse({'status': 'ok', 'message': 'Profile updated successfully'})



@csrf_exempt
def user_view_emergency_department(request):
    try:
        lid = request.POST.get('lid')
        user_area_id = None

        if lid:
            try:
                user_record = User_Table.objects.select_related('area').get(LOGIN_id=lid)
                if user_record.area:
                    user_area_id = user_record.area.id
            except User_Table.DoesNotExist:
                pass

        departments = EmergencyDepartment.objects.filter(is_active=True).prefetch_related('assigned_areas')

        dept_list = []
        for d in departments:
            assigned_areas_data = [
                {
                    'id': str(a.id),
                    'name': str(getattr(a, 'name', a)),
                    'city': str(getattr(a, 'city', '')),
                }
                for a in d.assigned_areas.all()
            ]

            is_user_area_covered = False
            if user_area_id:
                is_user_area_covered = any(str(a.id) == str(user_area_id) for a in d.assigned_areas.all())

            dept_list.append({
                'id': str(d.id),
                'department_name': d.department_name,
                'department_code': d.department_code,
                'contact_number': d.contact_number,
                'helpline_number': d.helpline_number,
                'department_email': d.department_email,
                'office_address': d.office_address,
                'is_user_area': is_user_area_covered,
                'assigned_areas': assigned_areas_data,
            })

        if user_area_id:
            dept_list.sort(key=lambda x: x['is_user_area'], reverse=True)

        return JsonResponse({
            'status': 'ok',
            'data': dept_list
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})




@csrf_exempt
def user_view_emergency_alerts(request):
    try:
        lid = request.POST.get('lid')
        user_area_id = None

        if lid:
            try:
                user_record = User_Table.objects.select_related('area').get(LOGIN_id=lid)
                if user_record.area:
                    user_area_id = user_record.area.id
            except User_Table.DoesNotExist:
                pass

        alerts = EmergencyAlert.objects.select_related('area', 'emergency_department').order_by('-created_at')

        alert_list = []
        for alert in alerts:
            is_user_area = (user_area_id is not None and alert.area_id == user_area_id)

            alert_list.append({
                'id': str(alert.id),
                'title': alert.title,
                'description': alert.description,
                'public_instructions': alert.public_instructions or 'Follow standard safety precautions and keep exits clear.',
                'severity': alert.severity,  # 'MEDIUM', 'HIGH', 'CRITICAL'
                'status': alert.status,      # 'ACTIVE', 'UNDER_CONTROL', 'RESOLVED'
                'area_name': getattr(alert.area, 'name', str(alert.area)),
                'area_city': getattr(alert.area, 'city', ''),
                'department_name': alert.emergency_department.department_name if alert.emergency_department else 'Central Dispatch',
                'department_helpline': alert.emergency_department.helpline_number if alert.emergency_department else '',
                'is_user_area': is_user_area,
                'created_at': alert.created_at.strftime('%d %b %Y, %I:%M %p') if alert.created_at else '',
            })

        alert_list.sort(key=lambda x: (x['is_user_area'], x['status'] == 'ACTIVE'), reverse=True)

        return JsonResponse({
            'status': 'ok',
            'data': alert_list,
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})




@csrf_exempt
def user_submit_complaint(request):
    lid = request.POST.get('lid')
    subject = request.POST.get('subject', '').strip()
    description = request.POST.get('description', '').strip()

    if not subject or not description:
        return JsonResponse({'status': 'no', 'message': 'Subject and description are required'})

    user_profile = User_Table.objects.get(LOGIN_id=lid)

    Complaint.objects.create(
        user=user_profile,
        subject=subject,
        description=description,
        status='Pending'
    )

    return JsonResponse({'status': 'ok', 'message': 'Complaint submitted successfully'})

@csrf_exempt
def user_view_complaints(request):
    lid = request.POST.get('lid')
    user_profile = User_Table.objects.get(LOGIN_id=lid)

    complaints = Complaint.objects.filter(user=user_profile).order_by('-submitted_at')

    data = []
    for c in complaints:
        data.append({
            'id': str(c.id),
            'subject': c.subject,
            'description': c.description,
            'admin_response': c.admin_response or '',
            'status': c.status,
            'submitted_at': c.submitted_at.strftime('%d %b %Y, %I:%M %p') if c.submitted_at else '',
            'resolved_at': c.resolved_at.strftime('%d %b %Y, %I:%M %p') if c.resolved_at else '',
        })

    return JsonResponse({'status': 'ok', 'data': data})



@csrf_exempt
def user_submit_feedback(request):
    lid = request.POST.get('lid')
    subject = request.POST.get('subject', '').strip()
    message = request.POST.get('message', '').strip()
    rating_raw = request.POST.get('rating', '5')

    if not subject or not message:
        return JsonResponse({'status': 'no', 'message': 'Subject and message are required'})

    try:
        rating = int(rating_raw)
        if rating < 1 or rating > 5:
            rating = 5
    except (ValueError, TypeError):
        rating = 5

    user_profile = User_Table.objects.get(LOGIN_id=lid)

    Feedback.objects.create(
        user=user_profile,
        subject=subject,
        message=message,
        rating=rating
    )

    return JsonResponse({'status': 'ok', 'message': 'Feedback submitted successfully'})


@csrf_exempt
def user_view_feedback(request):

    lid = request.POST.get('lid')
    user_profile = User_Table.objects.get(LOGIN_id=lid)

    feedbacks = Feedback.objects.filter(user=user_profile).order_by('-submitted_at')

    data = []
    for f in feedbacks:
        data.append({
            'id': str(f.id),
            'subject': f.subject,
            'message': f.message,
            'rating': f.rating,
            'submitted_at': f.submitted_at.strftime('%d %b %Y, %I:%M %p') if f.submitted_at else '',
        })

    return JsonResponse({'status': 'ok', 'data': data})




@csrf_exempt
def user_add_emergency_report(request):
    lid = request.POST.get('lid')
    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '').strip()
    public_instructions = request.POST.get('public_instructions', '').strip()

    if not title or not description:
        return JsonResponse({'status': 'no', 'message': 'Title and description are required'})

    if not public_instructions:
        public_instructions = "Avoid the crowded zone. Follow emergency volunteer directives and keep evacuation pathways open."

    user_profile = User_Table.objects.get(LOGIN_id=lid)

    report = Report_Emergency.objects.create(
        USER=user_profile,
        title=title,
        description=description,
        public_instructions=public_instructions,
        status='ACTIVE'
    )

    return JsonResponse({'status': 'ok', 'message': 'Emergency reported successfully', 'id': str(report.id)})


@csrf_exempt
def user_view_emergency_reports(request):

    lid = request.POST.get('lid')
    user_profile = User_Table.objects.get(LOGIN_id=lid)

    reports = Report_Emergency.objects.filter(USER=user_profile).order_by('-created_at')

    data = []
    for r in reports:
        data.append({
            'id': str(r.id),
            'title': r.title,
            'description': r.description,
            'public_instructions': r.public_instructions or '',
            'status': r.status,
            'created_at': r.created_at.strftime('%d %b %Y, %I:%M %p') if r.created_at else '',
        })

    return JsonResponse({'status': 'ok', 'data': data})


@csrf_exempt
def user_delete_emergency_report(request):

    lid = request.POST.get('lid')

    user_profile=User_Table.objects.get(LOGIN_id=lid)
    report_id = request.POST.get('report_id')

    report = Report_Emergency.objects.get(id=report_id, USER=user_profile)
    report.delete()

    return JsonResponse({'status': 'ok', 'message': 'Report deleted successfully'})




@csrf_exempt
def user_view_emergency_instructions(request):

    instructions = EmergencyInstruction.objects.select_related('emergency_department').order_by('-created_at')

    data = []
    for item in instructions:
        data.append({
            'id': str(item.id),
            'title': item.title,
            'instruction_type': item.instruction_type,
            'severity_level': item.severity_level,
            'department_name': item.emergency_department.department_name if item.emergency_department else 'Central Public Safety',
            'department_helpline': item.emergency_department.helpline_number if item.emergency_department else '',
            'summary': item.summary,
            'detailed_steps': item.detailed_steps,
            'do_list': item.do_list or '',
            'dont_list': item.dont_list or '',
            'created_at': item.created_at.strftime('%d %b %Y') if item.created_at else '',
        })

    return JsonResponse({'status': 'ok', 'data': data})




@csrf_exempt
def user_view_crowd_density(request):
    try:
        lid = request.POST.get('lid')
        user_area_id = None

        if lid:
            try:
                user_record = User_Table.objects.select_related('area').get(LOGIN_id=lid)
                if user_record.area:
                    user_area_id = user_record.area.id
            except User_Table.DoesNotExist:
                pass

        cameras = CCTVCamera.objects.all().select_related('area')

        # Prioritize cameras matching user's assigned area
        if user_area_id:
            cameras = sorted(cameras, key=lambda c: c.area_id == user_area_id, reverse=True)

        data = []
        for cam in cameras:
            latest_log = CrowdDensityLog.objects.filter(camera=cam).order_by('-recorded_at').first()

            count = latest_log.estimated_crowd_count if latest_log else 0
            status = latest_log.status if latest_log else 'NORMAL'
            density_img = latest_log.density_map_image.url if (latest_log and latest_log.density_map_image) else ''
            recorded_time = latest_log.recorded_at.strftime('%I:%M:%S %p, %d %b') if latest_log else 'Live Feed Idle'

            # Extract max_crowd_capacity directly from the camera's Area model
            max_capacity = cam.area.max_crowd_capacity if (cam.area and cam.area.max_crowd_capacity) else 500
            try:
                max_capacity = int(max_capacity)
            except (ValueError, TypeError):
                max_capacity = 500

            load_percentage = min(100, int((count / max_capacity) * 100)) if max_capacity > 0 else 0
            is_user_area = (user_area_id is not None and cam.area_id == user_area_id)

            data.append({
                'camera_id': str(cam.id),
                'camera_identifier': cam.camera_identifier,
                'location_details': cam.location_details or 'Surveillance Point',
                'latitude': str(cam.latitude) if cam.latitude is not None else '',
                'longitude': str(cam.longitude) if cam.longitude is not None else '',
                'area_name': cam.area.name if cam.area else 'Surveillance Zone',
                'area_city': cam.area.city if cam.area else '',
                'area_risk_level': cam.area.current_risk_level if cam.area else 'LOW',
                'is_user_area': is_user_area,
                'count': count,
                'max_capacity': max_capacity,
                'load_percentage': load_percentage,
                'status': status,
                'density_map': density_img,
                'recorded_at': recorded_time,
            })

        return JsonResponse({'status': 'ok', 'data': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})






@csrf_exempt
def user_view_all_crowd_status(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'no', 'message': 'Invalid request method'}, status=405)

    lid = request.POST.get('lid')

    try:
        user_assigned_area_id = None
        if lid:
            user_profile = User_Table.objects.select_related('area').filter(LOGIN_id=lid).first()
            if user_profile and user_profile.area:
                user_assigned_area_id = user_profile.area.id

        areas = Area.objects.all().order_by('name')
        area_data_list = []

        for area in areas:
            cameras = CCTVCamera.objects.filter(area=area)
            total_current_crowd = 0
            camera_details = []

            for cam in cameras:
                latest_log = cam.density_logs.order_by('-recorded_at').first()

                if latest_log:
                    cam_count = latest_log.estimated_crowd_count
                    total_current_crowd += cam_count
                    cam_status = latest_log.status
                    image_url = request.build_absolute_uri(
                        latest_log.density_map_image.url) if latest_log.density_map_image else ''
                    recorded_at = latest_log.recorded_at.strftime('%I:%M %p, %d %b %Y')
                else:
                    cam_count = 0
                    cam_status = 'OFFLINE'
                    image_url = ''
                    recorded_at = 'No updates'

                camera_details.append({
                    'camera_id': cam.id,
                    'identifier': cam.camera_identifier,
                    'location': cam.location_details,
                    'crowd_count': cam_count,
                    'status': cam_status,
                    'heatmap_url': image_url,
                    'last_updated': recorded_at,
                })

            max_capacity = area.max_crowd_capacity if area.max_crowd_capacity > 0 else 1
            load_percentage = min(round((total_current_crowd / max_capacity) * 100, 1), 100.0)

            area_data_list.append({
                'id': area.id,
                'name': area.name,
                'city': area.city,
                'district': area.district,
                'risk_level': area.current_risk_level,
                'max_capacity': area.max_crowd_capacity,
                'current_total_crowd': total_current_crowd,
                'load_percentage': load_percentage,
                'cameras_count': cameras.count(),
                'is_my_area': (area.id == user_assigned_area_id),
                'cameras': camera_details,
            })

        if user_assigned_area_id:
            area_data_list.sort(key=lambda x: not x['is_my_area'])

        return JsonResponse({
            'status': 'ok',
            'total_areas': len(area_data_list),
            'data': area_data_list
        })

    except Exception as e:
        return JsonResponse({'status': 'no', 'message': f'Server error: {str(e)}'})

@csrf_exempt
def user_view_area_risk_level(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'no', 'message': 'Invalid request method'}, status=405)

    lid = request.POST.get('lid')

    try:
        user_assigned_area_id = None
        if lid:
            user_profile = User_Table.objects.select_related('area').filter(LOGIN_id=lid).first()
            if user_profile and user_profile.area:
                user_assigned_area_id = user_profile.area.id

        areas = Area.objects.all().order_by('name')
        area_risk_data = []

        for area in areas:
            # 1. Fetch active emergency alerts for this sector
            active_alerts = EmergencyAlert.objects.filter(
                area=area,
                status='ACTIVE'
            ).order_by('-created_at')

            alert_list = []
            for alert in active_alerts:
                alert_list.append({
                    'id': alert.id,
                    'title': alert.title,
                    'severity': alert.severity,
                    'description': alert.description,
                    'public_instructions': alert.public_instructions,
                    'department': alert.emergency_department.name if alert.emergency_department else 'Sector Security Control',
                    'updated_at': alert.updated_at.strftime('%I:%M %p, %d %b %Y'),
                })

            # 2. Fetch latest critical anomalies detected across area cameras
            area_cameras = CCTVCamera.objects.filter(area=area)
            recent_anomalies = AnomalyDetectionLog.objects.filter(
                camera__in=area_cameras
            ).select_related('camera').order_by('-detected_at')[:3]

            anomaly_list = []
            for anom in recent_anomalies:
                snapshot_url = request.build_absolute_uri(anom.frame_snapshot.url) if anom.frame_snapshot else ''
                clip_url = request.build_absolute_uri(anom.video_clip.url) if anom.video_clip else ''
                anomaly_list.append({
                    'id': anom.id,
                    'camera_identifier': anom.camera.camera_identifier,
                    'location': anom.camera.location_details,
                    'type': anom.get_anomaly_type_display(),
                    'raw_type': anom.anomaly_type,
                    'confidence': round(anom.confidence_score * 100, 1),
                    'frame_snapshot': snapshot_url,
                    'video_clip': clip_url,
                    'detected_at': anom.detected_at.strftime('%I:%M %p, %d %b'),
                })

            area_risk_data.append({
                'id': area.id,
                'name': area.name,
                'city': area.city,
                'district': area.district,
                'risk_level': area.current_risk_level,
                'is_my_area': (area.id == user_assigned_area_id),
                'active_alerts_count': len(alert_list),
                'alerts': alert_list,
                'recent_anomalies': anomaly_list,
            })

        # Rank user's assigned area first, then critical/high risks
        if user_assigned_area_id:
            area_risk_data.sort(key=lambda x: not x['is_my_area'])

        return JsonResponse({
            'status': 'ok',
            'areas': area_risk_data,
        })

    except Exception as e:
        return JsonResponse({'status': 'no', 'message': f'Server error: {str(e)}'})



# volunteer module




@csrf_exempt
def updatelocation(request):

    if request.method != "POST":
        return JsonResponse({
            "status": "error",
            "message": "POST method required"
        }, status=405)

    lid = request.POST.get("lid", "").strip()
    lat = request.POST.get("latitude", "").strip()
    lon = request.POST.get("longitude", "").strip()

    # Validate input
    if not lid or not lat or not lon:
        return JsonResponse({
            "status": "error",
            "message": "lid, latitude and longitude are required"
        }, status=400)

    try:
        user_id = int(lid)
        latitude = float(lat)
        longitude = float(lon)
    except (ValueError, TypeError):
        return JsonResponse({
            "status": "error",
            "message": "Invalid user ID or coordinates"
        }, status=400)

    # Validate latitude
    if not -90 <= latitude <= 90:
        return JsonResponse({
            "status": "error",
            "message": "Invalid latitude"
        }, status=400)

    # Validate longitude
    if not -180 <= longitude <= 180:
        return JsonResponse({
            "status": "error",
            "message": "Invalid longitude"
        }, status=400)

    # Find user
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": "User not found"
        }, status=404)

    # Find volunteer profile
    try:
        volunteer = VolunteerProfile.objects.get(LOGIN=user)
    except VolunteerProfile.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": "Volunteer profile not found"
        }, status=404)

    # Update latitude and longitude
    volunteer.latitude = latitude
    volunteer.longitude = longitude
    volunteer.save(update_fields=["latitude", "longitude"])

    return JsonResponse({
        "status": "ok",
        "message": "Volunteer location updated successfully",
        "lid": str(user.id),
        "latitude": float(volunteer.latitude),
        "longitude": float(volunteer.longitude)
    }, status=200)


@csrf_exempt
def volunteer_view_profile(request):
    lid = request.POST.get('lid')


    profile = VolunteerProfile.objects.select_related('emergency_department').get(LOGIN_id=lid)

    # Assigned area details extraction from EmergencyDepartment
    dept_name = "Not Assigned"
    dept_contact = "N/A"
    assigned_area_names = []

    if profile.emergency_department:
        dept_name = profile.emergency_department.department_name
        dept_contact = profile.emergency_department.contact_number
        assigned_area_names = list(
            profile.emergency_department.assigned_areas.values_list('name', flat=True)
        )

    photo_url = request.build_absolute_uri(profile.photo.url) if profile.photo else ''
    id_proof_url = request.build_absolute_uri(profile.id_proof.url) if profile.id_proof else ''

    data = {
        'id': profile.id,
        'name': profile.name,
        'email': profile.email,
        'phone': profile.phone,
        'place': profile.place,
        'photo': photo_url,
        'id_proof': id_proof_url,
        'approval_status': profile.approval_status,
        'availability_status': profile.availability_status,
        'join_at': profile.join_at.strftime('%Y-%m-%d %H:%M') if profile.join_at else 'N/A',
        'latitude': str(profile.latitude) if profile.latitude else None,
        'longitude': str(profile.longitude) if profile.longitude else None,
        'department_name': dept_name,
        'department_contact': dept_contact,
        'assigned_areas': assigned_area_names,
    }

    return JsonResponse({'status': 'ok', 'data': data})




@csrf_exempt
def update_volunteer_profile_place(request):
    if request.method == 'POST':
        lid = request.POST.get('lid')
        place = request.POST.get('place')
        lat = request.POST.get('latitude')
        lon = request.POST.get('longitude')

        if not lid or not place:
            return JsonResponse({'status': 'error', 'message': 'Missing lid or place data'}, status=400)

        try:
            profile = VolunteerProfile.objects.get(LOGIN_id=lid)
            profile.place = place
            if lat:
                profile.latitude = float(lat)
            if lon:
                profile.longitude = float(lon)
            profile.save(update_fields=['place', 'latitude', 'longitude'])

            return JsonResponse({'status': 'ok', 'message': 'Place updated successfully', 'place': profile.place})
        except VolunteerProfile.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Volunteer profile not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
@csrf_exempt

def volunteer_change_password(request):
    id = request.POST['lid']
    current_password = request.POST['old_password']
    new_password = request.POST['new_password']
    confirm_password = request.POST['confirm_password']
    res = User.objects.get(id=id)
    if res.check_password(current_password):
        if new_password == confirm_password:
            res.set_password(new_password)
            res.save()
            return JsonResponse({'status': 'ok'})
        else:
            return JsonResponse({'status': 'no'})
    else:
        return JsonResponse({'status': 'no'})


@csrf_exempt
def volunteer_view_assigned_department(request):
    if request.method == 'POST':
        lid = request.POST.get('lid')
        if not lid:
            return JsonResponse({'status': 'error', 'message': 'Missing user identifier (lid)'}, status=400)

        try:
            profile = VolunteerProfile.objects.select_related('emergency_department').get(LOGIN_id=lid)
            dept = profile.emergency_department

            if not dept:
                return JsonResponse({
                    'status': 'no_dept',
                    'message': 'No Emergency Department has been assigned yet.'
                })

            # Assigned Areas listing
            areas_data = []
            for area in dept.assigned_areas.all():
                areas_data.append({
                    'id': area.id,
                    'name': area.name,
                    'city': area.city,
                    'district': area.district,
                    'state': area.state,
                    'pincode': area.pincode,
                    'latitude': str(area.latitude) if area.latitude else None,
                    'longitude': str(area.longitude) if area.longitude else None,
                    'max_crowd_capacity': area.max_crowd_capacity,
                    'current_risk_level': area.current_risk_level,
                    'description': area.description or '',
                })

            data = {
                'department_name': dept.department_name,
                'department_code': dept.department_code,
                'contact_number': dept.contact_number,
                'helpline_number': dept.helpline_number,
                'department_email': dept.department_email,
                'office_address': dept.office_address,
                'is_active': dept.is_active,
                'volunteer_name': profile.name,
                'assigned_areas': areas_data,
            }

            return JsonResponse({'status': 'ok', 'data': data})

        except VolunteerProfile.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Volunteer profile not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)




@csrf_exempt
def volunteer_view_emergency_alerts(request):
    if request.method == 'POST':
        lid = request.POST.get('lid')
        status_filter = request.POST.get('status', 'ALL')  # ALL, ACTIVE, UNDER_CONTROL, RESOLVED

        if not lid:
            return JsonResponse({'status': 'error', 'message': 'Missing user identifier (lid)'}, status=400)

        try:
            profile = VolunteerProfile.objects.select_related('emergency_department').get(LOGIN_id=lid)
            dept = profile.emergency_department

            alerts_qs = EmergencyAlert.objects.select_related('area', 'emergency_department').all()

            if dept:
                assigned_areas = dept.assigned_areas.all()
                alerts_qs = alerts_qs.filter(area__in=assigned_areas)

            if status_filter.upper() != 'ALL':
                alerts_qs = alerts_qs.filter(status=status_filter.upper())

            alerts_qs = alerts_qs.order_by('-created_at')

            alerts_list = []
            for alert in alerts_qs:
                alerts_list.append({
                    'id': alert.id,
                    'title': alert.title,
                    'severity': alert.severity,
                    'status': alert.status,
                    'area_name': alert.area.name if alert.area else 'Sector Unknown',
                    'city': alert.area.city if alert.area else '',
                    'current_risk_level': alert.area.current_risk_level if alert.area else 'MODERATE',
                    'department_name': alert.emergency_department.department_name if alert.emergency_department else (dept.department_name if dept else 'Central Command'),
                    'description': alert.description,
                    'public_instructions': alert.public_instructions,
                    'created_at': alert.created_at.strftime('%d %b %Y, %I:%M %p') if alert.created_at else 'Just now',
                    'updated_at': alert.updated_at.strftime('%d %b %Y, %I:%M %p') if alert.updated_at else '',
                })

            return JsonResponse({
                'status': 'ok',
                'active_count': alerts_qs.filter(status='ACTIVE').count(),
                'data': alerts_list
            })

        except VolunteerProfile.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Volunteer profile not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)



@csrf_exempt
def volunteer_view_tasks(request):
    if request.method == 'POST':
        lid = request.POST.get('lid')
        status_filter = request.POST.get('status', 'ALL')

        if not lid:
            return JsonResponse({'status': 'error', 'message': 'Missing user identifier (lid)'}, status=400)

        try:
            profile = VolunteerProfile.objects.get(LOGIN_id=lid)
            tasks_qs = EmergencyTask.objects.select_related('alert', 'department', 'alert__area').filter(volunteer=profile)

            if status_filter.upper() != 'ALL':
                tasks_qs = tasks_qs.filter(status=status_filter.upper())

            tasks_qs = tasks_qs.order_by('-assigned_at')

            tasks_list = []
            for task in tasks_qs:
                tasks_list.append({
                    'id': task.id,
                    'title': task.title,
                    'instruction': task.instruction,
                    'status': task.status,
                    'alert_title': task.alert.title if task.alert else 'General Incident',
                    'alert_severity': task.alert.severity if task.alert else 'MEDIUM',
                    'area_name': task.alert.area.name if (task.alert and task.alert.area) else 'Field Checkpoint',
                    'department_name': task.department.department_name if task.department else 'Central Command',
                    'assigned_at': task.assigned_at.strftime('%d %b %Y, %I:%M %p') if task.assigned_at else '',
                    'responded_at': task.responded_at.strftime('%d %b %Y, %I:%M %p') if task.responded_at else None,
                    'completed_at': task.completed_at.strftime('%d %b %Y, %I:%M %p') if task.completed_at else None,
                })

            return JsonResponse({
                'status': 'ok',
                'pending_count': tasks_qs.filter(status='PENDING').count(),
                'data': tasks_list
            })

        except VolunteerProfile.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Volunteer profile not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)



@csrf_exempt
def volunteer_update_task_status(request):
    if request.method == 'POST':
        lid = request.POST.get('lid')
        task_id = request.POST.get('task_id')
        new_status = request.POST.get('status')  # ACCEPTED, DECLINED, IN_PROGRESS, COMPLETED

        valid_statuses = ['ACCEPTED', 'DECLINED', 'IN_PROGRESS', 'COMPLETED']

        if not lid or not task_id or not new_status:
            return JsonResponse({'status': 'error', 'message': 'lid, task_id, and status are required.'}, status=400)

        if new_status.upper() not in valid_statuses:
            return JsonResponse({'status': 'error', 'message': 'Invalid status choice.'}, status=400)

        try:
            profile = VolunteerProfile.objects.get(LOGIN_id=lid)
            task = EmergencyTask.objects.get(id=int(task_id), volunteer=profile)

            status_upper = new_status.upper()
            task.status = status_upper

            if status_upper in ['ACCEPTED', 'DECLINED']:
                task.responded_at = timezone.now()
            elif status_upper == 'COMPLETED':
                task.completed_at = timezone.now()

            task.save()

            return JsonResponse({
                'status': 'ok',
                'message': f'Task status updated to {status_upper}',
                'updated_status': task.status
            })

        except VolunteerProfile.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Volunteer profile not found.'}, status=404)
        except EmergencyTask.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Task not found or unauthorized.'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)





@csrf_exempt
def volunteer_view_emergency_instructions(request):
    if request.method == 'POST':
        lid = request.POST.get('lid')
        search_query = request.POST.get('search', '').strip()
        severity_filter = request.POST.get('severity', 'ALL')

        try:
            profile = None
            if lid:
                profile = VolunteerProfile.objects.select_related('emergency_department').filter(LOGIN_id=lid).first()

            instructions_qs = EmergencyInstruction.objects.select_related('emergency_department').all()

            if profile and profile.emergency_department:
                instructions_qs = instructions_qs.filter(
                    emergency_department__in=[profile.emergency_department, None]
                )

            if severity_filter.upper() != 'ALL':
                instructions_qs = instructions_qs.filter(severity_level=severity_filter.upper())

            if search_query:
                instructions_qs = instructions_qs.filter(title__icontains=search_query)

            instructions_qs = instructions_qs.order_by('-created_at')

            instructions_list = []
            for item in instructions_qs:
                instructions_list.append({
                    'id': item.id,
                    'title': item.title,
                    'instruction_type': item.instruction_type,
                    'severity_level': item.severity_level,
                    'department_name': item.emergency_department.department_name if item.emergency_department else 'Central Command / Standard SOP',
                    'summary': item.summary,
                    'detailed_steps': item.detailed_steps,
                    'do_list': item.do_list or '',
                    'dont_list': item.dont_list or '',
                    'created_at': item.created_at.strftime('%d %b %Y, %I:%M %p') if item.created_at else '',
                })

            return JsonResponse({
                'status': 'ok',
                'count': len(instructions_list),
                'data': instructions_list
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import VolunteerProfile, GroundReport, EmergencyTask


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import VolunteerProfile, GroundReport, EmergencyTask

# -------------------------------------------------------------------------
# 1. GET TODAY'S TASKS FOR FORM DROPDOWN
# -------------------------------------------------------------------------
@csrf_exempt
def get_volunteer_tasks_dropdown(request):
    if request.method == 'POST':
        lid = request.POST.get('lid')
        if not lid:
            return JsonResponse({'status': 'error', 'message': 'Missing lid'}, status=400)

        try:
            profile = VolunteerProfile.objects.get(LOGIN_id=lid)
            today = timezone.localdate()

            # ഇന്നത്തെ തീയതിയിലെ ടാസ്കുകൾ മാത്രം ഫിൽട്ടർ ചെയ്യുന്നു
            tasks = EmergencyTask.objects.filter(
                volunteer=profile,
                assigned_at__date=today
            ).order_by('-assigned_at')

            task_list = []
            for t in tasks:
                task_list.append({
                    'id': t.id,
                    'title': t.title,
                    'instruction': t.instruction,
                    'status': t.status,
                })

            return JsonResponse({'status': 'ok', 'tasks': task_list})

        except VolunteerProfile.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Volunteer profile not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


# -------------------------------------------------------------------------
# 2. VIEW ALL SUBMITTED GROUND REPORTS
# -------------------------------------------------------------------------
@csrf_exempt
def volunteer_view_ground_reports(request):
    if request.method == 'POST':
        lid = request.POST.get('lid')
        if not lid:
            return JsonResponse({'status': 'error', 'message': 'Missing lid'}, status=400)

        try:
            profile = VolunteerProfile.objects.get(LOGIN_id=lid)
            reports_qs = GroundReport.objects.select_related('task').filter(volunteer=profile).order_by('-reported_at')

            reports_list = []
            for report in reports_qs:
                img_url = request.build_absolute_uri(report.attached_image.url) if report.attached_image else ''
                reports_list.append({
                    'id': report.id,
                    'task_id': report.task_id,
                    'task_title': report.task.title if report.task else 'General Task',
                    'situation_update': report.situation_update,
                    'attached_image': img_url,
                    'reported_at': report.reported_at.strftime('%d %b %Y, %I:%M %p') if report.reported_at else '',
                })

            return JsonResponse({'status': 'ok', 'data': reports_list})

        except VolunteerProfile.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Volunteer profile not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


# -------------------------------------------------------------------------
# 3. ADD GROUND REPORT FOR SELECTED DROPDOWN TASK
# -------------------------------------------------------------------------
@csrf_exempt
def volunteer_add_ground_report(request):
    if request.method == 'POST':
        lid = request.POST.get('lid')
        task_id = request.POST.get('task_id')
        situation_update = request.POST.get('situation_update', '').strip()
        attached_image = request.FILES.get('attached_image')

        if not lid or not task_id or not situation_update:
            return JsonResponse({'status': 'error', 'message': 'lid, task_id, and situation update are required.'}, status=400)

        try:
            profile = VolunteerProfile.objects.get(LOGIN_id=lid)
            task_instance = EmergencyTask.objects.get(id=int(task_id), volunteer=profile)

            report = GroundReport.objects.create(
                volunteer=profile,
                task=task_instance,
                situation_update=situation_update,
                attached_image=attached_image
            )

            return JsonResponse({
                'status': 'ok',
                'message': 'Situation report submitted successfully.',
                'report_id': report.id
            })

        except VolunteerProfile.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Volunteer profile not found.'}, status=404)
        except EmergencyTask.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Task not found or unauthorized.'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


# -------------------------------------------------------------------------
# 4. DELETE GROUND REPORT
# -------------------------------------------------------------------------
@csrf_exempt
def volunteer_delete_ground_report(request):
    if request.method == 'POST':
        lid = request.POST.get('lid')
        report_id = request.POST.get('report_id')

        if not lid or not report_id:
            return JsonResponse({'status': 'error', 'message': 'Missing parameters'}, status=400)

        try:
            profile = VolunteerProfile.objects.get(LOGIN_id=lid)
            report = GroundReport.objects.get(id=int(report_id), volunteer=profile)

            if report.attached_image:
                report.attached_image.delete(save=False)
            report.delete()

            return JsonResponse({'status': 'ok', 'message': 'Report removed successfully.'})

        except VolunteerProfile.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Volunteer profile not found.'}, status=404)
        except GroundReport.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Report not found or unauthorized.'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)




@csrf_exempt
def volunteer_view_crowd_status(request):
    if request.method == 'POST':
        lid = request.POST.get('lid')
        area_filter = request.POST.get('area_id', '').strip()

        if not lid:
            return JsonResponse({'status': 'error', 'message': 'Missing user identifier (lid)'}, status=400)

        try:
            profile = VolunteerProfile.objects.select_related('emergency_department').get(LOGIN_id=lid)
            dept = profile.emergency_department

            if dept:
                areas_qs = dept.assigned_areas.all()
            else:
                areas_qs = Area.objects.all()

            if area_filter and area_filter != 'ALL':
                areas_qs = areas_qs.filter(id=int(area_filter))

            areas_list = []
            for area in areas_qs:
                cameras = CCTVCamera.objects.filter(area=area)
                camera_telemetry = []

                area_total_live_crowd = 0

                for cam in cameras:
                    latest_density = cam.density_logs.order_by('-recorded_at').first()
                    latest_anomaly = cam.anomaly_logs.order_by('-detected_at').first()

                    crowd_count = latest_density.estimated_crowd_count if latest_density else 0
                    area_total_live_crowd += crowd_count

                    density_map_url = ''
                    if latest_density and latest_density.density_map_image:
                        density_map_url = request.build_absolute_uri(latest_density.density_map_image.url)

                    anomaly_data = None
                    if latest_anomaly:
                        anomaly_frame = ''
                        if latest_anomaly.frame_snapshot:
                            anomaly_frame = request.build_absolute_uri(latest_anomaly.frame_snapshot.url)
                        anomaly_data = {
                            'type': latest_anomaly.get_anomaly_type_display(),
                            'confidence': round(latest_anomaly.confidence_score * 100, 1),
                            'frame': anomaly_frame,
                            'detected_at': latest_anomaly.detected_at.strftime('%I:%M %p, %d %b') if latest_anomaly.detected_at else '',
                        }

                    camera_telemetry.append({
                        'camera_id': cam.id,
                        'camera_identifier': cam.camera_identifier,
                        'location_details': cam.location_details,
                        'latitude': str(cam.latitude) if cam.latitude else None,
                        'longitude': str(cam.longitude) if cam.longitude else None,
                        'crowd_count': crowd_count,
                        'density_status': latest_density.status if latest_density else 'NORMAL',
                        'density_map_url': density_map_url,
                        'recorded_at': latest_density.recorded_at.strftime('%I:%M %p, %d %b') if latest_density and latest_density.recorded_at else 'Live Stream',
                        'latest_anomaly': anomaly_data,
                    })

                capacity = area.max_crowd_capacity if area.max_crowd_capacity > 0 else 1
                occupancy_rate = min(round((area_total_live_crowd / capacity) * 100, 1), 100.0)

                areas_list.append({
                    'area_id': area.id,
                    'area_name': area.name,
                    'city': area.city,
                    'max_capacity': area.max_crowd_capacity,
                    'current_risk_level': area.current_risk_level,
                    'total_live_crowd': area_total_live_crowd,
                    'occupancy_percentage': occupancy_rate,
                    'cameras': camera_telemetry,
                })

            available_dropdown_areas = list(
                dept.assigned_areas.values('id', 'name') if dept else Area.objects.values('id', 'name')
            )

            return JsonResponse({
                'status': 'ok',
                'areas_dropdown': available_dropdown_areas,
                'data': areas_list
            })

        except VolunteerProfile.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Volunteer profile not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)




@csrf_exempt
def volunteer_dashboard_data(request):
    if request.method == 'POST':
        lid = request.POST.get('lid')
        try:
            profile = VolunteerProfile.objects.select_related('emergency_department').get(LOGIN_id=lid)
            dept = profile.emergency_department
            today = timezone.localdate()

            today_tasks_qs = EmergencyTask.objects.select_related('alert', 'alert__area').filter(
                volunteer=profile,
                assigned_at__date=today
            ).order_by('-assigned_at')

            tasks_list = []
            for t in today_tasks_qs:
                tasks_list.append({
                    'id': t.id,
                    'title': t.title,
                    'location': t.alert.area.name if (t.alert and t.alert.area) else 'Field Checkpoint',
                    'priority': t.alert.severity if t.alert else 'HIGH',
                    'status': t.status,
                    'instruction': t.instruction,
                })

            active_emergency = EmergencyAlert.objects.filter(status='ACTIVE').order_by('-created_at').first()
            emergency_data = None
            if active_emergency:
                emergency_data = {
                    'id': active_emergency.id,
                    'title': active_emergency.title,
                    'instructions': active_emergency.public_instructions,
                    'severity': active_emergency.severity,
                }

            return JsonResponse({
                'status': 'ok',
                'name': profile.name,
                'department': dept.department_name if dept else 'Command Unit',
                'area': profile.area.name if hasattr(profile, 'area') and profile.area else 'Sector Assigned',
                'risk_level': 'MODERATE',
                'crowd_count': 120,
                'max_capacity': 2000,
                'active_emergency': emergency_data,
                'tasks': tasks_list,
            })
        except VolunteerProfile.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Profile not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)




# camera main part=======================








import base64
import binascii
import json
import threading
from collections import deque
from datetime import timedelta
from pathlib import Path

import cv2
import numpy as np

from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from .models import (
    Area,
    CCTVCamera,
    CrowdDensityLog,
    AnomalyDetectionLog,
    EmergencyAlert,
    EmergencyDepartment,
)



YOLO_MODEL_PATH = getattr(
    settings, "CROWD_YOLO_MODEL_PATH",
    str(Path(settings.BASE_DIR) / "yolov8n.pt")
)

CSRNET_PROTOTXT = getattr(
    settings, "CSRNET_PROTOTXT",
    str(Path(settings.BASE_DIR) / "models" / "deploy.prototxt")
)

CSRNET_WEIGHTS = getattr(
    settings, "CSRNET_WEIGHTS",
    str(Path(settings.BASE_DIR) / "models" / "shanghaib.caffemodel")
)

FRAME_HISTORY_SIZE = 8
MIN_LOG_INTERVAL_SECONDS = 30
ANOMALY_COOLDOWN_SECONDS = 30

model_lock = threading.Lock()
model_state = {
    "yolo": None,
    "csrnet": None,
    "csrnet_checked": False,
}

# Recent frame data is kept per camera in this process.
# For multiple workers, use shared storage instead.
frame_histories = {}
frame_history_lock = threading.Lock()


# ---------------------------------------------------------
# MODEL LOADING
# ---------------------------------------------------------

def get_yolo_model():
    """Load YOLO only when first needed."""
    if model_state["yolo"] is not None:
        return model_state["yolo"]

    with model_lock:
        if model_state["yolo"] is None:
            from ultralytics import YOLO
            model_state["yolo"] = YOLO(YOLO_MODEL_PATH)

    return model_state["yolo"]


def get_csrnet_model():
    """
    Load an existing CSRNet Caffe model if its files exist.
    Returns None when CSRNet files are unavailable.
    """
    if model_state["csrnet_checked"]:
        return model_state["csrnet"]

    with model_lock:
        if not model_state["csrnet_checked"]:
            if (
                Path(CSRNET_PROTOTXT).exists()
                and Path(CSRNET_WEIGHTS).exists()
            ):
                model_state["csrnet"] = cv2.dnn.readNetFromCaffe(
                    CSRNET_PROTOTXT,
                    CSRNET_WEIGHTS,
                )

            model_state["csrnet_checked"] = True

    return model_state["csrnet"]


# ---------------------------------------------------------
# FRAME DECODING
# ---------------------------------------------------------

def decode_frame(frame_string):
    """Decode a base64 webcam frame into an OpenCV image."""
    if not frame_string:
        raise ValueError("Frame data is missing.")

    if "," in frame_string and frame_string.startswith("data:"):
        frame_string = frame_string.split(",", 1)[1]

    try:
        raw_data = base64.b64decode(frame_string, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("Invalid base64 frame data.")

    image_array = np.frombuffer(raw_data, dtype=np.uint8)
    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if frame is None:
        raise ValueError("Unable to decode the image.")

    return frame


def image_to_base64(image, extension=".jpg"):
    success, encoded = cv2.imencode(extension, image)

    if not success:
        return None

    return base64.b64encode(encoded.tobytes()).decode("utf-8")


# ---------------------------------------------------------
# YOLO CROWD DETECTION
# ---------------------------------------------------------

def detect_people_yolo(frame):
    """
    Detect people using YOLO COCO class 0.
    Returns person count, bounding boxes and annotated image.
    """
    model = get_yolo_model()

    results = model.predict(
        source=frame,
        classes=[0],
        conf=0.20,
        imgsz=640,
        verbose=False,
    )

    result = results[0]
    annotated = frame.copy()
    people = []

    if result.boxes is not None:
        for box in result.boxes:
            coordinates = box.xyxy[0].cpu().numpy().astype(int)
            x1, y1, x2, y2 = coordinates.tolist()

            confidence = float(box.conf[0].cpu().item())

            people.append({
                "x1": max(0, x1),
                "y1": max(0, y1),
                "x2": min(frame.shape[1] - 1, x2),
                "y2": min(frame.shape[0] - 1, y2),
                "confidence": confidence,
                "center_x": (x1 + x2) // 2,
                "center_y": (y1 + y2) // 2,
            })

            cv2.rectangle(
                annotated,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2,
            )

            cv2.putText(
                annotated,
                f"Person {confidence:.2f}",
                (x1, max(y1 - 8, 15)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

    return len(people), people, annotated


# ---------------------------------------------------------
# CSRNET DENSITY ESTIMATION
# ---------------------------------------------------------

def predict_csrnet_density(frame):
    """
    Baseline CSRNet inference.
    Preprocessing must match the specific model used for training.
    """
    model = get_csrnet_model()

    if model is None:
        return None, None

    resized = cv2.resize(frame, (224, 224))
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

    blob = cv2.dnn.blobFromImage(
        rgb.astype(np.float32),
        scalefactor=1.0,
        size=(224, 224),
        mean=(0, 0, 0),
        swapRB=False,
        crop=False,
    )

    model.setInput(blob)
    density_map = model.forward()

    estimated_count = max(
        0,
        int(round(float(np.sum(density_map))))
    )

    density_map = np.squeeze(density_map)

    return estimated_count, density_map


def create_density_heatmap(frame, density_map=None):
    """
    Produce a visual heatmap.
    If a CSRNet density map is unavailable, use person detections
    as approximate spatial density points.
    """
    height, width = frame.shape[:2]

    heatmap = np.zeros((height, width), dtype=np.float32)

    if density_map is not None and density_map.ndim == 2:
        resized_map = cv2.resize(
            density_map.astype(np.float32),
            (width, height),
        )
        heatmap = np.maximum(resized_map, 0)

    else:
        # Approximate visualization from detected people.
        # This is not a trained density estimator.
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        heatmap = cv2.GaussianBlur(
            gray.astype(np.float32) * 0,
            (0, 0),
            12,
        )

    if heatmap.max() > 0:
        normalized = cv2.normalize(
            heatmap,
            None,
            0,
            255,
            cv2.NORM_MINMAX,
        ).astype(np.uint8)
    else:
        normalized = np.zeros((height, width), dtype=np.uint8)

    colored = cv2.applyColorMap(normalized, cv2.COLORMAP_JET)

    overlay = cv2.addWeighted(frame, 0.55, colored, 0.45, 0)

    return overlay


# ---------------------------------------------------------
# SPATIAL ANALYSIS: ZONE-WISE DENSITY
# ---------------------------------------------------------

def calculate_zone_density(people, frame_width, frame_height, rows=3, cols=3):
    """
    Divide camera image into a 3x3 grid.
    Count detected person centres in each zone.
    """
    zones = {}

    for row in range(rows):
        for col in range(cols):
            zone_name = f"R{row + 1}C{col + 1}"
            zones[zone_name] = {
                "people_count": 0,
                "zone_area_pixels": (
                    (frame_width / cols) * (frame_height / rows)
                ),
            }

    for person in people:
        x = person["center_x"]
        y = person["center_y"]

        col = min(cols - 1, max(0, int(x / frame_width * cols)))
        row = min(rows - 1, max(0, int(y / frame_height * rows)))

        zone_name = f"R{row + 1}C{col + 1}"
        zones[zone_name]["people_count"] += 1

    for zone in zones.values():
        zone["people_per_10000_pixels"] = round(
            zone["people_count"] /
            max(zone["zone_area_pixels"], 1) * 10000,
            3,
        )

    return zones


# ---------------------------------------------------------
# OPTICAL FLOW / CROWD MOTION
# ---------------------------------------------------------

def calculate_optical_flow(camera_id, frame):
    """
    Farneback optical flow compares the previous and current frames.
    It estimates image motion, not individual pedestrian trajectories.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    with frame_history_lock:
        history = frame_histories.setdefault(
            camera_id,
            deque(maxlen=FRAME_HISTORY_SIZE),
        )

        previous_gray = history[-1]["gray"] if history else None

        flow_result = {
            "available": False,
            "mean_magnitude": 0.0,
            "moving_pixel_ratio": 0.0,
            "mean_direction_degrees": 0.0,
            "motion_level": "UNKNOWN",
        }

        if previous_gray is not None:
            flow = cv2.calcOpticalFlowFarneback(
                previous_gray,
                gray,
                None,
                0.5,
                3,
                15,
                3,
                5,
                1.2,
                0,
            )

            magnitude, angle = cv2.cartToPolar(
                flow[..., 0],
                flow[..., 1],
                angleInDegrees=True,
            )

            mean_magnitude = float(np.mean(magnitude))
            moving_ratio = float(np.mean(magnitude > 2.0))
            mean_angle = float(np.mean(angle))

            if mean_magnitude < 0.5:
                motion_level = "LOW"
            elif mean_magnitude < 2.5:
                motion_level = "MODERATE"
            else:
                motion_level = "HIGH"

            flow_result = {
                "available": True,
                "mean_magnitude": round(mean_magnitude, 3),
                "moving_pixel_ratio": round(moving_ratio, 4),
                "mean_direction_degrees": round(mean_angle, 2),
                "motion_level": motion_level,
            }

        history.append({
            "gray": gray,
            "timestamp": timezone.now().isoformat(),
        })

    return flow_result


# ---------------------------------------------------------
# TEMPORAL / FRAME SEQUENCE ANALYSIS
# ---------------------------------------------------------

def get_previous_count(camera):
    previous_log = (
        CrowdDensityLog.objects
        .filter(camera=camera)
        .order_by("-recorded_at")
        .first()
    )

    return previous_log.estimated_crowd_count if previous_log else None


def calculate_temporal_analysis(current_count, previous_count, capacity):
    if previous_count is None:
        change = 0
        change_percent = 0.0
    else:
        change = current_count - previous_count
        change_percent = round(
            change / max(previous_count, 1) * 100,
            2,
        )

    capacity_percent = round(
        current_count / max(capacity, 1) * 100,
        2,
    )

    return {
        "current_count": current_count,
        "previous_logged_count": previous_count,
        "count_change": change,
        "change_percent": change_percent,
        "capacity_percent": capacity_percent,
        "sequence_status": (
            "RAPID_INCREASE"
            if change >= max(10, int(max(previous_count or 0, 1) * 0.5))
            else "STABLE_OR_NORMAL"
        ),
    }


# ---------------------------------------------------------
# ALTERNATIVE ANOMALY DETECTION
# ---------------------------------------------------------

def detect_anomalies(
    current_count,
    capacity,
    previous_count,
    zones,
    optical_flow,
):
    """
    Explainable rule-based alternative to a trained STCAE model.
    Results are heuristic indicators, not a validated stampede predictor.
    """
    anomalies = []

    capacity_percent = current_count / max(capacity, 1)

    if capacity_percent >= 1.0:
        anomalies.append({
            "type": "ABNORMAL_ACCUMULATION",
            "confidence": 0.95,
            "severity": "CRITICAL",
            "reason": "Estimated crowd count reached or exceeded safe capacity.",
        })
    elif capacity_percent >= 0.90:
        anomalies.append({
            "type": "ABNORMAL_ACCUMULATION",
            "confidence": 0.85,
            "severity": "CRITICAL",
            "reason": "Estimated crowd occupancy is at least 90% of capacity.",
        })
    elif capacity_percent >= 0.75:
        anomalies.append({
            "type": "PROLONGED_CONGESTION",
            "confidence": 0.70,
            "severity": "HIGH",
            "reason": "Estimated crowd occupancy is at least 75% of capacity.",
        })

    if previous_count is not None:
        increase = current_count - previous_count
        required_increase = max(10, int(max(previous_count, 1) * 0.5))

        if increase >= required_increase:
            anomalies.append({
                "type": "STAMPEDE_RUSH",
                "confidence": 0.75,
                "severity": "HIGH",
                "reason": (
                    f"Count increased by {increase} since the last saved log."
                ),
            })

    busiest_zone = max(
        zones.items(),
        key=lambda item: item[1]["people_count"],
    ) if zones else None

    if busiest_zone and current_count >= 10:
        busiest_count = busiest_zone[1]["people_count"]

        if busiest_count / max(current_count, 1) >= 0.60:
            anomalies.append({
                "type": "ABNORMAL_ACCUMULATION",
                "confidence": 0.65,
                "severity": "HIGH",
                "reason": (
                    f"Most detections are concentrated in zone "
                    f"{busiest_zone[0]}."
                ),
            })

    if (
        optical_flow.get("available")
        and optical_flow.get("motion_level") == "HIGH"
        and current_count >= 10
    ):
        anomalies.append({
            "type": "TURBULENCE",
            "confidence": 0.60,
            "severity": "HIGH",
            "reason": (
                "High image-motion magnitude detected in a populated frame. "
                "This alone does not prove panic or stampede."
            ),
        })

    return anomalies


# ---------------------------------------------------------
# RISK IDENTIFICATION
# ---------------------------------------------------------

def identify_risk(current_count, capacity):
    percentage = current_count / max(capacity, 1) * 100

    if percentage >= 90:
        return "CRITICAL", "CRITICAL", percentage
    if percentage >= 75:
        return "HIGH", "HIGH", percentage
    if percentage >= 50:
        return "MODERATE", "MODERATE", percentage

    return "NORMAL", "LOW", percentage


def severity_for_anomaly(anomalies):
    if any(a["severity"] == "CRITICAL" for a in anomalies):
        return "CRITICAL"
    if any(a["severity"] == "HIGH" for a in anomalies):
        return "HIGH"
    return "MEDIUM"


# ---------------------------------------------------------
# DATABASE: SAVE DENSITY, ANOMALY AND ALERT
# ---------------------------------------------------------

def save_density_log(camera, count, status, heatmap_bytes):
    density_log = CrowdDensityLog(
        camera=camera,
        estimated_crowd_count=max(0, int(count)),
        status=status,
    )

    if heatmap_bytes:
        density_log.density_map_image.save(
            f"camera_{camera.pk}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.jpg",
            ContentFile(heatmap_bytes),
            save=False,
        )

    density_log.save()
    return density_log


def save_anomaly_log(camera, anomaly, frame_bytes):
    anomaly_log = AnomalyDetectionLog(
        camera=camera,
        anomaly_type=anomaly["type"],
        confidence_score=max(
            0.0,
            min(1.0, float(anomaly["confidence"])),
        ),
    )

    # frame_snapshot is required by the supplied model.
    anomaly_log.frame_snapshot.save(
        f"camera_{camera.pk}_anomaly_{timezone.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg",
        ContentFile(frame_bytes),
        save=False,
    )

    anomaly_log.save()
    return anomaly_log


def create_emergency_alert(
    camera,
    density_log,
    anomaly_log,
    anomalies,
    risk_level,
):
    """
    Create an in-app alert. No email is sent.
    Avoid creating a duplicate active alert for the same camera,
    area and anomaly type within the cooldown period.
    """
    if not anomalies and risk_level not in ("HIGH", "CRITICAL"):
        return None

    area = camera.area
    severity = severity_for_anomaly(anomalies) if anomalies else (
        "CRITICAL" if risk_level == "CRITICAL" else "HIGH"
    )

    if anomalies:
        primary = max(
            anomalies,
            key=lambda a: (
                2 if a["severity"] == "CRITICAL"
                else 1 if a["severity"] == "HIGH"
                else 0,
                a["confidence"],
            ),
        )
        title = primary["type"].replace("_", " ").title()
        description = primary["reason"]
    else:
        title = f"{risk_level.title()} Crowd Risk"
        description = (
            f"Camera {camera.camera_identifier} reports "
            f"{risk_level.lower()} crowd risk."
        )

    cooldown_start = timezone.now() - timedelta(
        seconds=ANOMALY_COOLDOWN_SECONDS
    )

    existing = EmergencyAlert.objects.filter(
        area=area,
        status="ACTIVE",
        title=title,
        created_at__gte=cooldown_start,
    ).first()

    if existing:
        return existing

    instructions = (
        "Verify the camera feed and assess the scene. "
        "If danger is confirmed, notify the responsible safety team, "
        "keep exits accessible, and follow the site's emergency plan. "
        "Do not direct people into unsafe routes."
    )

    return EmergencyAlert.objects.create(
        area=area,
        emergency_department=None,
        density_log=density_log,
        anomaly_log=anomaly_log,
        severity=severity,
        title=title,
        description=description,
        public_instructions=instructions,
        status="ACTIVE",
    )


# ---------------------------------------------------------
# CAMERA MONITORING PAGE
# ---------------------------------------------------------

def camera_monitoring(request):
    cameras = (
        CCTVCamera.objects
        .select_related("area")
        .all()
        .order_by("camera_identifier")
    )

    return render(
        request,
        "camera/camera_monitoring.html",
        {"cameras": cameras},
    )




@require_POST
@csrf_protect
def live_crowd_predict(request):
    try:
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({
                "status": "error",
                "message": "Invalid JSON request.",
            }, status=400)

        camera_id = payload.get("camera_id")
        frame_string = payload.get("frame")

        if not camera_id or not frame_string:
            return JsonResponse({
                "status": "error",
                "message": "camera_id and frame are required.",
            }, status=400)

        camera = get_object_or_404(
            CCTVCamera.objects.select_related("area"),
            pk=camera_id,
        )

        frame = decode_frame(frame_string)

        # 1. YOLO person detection
        yolo_count, people, annotated_frame = detect_people_yolo(frame)

        # 2. CSRNet density estimation, if configured
        csrnet_count, density_map = predict_csrnet_density(frame)

        # YOLO count is the primary operational count.
        # CSRNet estimate is returned separately for comparison.
        current_count = yolo_count

        area = camera.area
        capacity = max(int(area.max_crowd_capacity or 1), 1)

        # 3. Spatial analysis / zone-wise density
        height, width = frame.shape[:2]
        zones = calculate_zone_density(
            people,
            width,
            height,
            rows=3,
            cols=3,
        )

        # 4. Optical flow and crowd motion
        optical_flow = calculate_optical_flow(camera.pk, frame)

        # 5. Temporal analysis using the previous saved log
        previous_count = get_previous_count(camera)

        temporal = calculate_temporal_analysis(
            current_count,
            previous_count,
            capacity,
        )

        # 6. Crowd risk identification
        crowd_status, risk_level, capacity_percent = identify_risk(
            current_count,
            capacity,
        )

        # 7. Alternative anomaly detection
        anomalies = detect_anomalies(
            current_count,
            capacity,
            previous_count,
            zones,
            optical_flow,
        )

        # 8. Density heatmap
        heatmap_overlay = create_density_heatmap(frame, density_map)
        heatmap_base64 = image_to_base64(heatmap_overlay)
        annotated_base64 = image_to_base64(annotated_frame)

        _, heatmap_bytes = cv2.imencode(".jpg", heatmap_overlay)
        _, frame_bytes = cv2.imencode(".jpg", frame)

        now = timezone.now()
        latest_log = (
            CrowdDensityLog.objects
            .filter(camera=camera)
            .order_by("-recorded_at")
            .first()
        )

        should_save_density = (
            latest_log is None
            or (now - latest_log.recorded_at).total_seconds()
            >= MIN_LOG_INTERVAL_SECONDS
            or bool(anomalies)
        )

        saved_density_log = None
        saved_anomaly_logs = []
        alert_data = None

        with transaction.atomic():
            # 9. Update Area risk level
            area.current_risk_level = risk_level
            area.save(update_fields=["current_risk_level"])

            # 10. Save crowd density record
            if should_save_density:
                saved_density_log = save_density_log(
                    camera,
                    current_count,
                    crowd_status,
                    heatmap_bytes.tobytes(),
                )

            # 11. Save anomaly records, deduplicated per camera/type
            for anomaly in anomalies:
                cooldown_key = (
                    f"crowdsense_anomaly_{camera.pk}_{anomaly['type']}"
                )

                if cache.get(cooldown_key):
                    continue

                anomaly_log = save_anomaly_log(
                    camera,
                    anomaly,
                    frame_bytes.tobytes(),
                )

                saved_anomaly_logs.append(anomaly_log)

                cache.set(
                    cooldown_key,
                    True,
                    ANOMALY_COOLDOWN_SECONDS,
                )

            # 12. Create website/database alert, no email
            if anomalies or risk_level in ("HIGH", "CRITICAL"):
                density_for_alert = saved_density_log or latest_log

                primary_anomaly_log = (
                    saved_anomaly_logs[0]
                    if saved_anomaly_logs
                    else None
                )

                alert = create_emergency_alert(
                    camera=camera,
                    density_log=density_for_alert,
                    anomaly_log=primary_anomaly_log,
                    anomalies=anomalies,
                    risk_level=risk_level,
                )

                if alert:
                    alert_data = {
                        "id": alert.pk,
                        "title": alert.title,
                        "description": alert.description,
                        "severity": alert.severity,
                        "status": alert.status,
                        "public_instructions": alert.public_instructions,
                        "created_at": alert.created_at.isoformat(),
                    }

        # STCAE is not loaded here unless you supply a trained model.
        # This implementation uses the rule-based alternative instead.
        return JsonResponse({
            "status": "ok",
            "camera_id": camera.pk,
            "camera_identifier": camera.camera_identifier,

            "total_crowd_count": current_count,
            "yolo_count": yolo_count,
            "csrnet_count": csrnet_count,

            "capacity": capacity,
            "capacity_percentage": round(capacity_percent, 2),
            "crowd_status": crowd_status,
            "risk_level": risk_level,

            "spatial_analysis": {
                "zone_count": len(zones),
                "zones": zones,
                "busiest_zone": (
                    max(
                        zones,
                        key=lambda zone: zones[zone]["people_count"],
                    )
                    if zones else None
                ),
            },

            "temporal_analysis": temporal,
            "frame_sequence_analysis": {
                "history_length": len(frame_histories.get(camera.pk, [])),
                "status": temporal["sequence_status"],
            },

            "crowd_motion": optical_flow,
            "optical_flow": optical_flow,

            "anomaly_detection": {
                "method": "Rule-based alternative + spatial/temporal/flow indicators",
                "stcae_available": False,
                "stcae_note": (
                    "A trained STCAE model is not configured. "
                    "The returned anomalies come from the alternative rules."
                ),
                "anomaly_count": len(anomalies),
                "anomalies": anomalies,
            },

            "flow_guided_detection": {
                "available": optical_flow["available"],
                "motion_level": optical_flow["motion_level"],
                "note": (
                    "Optical-flow motion indicators are available; "
                    "a separately trained flow-guided classifier is not configured."
                ),
            },

            "risk_identification": {
                "risk_level": risk_level,
                "capacity_percentage": round(capacity_percent, 2),
                "anomaly_count": len(anomalies),
            },

            "density_temporal_anomaly": {
                "count_change": temporal["count_change"],
                "change_percent": temporal["change_percent"],
                "capacity_percentage": temporal["capacity_percent"],
                "anomalies": anomalies,
            },

            "heatmap": (
                f"data:image/jpeg;base64,{heatmap_base64}"
                if heatmap_base64 else None
            ),
            "annotated_frame": (
                f"data:image/jpeg;base64,{annotated_base64}"
                if annotated_base64 else None
            ),

            "saved_to_database": (
                saved_density_log is not None
                or bool(saved_anomaly_logs)
            ),
            "density_log_id": (
                saved_density_log.pk if saved_density_log else None
            ),
            "anomaly_logs_saved": len(saved_anomaly_logs),
            "alert": alert_data,
            "alert_created": alert_data is not None,
            "alert_message": (
                alert_data["title"] if alert_data else None
            ),
            "timestamp": now.isoformat(),
        })

    except CCTVCamera.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": "Camera not found.",
        }, status=404)

    except ValueError as exc:
        return JsonResponse({
            "status": "error",
            "message": str(exc),
        }, status=400)

    except Exception as exc:
        # Log the full traceback in the Django server console.
        import logging
        logging.getLogger(__name__).exception(
            "Live crowd prediction failed"
        )

        return JsonResponse({
            "status": "error",
            "message": "Crowd prediction failed. Check the Django server console.",
        }, status=500)
