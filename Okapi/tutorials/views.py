from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.utils import timezone
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect, render,get_object_or_404
from django.views import View
from django.views.generic.edit import FormView, UpdateView
from django.urls import reverse, reverse_lazy
from tutorials.forms import LogInForm, PasswordForm, UserForm, SignUpForm,CourseForm
from tutorials.helpers import login_prohibited
from tutorials.models import Course, RequestSession,User, Invoices,Ticket,Messages
import ast
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from datetime import datetime, timedelta

@login_required
def admin_accept_request_session(request,request_id):
    if request.user.role != "Admin":
        raise PermissionDenied
    request_session = get_object_or_404(RequestSession, id=request_id)

@login_required
def ticket_details(request,ticket_id):
    current_user=request.user
    if current_user.role == "Tutor":
        raise PermissionDenied
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if current_user.role == "Student" and ticket.student_id != current_user.id:
        raise PermissionDenied
    if request.method == "POST" and not ticket.is_close:
        if request.POST.get("content").strip() != "":
            msg = Messages(
                ticket=ticket,
                content=request.POST.get("content"),
                msg_from=current_user.role.lower()
            )
            msg.save()
        if current_user.role == "Admin" and request.POST.get("close_ticket"):
            ticket.is_close=True
            ticket.save()
    msgs = ticket.ticket_messages.all().order_by("date","time")
    mark_as_read_for="student"
    if current_user.role=="Student":
        mark_as_read_for="admin"
    ticket.ticket_messages.filter(msg_from=mark_as_read_for).update(is_read=True)
    return render(request, 'ticket/ticket_details.html', {"ticket": ticket,"msgs" : msgs,"current_user":current_user})
@login_required
def all_ticket(request):

    if request.user.role == "Tutor":
        raise PermissionDenied
    tickets=[]
    if request.user.role == "Admin":
        tickets=Ticket.objects.annotate(
            unread_msg_count=Count('ticket_messages', filter=Q(ticket_messages__is_read=False, ticket_messages__msg_from="student"))
        ).order_by('-date','-time')
    else:
        tickets=Ticket.objects.filter(student=request.user).annotate(
            unread_msg_count=Count('ticket_messages', filter=Q(ticket_messages__is_read=False, ticket_messages__msg_from="admin"))
        ).order_by("-date",'-time')
    return render(request, 'ticket/all_ticket.html',{"tickets":tickets,"current_user":request.user})


@login_required
def open_ticket(request):
    if request.user.role != "Student":
        raise  PermissionDenied
    if request.method == "POST":
        ticket = Ticket(
            title= request.POST.get("title"),
            student=request.user
        )
        ticket.save()
        msg= Messages(
            ticket=ticket,
            content=request.POST.get("content"),
            msg_from="student"
        )
        msg.save()
        return redirect('all_ticket')
    else:
        return render(request, 'ticket/open_ticket.html')

@login_required
def admin_request_details(request, request_id):
    if request.user.role != "Admin":
        raise PermissionDenied
    request_session = get_object_or_404(RequestSession, id=request_id)
    tutors = request_session.course.users.all()
    availability = ast.literal_eval(str(request_session.availability))
    
    if request.method == "POST":
        status = request.POST.get("status")
        if status in ['accepted', 'rejected', 'pending']:
            request_session.status = status
            
            # If status is accepted and a tutor is selected
            if status == 'accepted' and request.POST.get("tutor"):
                tutor = User.objects.get(id=request.POST.get("tutor"))
                request_session.tutor = tutor  # Use direct assignment for ForeignKey
                availability = ast.literal_eval(str(request_session.availability))
                start_date = datetime.strptime(str(request_session.start_date), "%Y-%m-%d")
                end_date = datetime.strptime(str(request_session.end_date), "%Y-%m-%d")

                # Map day names to their respective integers
                day_map = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]


                # Initialize session count
                session_count = 0

                # Loop through all dates from start_date to end_date
                current_date = start_date

                while current_date <= end_date:
                    day_name = current_date.strftime("%A")  # Get the day name (e.g., "Tuesday")
                    if day_name.lower() in availability:  # Check if the day is in availability
                        session_count += 1  # Add the number of sessions for that day
                    current_date += timedelta(days=1)
                total = request_session.course.price * session_count
                due_date=start_date+timedelta(days=3)
                invoice = Invoices(
                    due_date=due_date,
                    course_id=request_session.course.id,
                    student_id=request_session.student.id,
                    tutor_id=tutor.id,
                    total=total
                )
                invoice.save()
                request_session.save()
            else:
                request_session.save()

            return redirect('admin.request.list')

    context = {
        'request_session': request_session,
        "availability": availability,
        "tutors": tutors
    }
    return render(request, 'admin/sessions/request_details.html', context)

