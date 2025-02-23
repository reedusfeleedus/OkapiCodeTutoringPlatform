from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from tutorials import views

urlpatterns = [
    path('course/add', views.create_course, name='course.create'),
    path('courses/', views.course_list, name='course_list'),

    path('sessions/',views.all_sessions,name="all_sessions"),
    path('invoices/', views.invoices, name='invoices'),

    path('invoices/mark_paid/<int:invoice_id>/', views.mark_invoice_paid, name='mark_invoice_paid'),

    path('dashboard/request/list',views.admin_request_list,name="admin.request.list"),
    path('dashboard/request/<int:request_id>',views.admin_request_details,name="admin.request.details"),
    # path('admin-dashboard/request/accept/<int:request_id>',views.admin_accept_request_session,name="admin.request.accept"),

    path('course/edit/<int:course_id>/', views.edit_course, name='course.edit'),
    path('course/delete/<int:course_id>/', views.delete_course, name='course.delete'),
    path('request_session/course_list', views.request_session_course_list, name='request_session.course_list'),
    path('request_session/<int:course_id>', views.request_session, name='request_session'),
    path('students/requests/',views.student_requests_list,name="student.requests_list"),
    path('open_ticket/',views.open_ticket,name="open_ticket"),
    path('tickets/',views.all_ticket,name="all_ticket"),
    path('ticket/<int:ticket_id>',views.ticket_details,name="ticket_details"),

]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


# create a dashboard for tutor just to display the sessions with detalis(time,student name,course name,date) one student

# create a page for tutor to add availabl time
