from email.headerregistry import Group
from django.core.management.base import BaseCommand, CommandError
from tutorials.models import User, Course, Tutor, Student, RequestSession, Invoices
import pytz
from faker import Faker
from random import randint, random, choice, sample, uniform
from datetime import date, timedelta ,datetime
import ast

user_fixtures = [
    {'username': '@johndoe', 'email': 'john.doe@example.org', 'first_name': 'John', 'last_name': 'Doe', 'role':'Student'},
    {'username': '@janedoe', 'email': 'jane.doe@example.org', 'first_name': 'Jane', 'last_name': 'Doe','role':'Tutor'},
    {'username': '@charlie', 'email': 'charlie.johnson@example.org', 'first_name': 'Charlie', 'last_name': 'Johnson', 'role':'Admin'},
] 
course_fixtures = [
    {
        'name': 'Python Basics',
        'desc': 'Learn Python fundamentals including variables, loops, functions and basic data structures',
        'price': 99.99
    },
    {
        'name': 'Java Basics',
        'desc': 'Learn Java fundamentals including variables, loops, functions and basic data structures',
        'price': 99.99
    },
    {
        'name': 'C++ Basic',
        'desc': 'Deep dive into OOP, pointers, adresses, and other basic C++ concepts',
        'price': 149.99
    },
    {
        'name': 'Advanced Python',
        'desc': 'Deep dive into OOP, decorators, generators, and advanced Python concepts',
        'price': 149.99
    },
    {
        'name': 'Web Development Fundamentals',
        'desc': 'HTML, CSS and JavaScript basics for building interactive websites',
        'price': 129.99
    },
    {
        'name': 'React Framework',
        'desc': 'Modern React including hooks, state management, and component architecture',
        'price': 179.99
    },
    {
        'name': 'Data Structures & Algorithms',
        'desc': 'Essential DS&A concepts with Python implementations',
        'price': 199.99
    }
]