@login_required
def admin_request_list(request):
    if not request.user.role == "Admin":
        raise PermissionDenied
    requests = RequestSession.objects.all().order_by('-id')
    return render(request, 'admin/sessions/requests.html', {'requests': requests})

@login_required
def request_session(request,course_id):
    if not request.user.role == "Student":
        raise PermissionDenied
    course = get_object_or_404(Course, id=course_id)
    if request.method == "POST":
        # Get user and course
        student = request.user
        course = get_object_or_404(Course, id=course_id)

        # Get start_date and end_date from the form
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        # Validate start_date and end_date
        if not start_date or not end_date:
            messages.error(request, "Start date and end date are required.")
            return render(request, 'sessions/request_session.html', {'course_id': course_id, "course": course, 'weekdays': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']})

        # Prepare the availability dictionary
        availability = {}
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in days:
            if f'cb_{day}' in request.POST:  # Checkbox is checked
                time = request.POST.get(f'{day}_time', None)
                if time:  # If a time is provided
                    availability[day] = time
        if not availability:
            messages.error(request, "You must select at least one day with an available time.")
            return render(request, 'sessions/request_session.html', {'course_id': course_id, "course": course, 'weekdays': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']})
        # Save the RequestSession object

        session = RequestSession.objects.create(
            student=student,
            course=course,
            start_date=start_date,
            end_date=end_date,
            availability=availability
        )
        # Redirect or return a response
        return redirect('student.requests_list')
    return render(request, 'sessions/request_session.html', {'course_id': course_id,"course":course, 'weekdays':['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']})

@login_required
def student_requests_list(request):
    if not request.user.role == "Student":
        raise PermissionDenied
    current_user = request.user
    requests = []
    all_requests = RequestSession.objects.all()
    for req in all_requests:
        if req.student == current_user:
            requests.append(req)
    courses = Course.objects.all()
    return render(request, 'students/requests.html', {'requests': requests, 'courses': courses})

@login_required
def create_course(request):
    if not request.user.role == "Admin":
        raise PermissionDenied
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            # Save course
            form.save()
            return redirect('course_list')  # Redirect to a course list view or similar
    else:
        form = CourseForm()

    return render(request, 'courses/add_course.html', {'form': form})

@login_required
def edit_course(request, course_id):
    if not request.user.role == "Admin":
        raise PermissionDenied
    # Get the course instance by id or return a 404 if not found
    course = get_object_or_404(Course, id=course_id)
    form = None  # Initialize form variable


    if request.method == 'POST':
        # Create a form instance with POST data and bind it to the course
        form = CourseForm(request.POST,instance=course)
        if form.is_valid():
            # Save changes to the course instance
            form.save()
            return redirect('course_list')  # Redirect to a course list view or similar
        #else:
        #    form = CourseForm(instance=course)
            #print(form.errors)
    # Render the form for editing the course

    if form is None:
        form = CourseForm(instance=course)
            
    return render(request, 'courses/edit_course.html', {'form': form, 'course': course})



def request_session_course_list(request):
    courses = Course.objects.all()
    return render(request, 'sessions/course_list.html', {'courses': courses})

@login_required
def course_list(request):
    if not request.user.role == "Admin":
        raise PermissionDenied
    # Retrieve all courses
    courses = Course.objects.all()
    # Render them in a template
    return render(request, 'courses/course_list.html', {'courses': courses})

@login_required
def delete_course(request,course_id):
    if not request.user.role == "Admin":
        raise PermissionDenied
    course = Course.objects.get(id=course_id)
    if request.method == 'POST':
        course.delete()
        return redirect('course_list')
    return render(request,
                  "courses/delete_course.html",{"course":course})


@login_required
def show_usernames(request):
    if not request.user.role == "Admin":
        raise PermissionDenied
    users = User.objects.all()  # Fetch all users
    context = {
        'usernames': [user.username for user in users]  # Extract usernames
    }
    return render(request, 'usernames_list.html', context)

@login_required
def mark_invoice_paid(request, invoice_id):
    # Only allow admins to mark invoices as paid
    if request.user.role != 'Admin':
        messages.error(request, "You do not have permission to mark invoices as paid.")
        return redirect('invoices')
    
    invoice = get_object_or_404(Invoices, id=invoice_id)
    
    # Mark the invoice as paid and set the payment date to today
    invoice.status = True
    invoice.payment_date = timezone.now().date()
    invoice.save()
    
    messages.success(request, f"Invoice for {invoice.course.name} has been marked as paid.")
    return redirect('invoices')

@login_required
def dashboard(request):
    """Display the current user's dashboard."""

    current_user = request.user

    if request.user.role == 'Admin':

        students_count = User.objects.filter(role="Student").count()
        tutors_count = User.objects.filter(role="Tutor").count()
        admin_count = User.objects.filter(role="Admin").count()
        request_count= RequestSession.objects.filter(status='pending').count()
        courses_count= Course.objects.filter().count()
        unpaid_invoices_count = Invoices.objects.filter(status=False).count()
        context = {
            'user': current_user,
            'students_count': students_count,
            'tutors_count': tutors_count,
            'admin_count': admin_count,
            'request_count': request_count,
            'courses_count': courses_count,
            'unpaid_invoices_count': unpaid_invoices_count,
        }
        return render(request, 'admin_dashboard.html', context)
        #return render(request, 'admin_dashboard.html', {'user': current_user})

    elif current_user.role == 'Student':
        upcoming_sessions = RequestSession.objects.filter(
            student=current_user,
            status='accepted',
            start_date__gte=timezone.now().date()
        ).order_by('start_date')


        all_courses = Course.objects.all()
        context = {
            'user': current_user,
            'upcoming_sessions': upcoming_sessions,
            'courses': all_courses
        }
        
        return render(request, 'dashboard.html', context)
    
    elif current_user.role == 'Tutor':
        upcoming_sessions = RequestSession.objects.filter(
            tutor=current_user,
            status='accepted',
            start_date__gte=timezone.now().date()
        ).order_by('start_date')

        next_session = None
        if upcoming_sessions:
            next_session = upcoming_sessions[0]
            upcoming_sessions = upcoming_sessions[1:]

        context = {
            'user': current_user,
            'upcoming_sessions': upcoming_sessions,
            'next_session': next_session,
        }
        
        return render(request, 'dashboard.html', context)
    else:
        return render(request, 'dashboard.html', {'user': current_user})


# def admin_dashboard(request):
#     """Display the admin's' dashboard."""
#
#     current_user = request.user
#     if request.user.role == 'Admin':
#         students_count = User.objects.filter(role="Student").count()
#         tutors_count = User.objects.filter(role="Tutor").count()
#         admin_count = User.objects.filter(role="Admin").count()
#
#         context = {
#             'user': current_user,
#             'students_count': students_count,
#             'tutors_count': tutors_count,
#             'admin_count': admin_count,
#         }
#
#         return render(request, 'admin_dashboard.html', context)
    

    #courses = Course.objects.all()
    #tutors = Tutor.objects.all()
    #students = Student.objects.all()
    #invoices = Invoice.objects.all()
    
    #context = {
     #   'lessons_count': courses.count(),
      #  'tutors_count': tutors.count(),
      #  'students_count': students.count(),
        #'unpaid_invoices':invoices.count()

    #}
   
    #return render(request, 'admin_dashboard.html', context)




    


@login_prohibited
def home(request):
    """Display the application's start/home screen."""

    return render(request, 'home.html')


class LoginProhibitedMixin:
    """Mixin that redirects when a user is logged in."""

    redirect_when_logged_in_url = None

    def dispatch(self, *args, **kwargs):
        """Redirect when logged in, or dispatch as normal otherwise."""
        if self.request.user.is_authenticated:
            return self.handle_already_logged_in(*args, **kwargs)
        return super().dispatch(*args, **kwargs)

    def handle_already_logged_in(self, *args, **kwargs):
        url = self.get_redirect_when_logged_in_url()
        return redirect(url)

    def get_redirect_when_logged_in_url(self):
        """Returns the url to redirect to when not logged in."""
        if self.redirect_when_logged_in_url is None:
            raise ImproperlyConfigured(
                "LoginProhibitedMixin requires either a value for "
                "'redirect_when_logged_in_url', or an implementation for "
                "'get_redirect_when_logged_in_url()'."
            )
        else:
            return self.redirect_when_logged_in_url


class LogInView(LoginProhibitedMixin, View):
    """Display login screen and handle user login."""

    http_method_names = ['get', 'post']
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def get(self, request):
        """Display log in template."""

        self.next = request.GET.get('next') or ''
        return self.render()

    def post(self, request):
        """Handle log in attempt."""

        form = LogInForm(request.POST)
        self.next = request.POST.get('next') or settings.REDIRECT_URL_WHEN_LOGGED_IN
        user = form.get_user()
        if user is not None:
            login(request, user)
            return redirect(self.next)
        messages.add_message(request, messages.ERROR, "The credentials provided were invalid!")
        return self.render()

    def render(self):
        """Render log in template with blank log in form."""

        form = LogInForm()
        return render(self.request, 'log_in.html', {'form': form, 'next': self.next})


def log_out(request):
    """Log out the current user"""

    logout(request)
    return redirect('home')


class PasswordView(LoginRequiredMixin, FormView):
    """Display password change screen and handle password change requests."""

    template_name = 'password.html'
    form_class = PasswordForm

    def get_form_kwargs(self, **kwargs):
        """Pass the current user to the password change form."""

        kwargs = super().get_form_kwargs(**kwargs)
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        """Handle valid form by saving the new password."""

        form.save()
        login(self.request, self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect the user after successful password change."""

        messages.add_message(self.request, messages.SUCCESS, "Password updated!")
        return reverse('dashboard')


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Display user profile editing screen, and handle profile modifications."""

    model = UserForm
    template_name = "profile.html"
    form_class = UserForm

    def get_object(self):
        """Return the object (user) to be updated."""
        user = self.request.user
        return user

    def get_success_url(self):
        """Return redirect URL after successful update."""
        messages.add_message(self.request, messages.SUCCESS, "Profile updated!")
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)


class SignUpView(LoginProhibitedMixin, FormView):
    """Display the sign up screen and handle sign ups."""

    form_class = SignUpForm
    template_name = "sign_up.html"
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def form_valid(self, form):
        self.object = form.save()
        login(self.request, self.object)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)
    

@login_required
def all_sessions(request):
    current_user = request.user
    if current_user.role == 'Student':
        previous_sessions = RequestSession.objects.filter(
                student=current_user,
                status='accepted',
                end_date__lt=timezone.now().date()
            ).order_by('start_date')
        current_sessions = RequestSession.objects.filter(
            student=current_user,
            status='accepted',
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date()
        ).order_by('start_date')
        upcoming_sessions = RequestSession.objects.filter(
                student=current_user,
                status='accepted',
                start_date__gte=timezone.now().date()
            ).order_by('start_date')
    elif current_user.role == 'Tutor':
        previous_sessions = RequestSession.objects.filter(
                tutor=current_user,
                status='accepted',
                end_date__lt=timezone.now().date()
            ).order_by('start_date')
        current_sessions = RequestSession.objects.filter(
            tutor=current_user,
            status='accepted',
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date()
        ).order_by('start_date')
        upcoming_sessions = RequestSession.objects.filter(
                tutor=current_user,
                status='accepted',
                start_date__gte=timezone.now().date()
            ).order_by('start_date')
    
    context = {
        'user': current_user,
        'upcoming_sessions': upcoming_sessions,
        'previous_sessions': previous_sessions,
        "current_sessions": current_sessions
    }
    
    return render(request, 'sessions.html', context)



def invoices(request):
    current_user = request.user
    unpaid_invoices_count=0
    if current_user.role == 'Student':
        paid_invoices = Invoices.objects.filter(
            student=current_user,
            status=True,
        ).order_by('due_date')
        
        unpaid_invoices = Invoices.objects.filter(
            student=current_user,
            status=False,
        ).order_by('due_date')
        unpaid_invoices_count=len(unpaid_invoices)
    elif current_user.role == 'Tutor':
        paid_invoices = Invoices.objects.filter(
            tutor=current_user,
            status=True,
        ).order_by('due_date')
        
        unpaid_invoices = Invoices.objects.filter(
            tutor=current_user,
            status=False,
        ).order_by('due_date')
        unpaid_invoices_count = len(unpaid_invoices)
    elif current_user.role == 'Admin':
        # For admin, show all invoices
        paid_invoices = Invoices.objects.filter(status=True).order_by('due_date')
        unpaid_invoices = Invoices.objects.filter(status=False).order_by('due_date')
        unpaid_invoices_count = unpaid_invoices.count()
    
    else:
        # If no matching role, return empty querysets
        paid_invoices = Invoices.objects.none()
        unpaid_invoices = Invoices.objects.none()
    context = {
        'paid_invoices': paid_invoices,
        'unpaid_invoices': unpaid_invoices,
        'unpaid_invoices_count': unpaid_invoices_count
    }
    return render(request, 'invoices.html', context)



# invoice for tutor
# invoice for student if there is no invoice
