import os
from datetime import datetime
from flask import render_template, redirect, url_for, request, flash, session, abort
from app import app
from models import User, Project, Proposal, Message, PortfolioItem, CATEGORIES
from forms import LoginForm, RegisterForm, ProjectForm, ProposalForm, MessageForm, PortfolioItemForm
import logging

logger = logging.getLogger(__name__)

# Utility functions
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def client_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login', next=request.url))
        
        user = User.get_by_id(session['user_id'])
        if not user or user.user_type != 'client':
            flash('Access denied. Client privileges required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def freelancer_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login', next=request.url))
        
        user = User.get_by_id(session['user_id'])
        if not user or user.user_type != 'freelancer':
            flash('Access denied. Freelancer privileges required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Routes
@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user = User.get_by_id(session['user_id'])
    return dict(current_user=user)

@app.route('/')
def index():
    featured_projects = Project.get_all()[:4]
    return render_template('index.html', featured_projects=featured_projects, categories=CATEGORIES)

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_email(form.email.data)
        if user and user.check_password(form.password.data):
            session['user_id'] = user.id
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect based on user type
            if user.user_type == 'client':
                return redirect(url_for('client_dashboard'))
            else:
                return redirect(url_for('freelancer_dashboard'))
        else:
            flash('Login failed. Please check your email and password.', 'danger')
    
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            user_type=form.user_type.data
        )
        
        session['user_id'] = user.id
        flash('Registration successful! Your account has been created.', 'success')
        
        # Redirect based on user type
        if user.user_type == 'client':
            return redirect(url_for('client_dashboard'))
        else:
            return redirect(url_for('freelancer_dashboard'))
    
    return render_template('auth/register.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

# Client Routes
@app.route('/client/dashboard')
@client_required
def client_dashboard():
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    projects = Project.get_by_client(user_id)
    
    return render_template('client/dashboard.html', user=user, projects=projects)

@app.route('/client/post-project', methods=['GET', 'POST'])
@client_required
def post_project():
    form = ProjectForm()
    
    if form.validate_on_submit():
        project = Project(
            title=form.title.data,
            description=form.description.data,
            budget=form.budget.data,
            deadline=form.deadline.data,
            category=form.category.data,
            client_id=session['user_id']
        )
        
        flash('Your project has been posted successfully!', 'success')
        return redirect(url_for('client_dashboard'))
    
    return render_template('client/post_project.html', form=form)

@app.route('/client/view-proposals/<int:project_id>')
@client_required
def view_proposals(project_id):
    user_id = session['user_id']
    project = Project.get_by_id(project_id)
    
    if not project or project.client_id != user_id:
        flash('Project not found or access denied.', 'danger')
        return redirect(url_for('client_dashboard'))
    
    proposals = Proposal.get_by_project(project_id)
    freelancers = {proposal.freelancer_id: User.get_by_id(proposal.freelancer_id) for proposal in proposals}
    
    return render_template('client/view_proposals.html', project=project, proposals=proposals, freelancers=freelancers)

@app.route('/client/messages')
@client_required
def client_messages():
    user_id = session['user_id']
    messages = Message.get_by_user(user_id)
    
    # Group messages by conversation partners
    conversations = {}
    for message in messages:
        other_id = message.sender_id if message.sender_id != user_id else message.receiver_id
        if other_id not in conversations:
            conversations[other_id] = {
                'user': User.get_by_id(other_id),
                'last_message': message
            }
    
    form = MessageForm()
    return render_template('client/messages.html', conversations=conversations, form=form)

# Freelancer Routes
@app.route('/freelancer/dashboard')
@freelancer_required
def freelancer_dashboard():
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    proposals = Proposal.get_by_freelancer(user_id)
    portfolio_items = PortfolioItem.get_by_freelancer(user_id)
    
    # Get projects from proposals
    projects = {proposal.project_id: Project.get_by_id(proposal.project_id) for proposal in proposals}
    
    return render_template('freelancer/dashboard.html', 
                          user=user, 
                          proposals=proposals, 
                          projects=projects, 
                          portfolio_items=portfolio_items)

@app.route('/freelancer/browse-projects')
@freelancer_required
def browse_projects():
    category = request.args.get('category', '')
    
    if category and category in CATEGORIES:
        projects = Project.get_by_category(category)
    else:
        projects = Project.get_all()
    
    # Filter projects that are still open
    open_projects = [p for p in projects if p.status == 'open']
    
    return render_template('freelancer/browse_projects.html', 
                          projects=open_projects, 
                          categories=CATEGORIES, 
                          selected_category=category)

@app.route('/freelancer/portfolio', methods=['GET', 'POST'])
@freelancer_required
def portfolio():
    user_id = session['user_id']
    form = PortfolioItemForm()
    
    if form.validate_on_submit():
        portfolio_item = PortfolioItem(
            freelancer_id=user_id,
            title=form.title.data,
            description=form.description.data,
            image_url=form.image_url.data,
            category=form.category.data
        )
        
        flash('Portfolio item added successfully!', 'success')
        return redirect(url_for('portfolio'))
    
    portfolio_items = PortfolioItem.get_by_freelancer(user_id)
    return render_template('freelancer/portfolio.html', form=form, portfolio_items=portfolio_items)

@app.route('/freelancer/submit-proposal/<int:project_id>', methods=['GET', 'POST'])
@freelancer_required
def submit_proposal(project_id):
    user_id = session['user_id']
    project = Project.get_by_id(project_id)
    
    if not project or project.status != 'open':
        flash('Project not found or not open for proposals.', 'danger')
        return redirect(url_for('browse_projects'))
    
    # Check if the freelancer has already submitted a proposal for this project
    existing_proposals = Proposal.get_by_freelancer(user_id)
    for proposal in existing_proposals:
        if proposal.project_id == project_id:
            flash('You have already submitted a proposal for this project.', 'warning')
            return redirect(url_for('browse_projects'))
    
    form = ProposalForm()
    form.project_id.data = project_id
    
    if form.validate_on_submit():
        proposal = Proposal(
            project_id=project_id,
            freelancer_id=user_id,
            cover_letter=form.cover_letter.data,
            price=form.price.data,
            delivery_time=form.delivery_time.data
        )
        
        flash('Your proposal has been submitted successfully!', 'success')
        return redirect(url_for('freelancer_dashboard'))
    
    return render_template('freelancer/submit_proposal.html', form=form, project=project)

@app.route('/freelancer/messages')
@freelancer_required
def freelancer_messages():
    user_id = session['user_id']
    messages = Message.get_by_user(user_id)
    
    # Group messages by conversation partners
    conversations = {}
    for message in messages:
        other_id = message.sender_id if message.sender_id != user_id else message.receiver_id
        if other_id not in conversations:
            conversations[other_id] = {
                'user': User.get_by_id(other_id),
                'last_message': message
            }
    
    form = MessageForm()
    return render_template('freelancer/messages.html', conversations=conversations, form=form)

# Project Routes
@app.route('/project/<int:project_id>')
@login_required
def view_project(project_id):
    project = Project.get_by_id(project_id)
    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('index'))
    
    client = User.get_by_id(project.client_id)
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    
    # If the user is a freelancer, show the proposal form
    proposal_form = None
    if user.user_type == 'freelancer':
        # Check if the freelancer has already submitted a proposal
        existing_proposals = Proposal.get_by_freelancer(user_id)
        already_submitted = any(p.project_id == project_id for p in existing_proposals)
        
        if not already_submitted:
            proposal_form = ProposalForm()
            proposal_form.project_id.data = project_id
    
    # If the user is the client, show the proposals
    proposals = []
    freelancers = {}
    if user.user_type == 'client' and project.client_id == user_id:
        proposals = Proposal.get_by_project(project_id)
        freelancers = {p.freelancer_id: User.get_by_id(p.freelancer_id) for p in proposals}
    
    return render_template('project/view.html', 
                          project=project, 
                          client=client, 
                          proposal_form=proposal_form, 
                          proposals=proposals, 
                          freelancers=freelancers)

