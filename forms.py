from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DecimalField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class TransactionForm(FlaskForm):
    amount = DecimalField('Amount', validators=[DataRequired()], places=2)
    category = SelectField('Category', validators=[DataRequired()], choices=[
        ('food', 'Food'),
        ('transport', 'Transport'),
        ('housing', 'Housing'),
        ('entertainment', 'Entertainment'),
        ('health', 'Health'),
        ('education', 'Education'),
        ('salary', 'Salary'),
        ('bonus', 'Bonus'),
        ('investment', 'Investment'),
        ('other', 'Other')
    ])
    type = SelectField('Type', validators=[DataRequired()], choices=[
        ('income', 'Income'),
        ('expense', 'Expense')
    ])
    description = TextAreaField('Description')
    submit = SubmitField('Add Transaction')

class StockSearchForm(FlaskForm):
    symbol = StringField('Stock Symbol', validators=[DataRequired()])
    submit = SubmitField('Add to Watchlist')