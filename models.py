from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# In-memory database using dictionaries
class Database:
    def __init__(self):
        self.users = {}
        self.projects = {}
        self.proposals = {}
        self.messages = {}
        self.portfolios = {}
        self.user_id_counter = 1
        self.project_id_counter = 1
        self.proposal_id_counter = 1
        self.message_id_counter = 1
        self.portfolio_id_counter = 1

db = Database()

class User:
    def __init__(self, username, email, password, user_type):
        self.id = db.user_id_counter
        db.user_id_counter += 1
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.user_type = user_type  # 'client' or 'freelancer'
        self.created_at = datetime.now()
        # Add user to the database
        db.users[self.id] = self
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @classmethod
    def get_by_id(cls, user_id):
        return db.users.get(user_id)
    
    @classmethod
    def get_by_email(cls, email):
        for user in db.users.values():
            if user.email == email:
                return user
        return None
    
    @classmethod
    def get_by_username(cls, username):
        for user in db.users.values():
            if user.username == username:
                return user
        return None

class Project:
    def __init__(self, title, description, budget, deadline, category, client_id):
        self.id = db.project_id_counter
        db.project_id_counter += 1
        self.title = title
        self.description = description
        self.budget = budget
        self.deadline = deadline
        self.category = category
        self.client_id = client_id
        self.status = 'open'  # open, in_progress, completed, cancelled
        self.created_at = datetime.now()
        # Add project to the database
        db.projects[self.id] = self
    
    @classmethod
    def get_by_id(cls, project_id):
        return db.projects.get(project_id)
    
    @classmethod
    def get_by_client(cls, client_id):
        return [project for project in db.projects.values() if project.client_id == client_id]
    
    @classmethod
    def get_all(cls):
        return list(db.projects.values())
    
    @classmethod
    def get_by_category(cls, category):
        return [project for project in db.projects.values() if project.category == category]

class Proposal:
    def __init__(self, project_id, freelancer_id, cover_letter, price, delivery_time):
        self.id = db.proposal_id_counter
        db.proposal_id_counter += 1
        self.project_id = project_id
        self.freelancer_id = freelancer_id
        self.cover_letter = cover_letter
        self.price = price
        self.delivery_time = delivery_time
        self.status = 'pending'  # pending, accepted, rejected
        self.created_at = datetime.now()
        # Add proposal to the database
        db.proposals[self.id] = self
    
    @classmethod
    def get_by_id(cls, proposal_id):
        return db.proposals.get(proposal_id)
    
    @classmethod
    def get_by_project(cls, project_id):
        return [proposal for proposal in db.proposals.values() if proposal.project_id == project_id]
    
    @classmethod
    def get_by_freelancer(cls, freelancer_id):
        return [proposal for proposal in db.proposals.values() if proposal.freelancer_id == freelancer_id]

class Message:
    def __init__(self, sender_id, receiver_id, project_id, content):
        self.id = db.message_id_counter
        db.message_id_counter += 1
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.project_id = project_id
        self.content = content
        self.read = False
        self.created_at = datetime.now()
        # Add message to the database
        db.messages[self.id] = self
    
    @classmethod
    def get_by_id(cls, message_id):
        return db.messages.get(message_id)
    
    @classmethod
    def get_conversation(cls, user1_id, user2_id, project_id=None):
        if project_id:
            return [message for message in db.messages.values() 
                   if ((message.sender_id == user1_id and message.receiver_id == user2_id) or 
                       (message.sender_id == user2_id and message.receiver_id == user1_id)) and 
                   message.project_id == project_id]
        else:
            return [message for message in db.messages.values() 
                   if (message.sender_id == user1_id and message.receiver_id == user2_id) or 
                   (message.sender_id == user2_id and message.receiver_id == user1_id)]
    
    @classmethod
    def get_by_user(cls, user_id):
        return [message for message in db.messages.values() 
               if message.sender_id == user_id or message.receiver_id == user_id]

class PortfolioItem:
    def __init__(self, freelancer_id, title, description, image_url, category):
        self.id = db.portfolio_id_counter
        db.portfolio_id_counter += 1
        self.freelancer_id = freelancer_id
        self.title = title
        self.description = description
        self.image_url = image_url
        self.category = category
        self.created_at = datetime.now()
        # Add portfolio item to the database
        db.portfolios[self.id] = self
    
    @classmethod
    def get_by_id(cls, portfolio_id):
        return db.portfolios.get(portfolio_id)
    
    @classmethod
    def get_by_freelancer(cls, freelancer_id):
        return [item for item in db.portfolios.values() if item.freelancer_id == freelancer_id]

# Add some initial categories
CATEGORIES = [
    "Logo Design", 
    "Web Design", 
    "Illustration", 
    "Branding", 
    "Print Design", 
    "UI/UX Design", 
    "Social Media Graphics", 
    "Packaging Design"
]