class Command(BaseCommand):
    """Build automation command to seed the database."""

    USER_COUNT = 300 
    DEFAULT_PASSWORD = 'Password123'
    help = 'Seeds the database with sample data'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.faker = Faker('en_GB')

    def handle(self, *args, **options):
        Course.objects.all().delete()
        self.create_courses()
        self.create_users()
        self.add_tutor_to_course()
        self.users = User.objects.all()
        self.create_request_sessions()

    def add_tutor_to_course(self):
        courses = Course.objects.all()
        tutors = User.objects.filter(role="Tutor")
        print(tutors, courses)
        for course in courses:
            tutors_for_course = []
            for _ in range(randint(1, 5)):
                tutors_for_course.append(choice(tutors))
            course.users.set(tutors_for_course)
            course.save()
    def create_courses(self):
        for data in course_fixtures:
            try:
                course = Course.objects.get_or_create(
                    name=data['name'],
                    defaults={
                        'desc': data['desc'],
                        'price': data['price']
                    }
                )

            except:
                pass

    def setup_groups(self):
        """Ensure required groups exist."""
        self.groups = {
            'Admin': Group.objects.get_or_create(name='Admin')[0],
            'Tutor': Group.objects.get_or_create(name='Tutor')[0],
            'Student': Group.objects.get_or_create(name='Student')[0],
        }

    def create_users(self):
        for data in user_fixtures:
            try:
                self.create_user(data)
            except:
                pass
        self.generate_random_users()

    def generate_random_users(self):
        user_count = User.objects.count()
        while user_count < self.USER_COUNT:
            print(f"Seeding user {user_count}/{self.USER_COUNT}", end='\r')
            self.generate_user()
            user_count = User.objects.count()
        print("User seeding complete.      ")

    def generate_user(self):
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        email = create_email(first_name, last_name)
        username = create_username(first_name, last_name)
        generated_role = generate_role()
        try:
            self.create_user({'username': username, 'email': email,'password':"Password123", 'first_name': first_name, 'last_name': last_name, 'role': generated_role})
        except:
            pass
               
    
    def create_user(self, data):
        try:
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=Command.DEFAULT_PASSWORD,
                first_name=data['first_name'],
                last_name=data['last_name'],
                role=data['role']
            )

            if data['role'] == 'Student':
                student = Student.objects.create(
                    user=user,
                    availability=generate_availability()
                )
                courses = Course.objects.all()
                student.courses.set(generate_courses())
            
            elif data['role'] == 'Tutor':
                tutor = Tutor.objects.create(
                    user=user,
                    availability=generate_availability(),
                    years_exp=randint(1, 15),
                    rate=round(uniform(0.5, 3.0), 2)
                )
                tutor.courses.set(generate_courses())
        except Exception as e:
            print(f"Error creating user {data['username']}: {e}")
            raise
    
        
    def create_request_sessions(self):
        try:
            for student in Student.objects.all():
                for course in student.courses.all():
                    self.create_request_session(student, course)
        except Exception as e:
            print(f"Error creating request sessions: {e}")

    def create_request_session(self, this_student, their_course):
        # Find tutors that teach this course
        available_tutors = Tutor.objects.filter(courses=their_course)
        if not available_tutors.exists():
            print(f"No available tutors for student {this_student.user.first_name}")
            return  
        
        their_tutor = choice(available_tutors)
        start_date = generate_start_date()
        end_date = generate_end_date()

        shared_availability = generate_shared_availability(this_student.availability,their_tutor.availability)
        
        if not shared_availability:
            print(f"No shared availability for student {this_student.user.first_name} and tutor {their_tutor.user.first_name}")
        else:
            new_session = RequestSession.objects.create(
                        student=this_student.user,
                        tutor=their_tutor.user,
                        course=their_course,
                        availability=shared_availability,
                        start_date=start_date,
                        end_date=end_date,
                        status=choice(['pending', 'accepted', 'rejected'])
                    )
            self.create_invoice(new_session)
    
    def create_invoice(self, new_session):
        availability = ast.literal_eval(str(new_session.availability))
        start_date = datetime.strptime(str(new_session.start_date), "%Y-%m-%d")
        end_date = datetime.strptime(str(new_session.end_date), "%Y-%m-%d")

        # Map day names to their respective integers
        day_map = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

        # Initialize session count
        session_count = 0

        # Loop through all dates from start_date to end_date
        current_date = start_date

        while current_date <= end_date:
            day_name = current_date.strftime("%A")  # Get the day name (e.g., "Tuesday")
            if day_name.lower() in availability:  # Check if the day is in availability
                session_count += 1  # Add the number of sessions for that day
            current_date += timedelta(days=1)
        total = new_session.course.price * session_count
        due_date = start_date + timedelta(days=3)

        try:
            Invoices.objects.create(
            student= new_session.student,
            tutor= new_session.tutor,
            course= new_session.course,
            due_date= due_date,
            status= False,
            total=total,
            )
        except Exception as e:
            print(f"Error creating invoice {e}")
            raise


def create_username(first_name, last_name):
    return '@' + first_name.lower() + last_name.lower()


def create_email(first_name, last_name):
    return first_name + '.' + last_name + '@example.org'


def generate_role():
    rand = random()
    if rand < 0.80:
        return 'Student'
    elif rand < 0.95:
        return 'Tutor'
    return 'Admin'
def generate_courses():
    courses = list(Course.objects.all())
    num_courses = randint(1, 3)
    return sample(courses, num_courses)

def generate_availability():
    weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    time_slots = [
        "1:00",
        "2:00",
        "3:00",
        "4:00",
        "5:00"
    ]
    availability = {}
    num_slots_days = randint(1, 3) # Randomly pick 1-3 time days
    weekdays = sample(weekdays, num_slots_days)
    for day in weekdays:
            # Randomly pick 1-3 time slots 
            num_slots = randint(1, 3)
            availability[day] = sample(time_slots, num_slots)
    return availability

def generate_start_date():
    today = date.today()
    days_ahead = randint(1, 30)  # Start within next 30 days
    return today + timedelta(days=days_ahead)

def generate_end_date():
    start = generate_start_date()
    weeks_duration = randint(1, 12)  # Sessions last 1-12 weeks
    return start + timedelta(weeks=weeks_duration)

def generate_shared_availability(student_availability, tutor_availability):
    shared = {}
    
    # Find common days
    common_days = set(student_availability.keys()) & set(tutor_availability.keys())
    
    for day in common_days:
        # Find common time slots for each day
        student_times = set(student_availability[day])
        tutor_times = set(tutor_availability[day])
        common_times = student_times & tutor_times

        
        if common_times:  # Only include days with matching times
            shared[day] = list(common_times)[0]
    
    return shared