from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect, get_object_or_404
from bookings.models import Booking
from django.utils import timezone 
from django.utils.timezone import now, make_aware, is_naive

from django.http import HttpResponseRedirect
from django.urls import reverse

from bookings.forms import BookingForm

from django.http import JsonResponse
from django.core.serializers import serialize
from bookings.models import Booking, InstructorAvailability

from django.contrib import messages

from django.core.mail import send_mail
from django.conf import settings

from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST

from django.contrib.auth import get_user_model

from .forms import StudentProfileForm, InstructorProfileForm

from django.db.models import Q
from accounts.models import CustomUser

from django.core.paginator import Paginator

from collections import Counter
from django.db.models.functions import TruncMonth
from django.db.models import Count

from datetime import datetime
from collections import Counter
import calendar

from datetime import datetime, timedelta, date

from .forms import ReviewForm
from .models import Review

from django.db.models import Avg

import json

from django.shortcuts import render
from accounts.models import InstructorProfile

from .forms import InstructorProfileForm
from .forms import AddInstructorDetailsForm

import stripe

from bookings.models import Payment

from .models import Tip
from .forms import TipForm


@login_required 
def calendar_view(request):
    return render(request, 'dashboard/calendar.html')

@login_required
def booking_events_json(request):
    student = request.user
    
    bookings = Booking.objects.filter(student=student)
    events = []

    for booking in bookings:
        color = 'green' if booking.status == 'booked' else 'red'
        start_time = f"{booking.date}T{booking.time}"


        events.append({
            "title": f"Lesson with {booking.instructor.username}",
            "start": f"{booking.date}T{booking.time}",
            "color": color,
            "description": f"{booking.status.capitalize()} lesson on {booking.date} at {booking.time}",
            "booking_id": booking.id,
            "status": booking.status,
        })

    # available slots across instructors + skips booked ones
    availability = InstructorAvailability.objects.all()
    
    for slot in availability:
        is_taken = Booking.objects.filter(
            instructor=slot.instructor,
            date=slot.date,
            time=slot.time,
            status='booked'
        ).exists()

        if not is_taken:
            events.append({
                "title": f"Available: {slot.instructor.username}",
                "start": f"{slot.date}T{slot.time}",
                "color": "#007bff",
                "description": f"{slot.instructor.username} is available on {slot.date} at {slot.time}",
            })

    return JsonResponse(events, safe=False)


@login_required
def book_lesson(request):
    if request.method == 'POST':
        form = BookingForm(request.POST, student=request.user)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.student = request.user
            booking.status = 'booked'
            booking.save()
            messages.success(request, 'Lesson booked successfully!')

            # Send confirmation email
            html_body = render_to_string('email/lesson_confirmation.html', {
                'username': request.user.username,
                'instructor': booking.instructor.username,
                'date': booking.date,
                'time': booking.time,
            })
            subject = 'Lesson Booking Confirmation'
            from_email = settings.EMAIL_HOST_USER
            to_email = request.user.email

            email = EmailMultiAlternatives(subject, '', from_email, [to_email])
            email.attach_alternative(html_body, "text/html")
            email.send()

            # ✅ Redirect to confirmation page (NOT dashboard)
            return redirect('booking_confirmation', booking_id=booking.id)
        else:
            # Form invalid → re-render with errors
            return render(request, 'dashboard/book_lesson.html', {'form': form})
    else:
        initial_data = {}
        instructor_username = request.GET.get('instructor')
        if instructor_username:
            from accounts.models import CustomUser
            try:
                instructor = CustomUser.objects.get(username=instructor_username, role='instructor')
                initial_data['instructor'] = instructor.id
            except CustomUser.DoesNotExist:
                pass

        date = request.GET.get('date')
        time = request.GET.get('time')
        if date:
            initial_data['date'] = date
        if time:
            initial_data['time'] = time

        form = BookingForm(initial=initial_data)

    return render(request, 'dashboard/book_lesson.html', {'form': form})


