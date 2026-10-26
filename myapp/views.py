from django.contrib import messages
from django.contrib.auth import logout, authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect, get_object_or_404

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
                return redirect('/myapp/admin_home/')


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
from django.db.models import Q
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