
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



    path('department_home/', views.department_home, name='department_home'),

    path('dept_view_user_reports/', views.dept_view_user_reports, name='dept_view_user_reports'),
    path('dept_update_user_report_status/<int:report_id>/', views.dept_update_user_report_status, name='dept_update_user_report_status'),

    path('dept_manage_instructions/', views.dept_manage_instructions, name='dept_manage_instructions'),
    path('dept_delete_instruction/<int:instruction_id>/', views.dept_delete_instruction, name='dept_delete_instruction'),
    path('dept_view_profile/', views.dept_view_profile, name='dept_view_profile'),
    path('dept_change_password/', views.dept_change_password, name='dept_change_password'),
    path('dept_view_areas/', views.dept_view_areas, name='dept_view_areas'),

    path('dept_live_density/', views.dept_live_density_console, name='dept_live_density'),

    path('dept_density_maps/', views.dept_density_maps, name='dept_density_maps'),
    path('dept_view_crowd_count/', views.dept_view_crowd_count, name='dept_view_crowd_count'),

    path('dept_high_density/', views.dept_high_density, name='dept_high_density'),
    path('dept_view_anomalies/', views.dept_view_anomalies, name='dept_view_anomalies'),

    path('dept_receive_alerts/', views.dept_receive_alerts, name='dept_receive_alerts'),
    path('dept_acknowledge_alert/<int:alert_id>/', views.dept_acknowledge_alert, name='dept_acknowledge_alert'),

    path('dept_assigned_volunteers/', views.dept_assigned_volunteers, name='dept_assigned_volunteers'),
    path('dept_assign_tasks/', views.dept_assign_tasks, name='dept_assign_tasks'),

    path('dept_previous_incidents/', views.dept_previous_incidents, name='dept_previous_incidents'),

    path('dept_monitor_volunteer_response/', views.dept_monitor_volunteer_response, name='dept_monitor_volunteer_response'),



    # flutter=======================================

    path('app_login/', views.app_login, name='app_login'),
    # path('updatelocation/', views.updatelocation, name='updatelocation'),
    path('user_view_area/', views.user_view_area, name='user_view_area'),
    path('user_register/', views.user_register, name='user_register'),
    path('user_change_password/', views.user_change_password, name='user_change_password'),
    path('user_view_profile/', views.user_view_profile, name='user_view_profile'),
    path('user_edit_profile/', views.user_edit_profile, name='user_edit_profile'),
    path('user_view_emergency_department/', views.user_view_emergency_department, name='user_view_emergency_department'),
    path('user_view_emergency_alerts/', views.user_view_emergency_alerts, name='user_view_emergency_alerts'),

    path('user_submit_complaint/', views.user_submit_complaint, name='user_submit_complaint'),
    path('user_view_complaints/', views.user_view_complaints, name='user_view_complaints'),


    path('user_submit_feedback/', views.user_submit_feedback, name='user_submit_feedback'),
    path('user_view_feedback/', views.user_view_feedback, name='user_view_feedback'),

    path('user_add_emergency_report/', views.user_add_emergency_report, name='user_add_emergency_report'),
    path('user_view_emergency_reports/', views.user_view_emergency_reports, name='user_view_emergency_reports'),
    path('user_delete_emergency_report/', views.user_delete_emergency_report, name='user_delete_emergency_report'),


    path('user_view_emergency_instructions/', views.user_view_emergency_instructions, name='user_view_emergency_instructions'),
    path('user_view_crowd_density/', views.user_view_crowd_density, name='user_view_crowd_density'),
    path('user_view_all_crowd_status/', views.user_view_all_crowd_status, name='user_view_all_crowd_status'),
    path('user_view_area_risk_level/', views.user_view_area_risk_level, name='user_view_area_risk_level'),

    # volunteeer=========================================================

    path('updatelocation/', views.updatelocation, name='updatelocation'),
    path('volunteer_view_profile/', views.volunteer_view_profile, name='volunteer_view_profile'),
    path('update_volunteer_profile_place/', views.update_volunteer_profile_place, name='update_volunteer_profile_place'),
    path('volunteer_change_password/', views.volunteer_change_password, name='volunteer_change_password'),
    path('volunteer_view_assigned_department/', views.volunteer_view_assigned_department, name='volunteer_view_assigned_department'),
    path('volunteer_view_emergency_alerts/', views.volunteer_view_emergency_alerts, name='volunteer_view_emergency_alerts'),
    path('volunteer_view_tasks/', views.volunteer_view_tasks, name='volunteer_view_tasks'),
    path('volunteer_update_task_status/', views.volunteer_update_task_status, name='volunteer_update_task_status'),
    path('volunteer_view_emergency_instructions/', views.volunteer_view_emergency_instructions, name='volunteer_view_emergency_instructions'),
    path('volunteer_view_ground_reports/', views.volunteer_view_ground_reports, name='volunteer_view_ground_reports'),
    path('volunteer_add_ground_report/', views.volunteer_add_ground_report, name='volunteer_add_ground_report'),
    path('volunteer_delete_ground_report/', views.volunteer_delete_ground_report, name='volunteer_delete_ground_report'),
    path('get_volunteer_tasks_dropdown/', views.get_volunteer_tasks_dropdown, name='get_volunteer_tasks_dropdown'),
    path('volunteer_view_crowd_status/', views.volunteer_view_crowd_status, name='volunteer_view_crowd_status'),
    path('volunteer_dashboard_data/', views.volunteer_dashboard_data, name='volunteer_dashboard_data'),


    path('camera_monitoring/', views.camera_monitoring, name='camera_monitoring'),
    path("live_crowd_predict/",views.live_crowd_predict,name="live_crowd_predict",),



   ]