@login_required
def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, student=request.user)
    return render(request, "dashboard/booking_confirmation.html", {"booking": booking})

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # permission check: only student/instructor can cancel
    if request.user != booking.student and request.user != booking.instructor:
        return render(request, '403.html')

    if not booking.time:
        messages.error(request, "This booking has no time set. Unable to cancel.")
        return redirect('student_dashboard')

    # Combine date and time into a single datetime
    lesson_datetime = datetime.combine(booking.date, booking.time)

    # Make lesson_datetime timezone-aware
    if is_naive(lesson_datetime):
        lesson_datetime = make_aware(lesson_datetime)

    current_time = now()

    # Debugging output (to be removed later)
    print("Booking datetime:", lesson_datetime)
    print("Current time:", current_time)
    print("Time until lesson:", lesson_datetime - current_time)

    if lesson_datetime - current_time < timedelta(hours=48):
        messages.error(request, "You can only cancel a lesson more than 48 hours before its scheduled time.")
        if request.user.role == 'student':
            return redirect('student_dashboard')
        elif request.user.role == 'instructor':
            return redirect('instructor_dashboard')
        else:
            return redirect('home')

    # POST request means actually cancel it
    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, "Lesson cancelled successfully.")

        # Send email
        subject = "Lesson Cancelled"
        message = render_to_string('email/lesson_cancelled.html', {
            'user': request.user,
            'booking': booking,
        })
        send_mail(
            subject,
            '',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[request.user.email],
            fail_silently=False,
            html_message=message,
        )

    # Redirect based on role
    if request.user.role == 'student':
        return redirect('student_dashboard')
    elif request.user.role == 'instructor':
        return redirect('instructor_dashboard')
    else:
        return redirect('home')


@login_required
def student_dashboard(request):
    user = request.user
    today = now().date()

    upcoming = (Booking.objects
                .filter(student=user, date__gte=today, status='booked')
                .order_by('date'))
    
    past = (Booking.objects
            .filter(student=user, date__lt=today)
            .order_by('-date'))
    
    # progress: completed lessons per month (for this student)
    completed_qs = (Booking.objects
                    .filter(student=user, status='completed'))
    
    monthly = (completed_qs
               .annotate(month=TruncMonth('date'))
               .values('month')
               .annotate(c=Count('id'))
               .order_by('month'))
    
    labels = [entry['month'].strftime('%b %Y') for entry in monthly if entry['month']]
    data = [entry['c'] for entry in monthly]

    total_completed = completed_qs.count()
    GOAL = 12
    progress_pct = int(min(100, (total_completed / GOAL) * 100)) if GOAL else 0


    return render(request, 'dashboard/student_dashboard.html', {
        'upcoming': upcoming,
        'past': past,
        'progress_labels_json':json.dumps(labels),
        'progress_data_json': json.dumps(data),
        'total_completed': total_completed,
        'goal': GOAL,
        'progress_pct': progress_pct
    })


@login_required
def student_profile_view(request):
    if request.user.role != 'student':
        return render(request, '403.html')
    
    student = request.user
    return render(request, 'dashboard/student_profile.html', {'student': student})

@login_required
def reschedule_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # only allow if current user is student/instructor linked to this booking
    if request.user != booking.student and request.user != booking.instructor:
        return render(request, '403.html')

    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking, student=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Lesson rescheduled successfully.")

            # send email
            subject = "Lesson Rescheduled"
            message = render_to_string('email/lesson_rescheduled.html', {
                'user': request.user,
                'booking': booking,
            })
            send_mail(
                subject,
                '',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[request.user.email],
                fail_silently=False,
                html_message=message,
            )

            # redirect based on role
            if request.user.role == 'student':
                return redirect('student_dashboard')
            elif request.user.role == 'instructor': 
                return redirect('instructor_dashboard')
            elif request.user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('home')
            
    else:
        form = BookingForm(instance=booking, student=request.user)

    return render(request, 'dashboard/reschedule_lesson.html', {'form': form, 'booking': booking})


