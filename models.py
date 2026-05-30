# models.py - This file holds all our OOP Blueprints (Classes)

from werkzeug.security import generate_password_hash

# 1. THE PARENT CLASS


class UserLogin:
    def __init__(self, username, password):
        self.username = username

        # ENCAPSULATION: The double underscore (__) hides the password
        # so the outside code cannot directly touch or read it.
        self.__password = password

    # We use a controlled method to hash the password securely before saving
    def get_hashed_password(self):
        return generate_password_hash(self.__password)


# 2. THE CHILD CLASS (INHERITANCE)
# By putting (UserLogin) in the parentheses, NormalUser automatically
# inherits the username and password setup from the parent.
class NormalUser(UserLogin):
    def __init__(self, username, password, program, year_level):
        # 'super()' function calls the Parent class to handle the username and password
        super().__init__(username, password)

        # These are unique only to the Normal User
        self.program = program
        self.year_level = year_level

# 3. THE NOTES CLASS


class Notez:
    def __init__(self, user_id, note_title, note_type, content):
        self.user_id = user_id
        self.note_title = note_title
        self.note_type = note_type
        self.content = content


# 4. THE STUDY SESSION CLASS
class StudySession:
    def __init__(self, user_id, duration_minutes):
        self.user_id = user_id
        self.duration_minutes = duration_minutes

# 5. THE CALENDAR EVENT CLASS


class CalendarEvent:
    def __init__(self, user_id, event_title, event_type, event_date):
        self.user_id = user_id
        self.event_title = event_title
        self.event_type = event_type
        self.event_date = event_date


# 6. THE ADMIN CLASS (Inheriting from UserLogin)
class Admin(UserLogin):
    def __init__(self, username, password, permission_level):
        super().__init__(username, password)
        self.permission_level = permission_level