# Messaging Routes
@app.route('/send-message', methods=['POST'])
@login_required
def send_message():
    form = MessageForm()
    
    if form.validate_on_submit():
        sender_id = session['user_id']
        receiver_id = int(form.receiver_id.data)
        project_id = int(form.project_id.data) if form.project_id.data else None
        content = form.content.data
        
        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            project_id=project_id,
            content=content
        )
        
        flash('Message sent successfully!', 'success')
        
        # Redirect based on user type
        user = User.get_by_id(sender_id)
        if user.user_type == 'client':
            return redirect(url_for('client_messages'))
        else:
            return redirect(url_for('freelancer_messages'))
    
    flash('Failed to send message. Please try again.', 'danger')
    return redirect(request.referrer or url_for('index'))

@app.route('/messages/<int:user_id>', methods=['GET', 'POST'])
@login_required
def conversation(user_id):
    current_user_id = session['user_id']
    other_user = User.get_by_id(user_id)
    
    if not other_user:
        flash('User not found.', 'danger')
        return redirect(url_for('index'))
    
    # Get conversation history
    messages = Message.get_conversation(current_user_id, user_id)
    messages.sort(key=lambda x: x.created_at)
    
    # Message form
    form = MessageForm()
    form.receiver_id.data = user_id
    
    if form.validate_on_submit():
        message = Message(
            sender_id=current_user_id,
            receiver_id=user_id,
            project_id=form.project_id.data if form.project_id.data else None,
            content=form.content.data
        )
        
        # Refresh the page to see the new message
        return redirect(url_for('conversation', user_id=user_id))
    
    return render_template('messages.html', 
                          messages=messages, 
                          other_user=other_user, 
                          form=form)