@login_required
def instructor_dashboard(request):
    if request.user.role != 'instructor':
        return render(request, '403.html')
    
    instructor = request.user
    today = date.today()

    # for weaking hours calculations
    start_of_week = today - timedelta(days=today.weekday()) #Monday
    end_of_week = start_of_week + timedelta(days=6) #Sunday

    # count completed lessons this week
    weekly_hours = Booking.objects.filter(
        instructor=request.user,
        status='completed',
        date__range=[start_of_week, end_of_week]
    ).count()

    # for calculating pay for that week
    weekly_pay = weekly_hours * 55

    # query to count lessons
    total_bookings = Booking.objects.filter(instructor=instructor).count()
    upcoming_lessons = Booking.objects.filter(instructor=instructor, date__gte=timezone.now().date()).count()
    completed_lessons = Booking.objects.filter(instructor=instructor, status='completed').count()
    cancelled_lessons = Booking.objects.filter(instructor=instructor, status='cancelled').count()
    todays_lessons = Booking.objects.filter(instructor=instructor, date=today).order_by('time')

    # completed lessons without a review yet
    pending_reviews = (
        Booking.objects
        .filter(
            instructor=instructor,
            status='completed',
            date__lte=today,
            review__isnull=True
        )
        .order_by('-date', '-time')
    )
    pending_count = pending_reviews.count()
    pending_first = pending_reviews.first()
    
    return render(request, 'dashboard/instructor_dashboard.html', {
        'total_bookings': total_bookings,
        'upcoming_lessons': upcoming_lessons,
        'completed_lessons': completed_lessons,
        'cancelled_lessons':cancelled_lessons,
        'todays_lessons': todays_lessons,
        'weekly_hours': weekly_hours,
        'weekly_pay': weekly_pay,
        'pending_reviews': pending_reviews,
        'pending_count': pending_count,
        'pending_first': pending_first
    })


@login_required
def instructor_calendar(request):
    if request.user.role != 'instructor':
        return render(request, '403.html')
    return render(request, 'dashboard/instructor_calendar.html')

@login_required
def instructor_calendar_view(request):
    return render(request, 'dashboard/instructor_calendar.html')

@login_required
def instructor_calendar_data(request):
    instructor = request.user
    if request.user.role != 'instructor':
        return JsonResponse([], safe=False)
    
    bookings = Booking.objects.filter(instructor=request.user)
    events = []

    for booking in bookings:
        events.append({
            "title": f"Lesson with {booking.student.username}",
            "start":f"{booking.date}T{booking.time}",
            "color": "green" if booking.status == "booked" else "red",
            "status": booking.status,
            "booking_id": booking.id,
        })
        
    return JsonResponse(events, safe=False)

@login_required
def instructor_lessons_list(request, filter_type):
    if request.user.role != 'instructor':
        return render(request, '403.html')
    
    instructor = request.user
    today = timezone.now().date()

    if filter_type == 'total':
        lessons = Booking.objects.filter(instructor=instructor)
        title = "All Lessons"
    elif filter_type == 'upcoming':
        lessons = Booking.objects.filter(instructor=instructor, date__gte=today, status='booked')
        title = "Upcoming Lessons"
    elif filter_type == 'completed':
        lessons = Booking.objects.filter(instructor=instructor, status='completed')
        title = "Completed Lessons"
    elif filter_type == 'cancelled':
        lessons = Booking.objects.filter(instructor=instructor, status='cancelled')
        title = "Cancelled Lessons"
    else:
        return render(request, '404.html')
    
    lessons = lessons.order_by('-date', '-time')

    return render(request, 'dashboard/instructor_lesson_list.html', {
        'title': title,
        'lessons': lessons,
    })

@staff_member_required
def admin_dashboard(request):
    # Get filter input from GET parameters
    student_query = request.GET.get('student', '').strip()
    instructor_id = request.GET.get('instructor', '')
    status = request.GET.get('status', '')

    # Start with all bookings - base queryset
    bookings = Booking.objects.select_related('student', 'instructor').all()

    # Filter by student name/email
    if student_query:
        bookings = bookings.filter(
            Q(student__username__icontains=student_query) |
            Q(student__email__icontains=student_query)
        )

    # Filter by instructor
    if instructor_id:
        bookings = bookings.filter(instructor__id=instructor_id)

    # Filter by status
    if status:
        bookings = bookings.filter(status=status)

    # Order filtered bookings
    bookings = bookings.order_by('-date', '-time')

    # Stats and upcoming
    total_students = CustomUser.objects.filter(role='student').count()
    total_instructors = CustomUser.objects.filter(role='instructor').count()
    total_bookings = Booking.objects.count()

    upcoming = Booking.objects.filter(date__gte=timezone.now().date()).order_by('date', 'time')[:5]
    instructors = CustomUser.objects.filter(role='instructor')

    return render(request, 'dashboard/admin_dashboard.html', {
        'total_students': total_students,
        'total_instructors': total_instructors,
        'total_bookings': total_bookings,
        'upcoming': upcoming,
        'bookings': bookings,
        'instructors': instructors,
        'request': request
    })

