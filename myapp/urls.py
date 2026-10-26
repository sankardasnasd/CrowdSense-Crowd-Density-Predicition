
from django.contrib import admin
from django.urls import path,include

from myapp import views

urlpatterns = [

    path('public_page/',views.public_page),
    path('logout_page/',views.logout_page),
    path('login_page/',views.login_page),

    path('admin_home/',views.admin_home),
    path('admin_home_sub/',views.admin_home_sub),
    path('change_password/',views.change_password),
    path('manage_users/',views.manage_users),

    path('admin_manage_area/', views.admin_manage_area, name='admin_manage_area'),
    path("admin/area-search-location/",views.area_search_location,name="area_search_location",),
    path('admin_edit_area/<int:area_id>/', views.admin_edit_area, name='admin_edit_area'),
    path('admin_delete_area/<int:area_id>/', views.admin_delete_area, name='admin_delete_area'),


    path('manage_departments/', views.manage_departments, name='manage_departments'),
    path('edit_department/<int:dept_id>/', views.edit_department, name='edit_department'),
    path('delete_department/<int:dept_id>/', views.delete_department, name='delete_department'),

    path('manage_volunteers/', views.manage_volunteers, name='manage_volunteers'),
    path('edit_volunteer/<int:vol_id>/', views.edit_volunteer, name='edit_volunteer'),
    path('delete_volunteer/<int:vol_id>/', views.delete_volunteer, name='delete_volunteer'),

    path('manage_cameras/', views.manage_cameras, name='manage_cameras'),
    path('search_camera_sublocation/', views.search_camera_sublocation, name='search_camera_sublocation'),
    path('edit_camera/<int:cam_id>/', views.edit_camera, name='edit_camera'),
    path('delete_camera/<int:cam_id>/', views.delete_camera, name='delete_camera'),


    path('density_reports/', views.density_reports, name='density_reports'),
    path('view_anomalies/', views.view_anomalies, name='view_anomalies'),

    path('view_feedback/', views.view_feedback, name='view_feedback'),

    path('view_complaints/', views.view_complaints, name='view_complaints'),
    path('reply_complaint/<int:complaint_id>/', views.reply_complaint, name='reply_complaint'),

    path('view_alerts/', views.view_alerts, name='view_alerts'),
    path('update_alert_status/<int:alert_id>/', views.update_alert_status, name='update_alert_status'),


]
