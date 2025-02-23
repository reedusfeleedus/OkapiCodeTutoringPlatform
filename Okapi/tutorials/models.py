from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from libgravatar import Gravatar

class User(AbstractUser):
    """Model used for user authentication, and team member related information."""

    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[RegexValidator(
            regex=r'^@\w{3,}$',
            message='Username must consist of @ followed by at least three alphanumericals'
        )]
    )
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    email = models.EmailField(unique=True, blank=False)
    role = models.CharField(choices=[ 
        ('Student', 'Student'),
        ('Tutor', 'Tutor'), 
        ('Admin', 'Admin')
    ], max_length=7, default='Student') #


    class Meta:
        """Model options."""

        ordering = ['last_name', 'first_name']

    def full_name(self):
        """Return a string containing the user's full name."""

        return f'{self.first_name} {self.last_name}'

    def gravatar(self, size=120):
        """Return a URL to the user's gravatar."""

        gravatar_object = Gravatar(self.email)
        gravatar_url = gravatar_object.get_image(size=size, default='mp')
        return gravatar_url

    def mini_gravatar(self):
        """Return a URL to a miniature version of the user's gravatar."""
        
        return self.gravatar(size=60)
    
class Course(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    desc = models.CharField(max_length=200)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    users = models.ManyToManyField(User, related_name='courses')

class Tutor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    courses = models.ManyToManyField(Course)
    years_exp = models.IntegerField()
    availability = models.JSONField()  # JSON of available times #Add validation later TBD
    rate = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[
            MinValueValidator(0.5),  
            MaxValueValidator(3.0)   
        ]
    )

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    courses = models.ManyToManyField(Course)  # courses they're enrolled in
    availability = models.JSONField()  # when they can take classes

# class RequestSession(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
#     course = models.ForeignKey(Course, on_delete=models.CASCADE,null=True)
#     availability = models.JSONField()
#     start_date = models.DateField()
#     end_date = models.DateField()
#     status = models.BooleanField(null=True)
#     tutor = models.ManyToManyField(User,related_name='request_sessions_tutor')
# Ali I changed this cos 
# >why is it user and tutor should be student and tutor
# > why is it many tutors to one session 

class RequestSession(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='request_sessions_student', null=True)
    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='request_sessions_tutor', null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE,null=True)
    availability = models.JSONField()
    start_date = models.DateField()
    end_date = models.DateField()
    #status = models.BooleanField(null=True, default=None)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    fortnightly= models.BooleanField(default= False)
    venue= models.CharField(max_length=25, default='online')

    def get_formatted_availability(self):
        if not self.availability:
            return "No times set"
        
        formatted_slots = []
        for day, times in self.availability.items():
            times_str = ", ".join(times)
            formatted_slots.append(f"{day}: {times_str}")
        
        # Join all days with their times
        return " | ".join(formatted_slots)
    
    def get_first_time_slot(self):
        if not self.availability:
            return "No time set"
        
        first_day = list(self.availability.keys())[0]
        first_time = self.availability[first_day][0]
        return f"{first_day} {first_time}"
   


class Invoices(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_invoices', null=True)
    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tutor_invoices', null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE,null=True)
    due_date = models.DateField()
    payment_date = models.DateField(null=True)
    status = models.BooleanField(default=False)
    total = models.DecimalField(decimal_places=2, max_digits=10,default=0.0)
    #status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')


class Ticket(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_ticket')
    title = models.CharField(max_length=50)
    is_close = models.BooleanField(default=False)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)


class Messages(models.Model):
    FROM_CHOICES = [
        ('student', 'Student'),
        ('admin', 'Admin'),
    ]
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='ticket_messages')
    content = models.TextField()
    msg_from = models.CharField(max_length=10, choices=FROM_CHOICES, default='student')
    is_read = models.BooleanField(default=False)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)