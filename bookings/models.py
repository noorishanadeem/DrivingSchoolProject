from django.db import models
from accounts.models import CustomUser

class Booking(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='student_bookings')
    instructor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='instructor_bookings')
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=[
        ('booked', 'Booked'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='booked')
    create_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} -> {self.instructor.username} on {self.date} at {self.time}"

    def __str__(self):
        return f"lesson with {self.instructor.username} on {self.date} at {self.time}" 
    
class InstructorAvailability(models.Model):
    instructor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'instructor'})
    date = models.DateField()
    time = models.TimeField()

    def __str__(self):
        return f"{self.instructor.username} - {self.date} {self.time}"
    

# payment model for tracking
class Payment(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    stripe_payment_intent = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.booking} - {self.status}"