@staff_member_required
def admin_calendar_data(request):
    bookings = Booking.objects.all()
    events = []

    for booking in bookings:
        if booking.status =="booked":
            color = "orange"
        elif booking.status =="completed":
            color = "green"
        elif booking.status =="cancelled":
            color = "red"
        else:
            color = "grey"

        events.append({
            "title": f"{booking.student.username} with {booking.instructor.username}",#
            "start": f"{booking.date}T{booking.time}",
            "color": color,
            "description": f"{booking.status.capitalize()} lesson",
            "status": booking.status.capitalize(),
            "booking_id": booking.id,
        })

    return JsonResponse(events, safe=False)

@login_required
def instructor_students_list(request):
    if request.user.role != 'instructor':
        return render(request, '403.html')

    students = CustomUser.objects.filter(
        role='student',
        student_bookings__instructor=request.user
    ).distinct()

    return render(request, 'dashboard/instructor_students_list.html', {
        'students': students
    })


@login_required
def instructor_student_detail(request, student_id):
    if request.user.role != 'instructor':
        return render(request, '403.html')
    
    student = get_object_or_404(CustomUser, id=student_id, role='student')
    bookings = Booking.objects.filter(instructor=request.user, student=student).order_by('-date', '-time')

    instructor = request.user

    lessons = Booking.objects.filter(instructor=request.user, student=student)

    # counts bookings by status
    status_counts = Counter(bookings.values_list('status', flat=True))

    # filtered lessons for chart: only completed ones
    completed_lessons = bookings.filter(status='completed')

    # bar chart: lessons per month
    monthly_counts = (bookings
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month'))
    
    # prepares data for chart
    months = [entry['month'].strftime('%b %Y') for entry in monthly_counts]
    lesson_counts = [entry['total'] for entry in monthly_counts]

    # compute counts
    status_counts = {
        'booked': lessons.filter(status='booked').count(),
        'completed': lessons.filter(status='completed').count(),
        'cancelled': lessons.filter(status='cancelled').count(),
    }

    # chart data from completed lessons only
    completed_lessons = bookings.filter(status='completed')
    monthly_counts = (
        completed_lessons
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    month = [entry['month'].strftime('%b %Y') for entry in monthly_counts]
    lesson_counts = [entry['count'] for entry in monthly_counts]

    # computes average on instructor to student detail page
    avg_rating = (
        Review.objects
        .filter(instructor=request.user, booking__student=student)
        .aggregate(avg=Avg('rating'))
        .get('avg')
    )

    # progress charts
    completed_qs = lessons.filter(status='completed')

    monthly_completed = (
        completed_qs
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )

    progress_labels = [entry['month'].strftime('%b %Y') for entry in monthly_completed]
    progress_data = [entry['total'] for entry in monthly_completed]

    # JSON for Chart.js
    progress_labels_json = json.dumps(progress_labels)
    progress_data_json = json.dumps(progress_data)

    # progress bar - goals
    total_completed = lessons.filter(status='completed').count()
    goal = 12
    progress_pct = int(round((total_completed / goal) * 100)) if goal else 0
    progress_pct = max(0, min(progress_pct, 100))
    
    return render(request, 'dashboard/instructor_student_detail.html', {
        'student': student,
        'lessons': lessons,
        'bookings': bookings,
        'status_counts': status_counts,
        'months': months,
        'lesson_counts': lesson_counts,
        'request': request,
        'avg_rating': avg_rating,
        'progress_labels_json': progress_labels_json,
        'progress_data_json': progress_data_json,
        'total_completed': total_completed,
        'goal': goal,
        'progress_pct': progress_pct

    })

@staff_member_required
def admin_calendar_view(request):
    return render(request, 'dashboard/admin_calendar.html')

@staff_member_required
@require_POST
def admin_cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.status = 'cancelled' 
    booking.save()
    messages.success(request, "Booking Cancelled.")
    return redirect('admin_dashboard')

@staff_member_required
@require_POST
def admin_complete_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.status = 'completed' 
    booking.save()
    messages.success(request, f"Marked booking #{booking.id} as Completed.")
    return redirect('admin_dashboard')

@staff_member_required
@require_POST
def admin_delete_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.delete()
    messages.success(request, "Booking Deleted.")
    return redirect('admin_dashboard')

@staff_member_required
def admin_edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking, student=booking.student)
        if form.is_valid():
            form.save()
            messages.success(request, "Booking updated successfully.")
            return redirect('admin_dashboard')
    else:
        form = BookingForm(instance=booking, student=booking.student)

    return render(request, 'dashboard/admin_edit_booking.html', {
        'form': form,
        'booking': booking
    })


User = get_user_model()

@staff_member_required
def view_all_students(request):
    students = User.objects.filter(role='student')
    return render(request, 'dashboard/view_all_students.html', {'students': students})

@staff_member_required
def view_all_instructors(request):
    instructors = User.objects.filter(role='instructor')
    return render(request, 'dashboard/view_all_instructors.html', {'instructors': instructors})


@staff_member_required
def student_profile(request, student_id):
    student = get_object_or_404(User, id=student_id, role='student')
    return render(request, 'dashboard/student_profile.html', {'student': student})

@staff_member_required
def instructor_profile(request, instructor_id):
    instructor = get_object_or_404(User, id=instructor_id, role='instructor')
    return render(request, 'dashboard/instructor_profile.html', {'instructor': instructor})


@login_required
def dashboard_home_redirect(request):
    user = request.user

    if user.is_superuser or user.is_staff:
        return redirect('admin_dashboard')
    elif hasattr(user, 'role'):
        if user.role == 'instructor':
            return redirect('instructor_dashboard')
        elif user.role == 'student':
            return redirect('student_dashboard')
        
    return redirect('login')


@login_required
def edit_student_profile(request):
    form = StudentProfileForm(instance=request.user)
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('student_profile')
    return render(request, 'dashboard/edit_student_profile.html', {'form': form})
    
@login_required
def edit_instructor_profile(request):
    if request.user.role != 'instructor':
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You are not authorized to view this page.")
    
    if request.method == 'POST':
        form = InstructorProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('instructor_dashboard')
        else:
            form = InstructorProfileForm(instance=request.user)

        return render(request, 'dashboard/edit_instructor_profile.html', {'form': form}) 
    
@login_required
def leave_review(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, instructor=request.user)

    if booking.status != 'completed':
        messages.error(request, "You can only review completed lessons.")
        return redirect('instructor_dashboard')

    if Review.objects.filter(booking=booking).exists():
        messages.info(request, "A review already exists for this lesson.")
        return redirect('instructor_dashboard')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.instructor = request.user
            review.save()
            messages.success(request, "Review submitted.")
            return redirect('instructor_dashboard')
    else:
        form = ReviewForm()

    return render(request, 'dashboard/leave_review.html', {
        'form': form, 
        'booking': booking
    })



@login_required
def my_reviews(request):
    if request.user.role != 'instructor':
        return render(request, '403.html')
    reviews = (
        Review.objects
        .filter(instructor=request.user)
        .select_related('booking__student')
        .order_by('-created_at')
    )
    return render(request, 'dashboard/my_reviews.html', {'reviews': reviews})

@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, instructor=request.user)

    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Review updated successfully.")
            return redirect('instructor_dashboard')
    else:
        form = ReviewForm(instance=review)

    return render(request, "dashboard/edit_review.html", {"form": form})
    