# Accept/Reject Proposal Routes
@app.route('/client/accept-proposal/<int:proposal_id>')
@client_required
def accept_proposal(proposal_id):
    proposal = Proposal.get_by_id(proposal_id)
    
    if not proposal:
        flash('Proposal not found.', 'danger')
        return redirect(url_for('client_dashboard'))
    
    project = Project.get_by_id(proposal.project_id)
    
    if not project or project.client_id != session['user_id']:
        flash('Access denied or project not found.', 'danger')
        return redirect(url_for('client_dashboard'))
    
    # Update proposal and project status
    proposal.status = 'accepted'
    project.status = 'in_progress'
    
    # Reject all other proposals for this project
    other_proposals = Proposal.get_by_project(project.id)
    for p in other_proposals:
        if p.id != proposal_id:
            p.status = 'rejected'
    
    flash('Proposal accepted! The project is now in progress.', 'success')
    return redirect(url_for('view_proposals', project_id=project.id))

@app.route('/client/reject-proposal/<int:proposal_id>')
@client_required
def reject_proposal(proposal_id):
    proposal = Proposal.get_by_id(proposal_id)
    
    if not proposal:
        flash('Proposal not found.', 'danger')
        return redirect(url_for('client_dashboard'))
    
    project = Project.get_by_id(proposal.project_id)
    
    if not project or project.client_id != session['user_id']:
        flash('Access denied or project not found.', 'danger')
        return redirect(url_for('client_dashboard'))
    
    # Update proposal status
    proposal.status = 'rejected'
    
    flash('Proposal rejected.', 'success')
    return redirect(url_for('view_proposals', project_id=project.id))

# Add sample data for testing (can be removed in production)
@app.route('/initialize-data')
def create_sample_data():
    # Only create sample data if no users exist
    if not User.get_by_id(1):
        # Create sample users
        client = User(username="sampleclient", email="client@example.com", password="password", user_type="client")
        freelancer = User(username="samplefreelancer", email="freelancer@example.com", password="password", user_type="freelancer")
        
        # Create sample project
        project = Project(
            title="Logo Design for Tech Startup",
            description="We need a modern, minimalistic logo for our new tech startup. The logo should reflect innovation and reliability.",
            budget=300,
            deadline=datetime.now().date(),
            category="Logo Design",
            client_id=client.id
        )
        
        # Create sample proposal
        proposal = Proposal(
            project_id=project.id,
            freelancer_id=freelancer.id,
            cover_letter="I have 5+ years of experience in logo design and would love to work with you on this project.",
            price=250,
            delivery_time="5 days"
        )
        
        # Create sample portfolio item
        portfolio = PortfolioItem(
            freelancer_id=freelancer.id,
            title="Modern Restaurant Logo",
            description="A clean, modern logo design for a high-end restaurant.",
            image_url="https://images.unsplash.com/photo-1498677231914-50deb6ba4217",
            category="Logo Design"
        )
        
        logger.info("Sample data created successfully!")
    
    return redirect(url_for('index'))
