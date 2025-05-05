from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, DecimalField, DateField, SubmitField, HiddenField, RadioField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, Length, URL, ValidationError, Optional
from models import User, CATEGORIES

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    user_type = RadioField('I am a', choices=[('client', 'Client - I need design work'), ('freelancer', 'Freelancer - I offer design services')], validators=[DataRequired()])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.get_by_username(username.data)
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.get_by_email(email.data)
        if user:
            raise ValidationError('Email already registered. Please use a different one or login.')

class ProjectForm(FlaskForm):
    title = StringField('Project Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Project Description', validators=[DataRequired(), Length(min=30, max=2000)])
    category = SelectField('Category', choices=[(cat, cat) for cat in CATEGORIES], validators=[DataRequired()])
    budget = DecimalField('Budget ($)', validators=[DataRequired()])
    deadline = DateField('Deadline', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Post Project')

class ProposalForm(FlaskForm):
    project_id = HiddenField('Project ID')
    cover_letter = TextAreaField('Cover Letter', validators=[DataRequired(), Length(min=30, max=1000)])
    price = DecimalField('Your Price ($)', validators=[DataRequired()])
    delivery_time = StringField('Delivery Time (e.g., "5 days")', validators=[DataRequired()])
    submit = SubmitField('Submit Proposal')

class MessageForm(FlaskForm):
    receiver_id = HiddenField('Receiver ID')
    project_id = HiddenField('Project ID')
    content = TextAreaField('Message', validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField('Send Message')

class PortfolioItemForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=500)])
    image_url = StringField('Image URL', validators=[DataRequired(), URL()])
    category = SelectField('Category', choices=[(cat, cat) for cat in CATEGORIES], validators=[DataRequired()])
    submit = SubmitField('Add Portfolio Item')