@login_required
def delete_review(request, review_id):
    if request.user.role != 'instructor':
        return render (request, '403.html')
    
    review = get_object_or_404(Review, id=review_id, instructor=request.user)
    if request.method == 'POST':
        review.delete()
        messages.success(request, "Review deleted")
        return  redirect('my_reviews')
    
    return render(request, 'dashboard/delete_review_confirm.html', {'review': review})
    
    
def meet_instructors(request):
    # Pull all users who are instructors
    instructors_qs = CustomUser.objects.filter(role='instructor').order_by('first_name', 'last_name')

    # Build a safe list for the template (handles missing InstructorProfile)
    cards = []
    for u in instructors_qs:
        profile = getattr(u, 'instructorprofile', None)  # None if profile doesn’t exist
        cards.append({
            'id': u.id,
            'name': u.get_full_name() or u.username,
            'email': u.email,
            'phone': u.phone_number,
            'bio': (profile.bio if profile and profile.bio else "No bio available."),
            'car_type': (profile.car_type if profile and profile.car_type else "N/A"),
            'profile_picture': (
                profile.profile_picture.url if profile and profile.profile_picture
                else(u.profile_picture.url if u.profile_picture else None)
            )
        })

    return render(request, 'dashboard/meet_instructors.html', {
        'instructors': cards
    })


