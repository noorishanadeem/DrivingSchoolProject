from django.urls import path
from . import views

urlpatterns = [
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('instructor/', views.instructor_dashboard, name='instructor_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),

    path('student/profile/', views.student_profile_view, name='student_profile'),

    path('admin/calendar/', views.admin_calendar_view, name='admin_calendar_view'),
    path('admin/calendar/data/', views.admin_calendar_data, name='admin_calendar_data'),
    path('admin/complete-booking/<int:booking_id>/', views.admin_complete_booking, name='admin_complete_booking'),
    path('admin/delete-booking/<int:booking_id>/', views.admin_delete_booking, name='admin_delete_booking'),
    path('admin/cancel-booking/<int:booking_id>/', views.admin_cancel_booking, name='admin_cancel_booking'),
    path('admin/edit-booking/<int:booking_id>/', views.admin_edit_booking, name='admin_edit_booking'),
    path('admin/students/', views.view_all_students, name='view_all_students'),
    path('admin/instructor/', views.view_all_instructors, name='view_all_instructors'),
    path('admin/student/<int:student_id>/', views.student_profile, name='student_profile'),
    path('admin/instructor/<int:instructor_id>/', views.instructor_profile, name='instructor_profile'),
    path('admin/instructor/edit/<int:instructor_id>/', views.edit_instructor_profile, name='edit_instructor_profile'),

    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('book-lesson/', views.book_lesson, name='book_lesson'),

    path('calendar/', views.calendar_view, name='calendar_view'),
    path('calendar/data/', views.booking_events_json, name='booking_events_json'),

    path('reschedule/<int:booking_id>/', views.reschedule_booking, name='reschedule_booking'),
    path('cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),

    path('instructor/calendar/', views.instructor_calendar, name='instructor_calendar'),
    path('instructor/calendar/data/', views.instructor_calendar_data, name='instructor_calendar_data'),
    path('instructor/lessons/<str:filter_type>/', views.instructor_lessons_list, name='instructor_lessons_list'),
    path('dashboard/instructor/students/', views.instructor_students_list, name='instructor_students_list'),
    path('dashboard/instructor/students/<int:student_id>/', views.instructor_student_detail, name='instructor_student_detail'),

    path('student/edit/', views.edit_student_profile, name='edit_student_profile'),
    path('instructor/edit/', views.edit_instructor_profile, name='edit_instructor_profile'),
    path('instructor/add-details/', views.add_instructor_details, name='add_instructor_details'),
    path('', views.dashboard_home_redirect),

    path('dashboard/leave-review/<int:booking_id>/', views.leave_review, name='leave_review'),
    path('instructor/reviews/', views.my_reviews, name='my_reviews'),
    path('instructor/reviews/<int:review_id>/edit/', views.edit_review, name='edit_review'),
    path('instructor/reviews/<int:review_id>/delete', views.delete_review, name='delete_review'),

    path('instructors/', views.meet_instructors, name='meet_instructors'),

    path("checkout/<int:booking_id>/", views.create_checkout_session, name="create_checkout_session"),
    path("success/<int:payment_id>/", views.payment_success, name="payment_success"),
    path("cancel/<int:payment_id>/", views.payment_cancel, name="payment_cancel"),

    path('dashboard/booking/<int:booking_id>/confirmation/', views.booking_confirmation, name='booking_confirmation'),

    path("tips/add/", views.add_tip,  name="add_tip"),
    path("tips/", views.list_tips, name="list_tips"),
    path("reviews/", views.student_reviews, name="student_reviews"),

    path("contact-instructor/", views.contact_instructor, name="contact_instructor"),

]