@login_required
def edit_instructor_profile(request):
    if request.user.role != 'instructor':
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You are not authorized to view this page.")
    
    if request.method == 'POST':
        form = InstructorProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('instructor_dashboard')
    else:
        form = InstructorProfileForm(instance=request.user)

    return render(request, 'dashboard/edit_instructor_profile.html', {'form': form})


@login_required
def add_instructor_details(request):
    profile, created = InstructorProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = AddInstructorDetailsForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Instructor details updated successfully.")
            return redirect('instructor_dashboard')
    else:
        form = AddInstructorDetailsForm(instance=profile)

    return render(request, 'dashboard/add_instructor_details.html', {'form': form})



stripe.api_key = settings.STRIPE_SECRET_KEY

def create_checkout_session(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, student=request.user)

    # Create a Payment record
    payment = Payment.objects.create(
        booking=booking,
        amount=55.00,  
    )

    # Stripe Checkout session
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'eur',
                'unit_amount': int(payment.amount * 100),  # Stripe uses cents
                'product_data': {
                    'name': f"Driving Lesson - {booking.date}",
                },
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(
            reverse('payment_success', args=[payment.id])
        ),
        cancel_url=request.build_absolute_uri(
            reverse('payment_cancel', args=[payment.id])
        ),
    )

    # Save Stripe intent ID
    payment.stripe_payment_intent = checkout_session['payment_intent']
    payment.save()

    return redirect(checkout_session.url)
    
def payment_success(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    payment.status = "paid"
    payment.save()
    return render(request, "dashboard/success.html", {"payment": payment})


def payment_cancel(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    payment.status = "failed"
    payment.save()
    return render(request, "dashboard/cancel.html", {"payment": payment})


@login_required
def add_tip(request):
    if request.user.role != "instructor":
        return redirect("student_dashboard")  # prevent students from submitting

    if request.method == "POST":
        form = TipForm(request.POST)
        if form.is_valid():
            tip = form.save(commit=False)
            tip.instructor = request.user
            tip.save()
            return redirect("list_tips")
    else:
        form = TipForm()

    return render(request, "dashboard/add_tip.html", {"form": form})

@login_required
def list_tips(request):
    tips = Tip.objects.all()
    return render(request, "dashboard/list_tips.html", {"tips": tips})

@login_required
def student_reviews(request):
    reviews = Review.objects.filter(booking__student=request.user).select_related('booking', 'instructor')

    return render(request, "dashboard/student_reviews.html", {
        "reviews": reviews
    })


@login_required
def contact_instructor(request):
    if request.method == "POST":
        instructor_id = request.POST.get("instructor_id")
        instructor = get_object_or_404(CustomUser, id=instructor_id, role="instructor")

        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        subject = f"New Contact from {name}"
        body = f"You have received a new message from {name} ({email}):\n\n{message}"

        send_mail(
            subject,
            body,
            email,  # from student
            [instructor.email],  # to instructor
            fail_silently=False,
        )

        messages.success(request, "Your message has been sent successfully!")
        return redirect("meet_instructors")

    return redirect("meet_instructors")