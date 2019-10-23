import secrets, os
from PIL import Image
from flask import render_template, url_for, flash, redirect, request
from portfolio_site import app, db, bcrypt
from portfolio_site.forms import RegistrationForm, LoginForm, UpdateAccountForm
from portfolio_site.models import User , Post
from flask_login import login_user, logout_user, current_user, login_required


@app.route("/")
def home():
    return render_template('home.html', title='Home')

@app.route("/register", methods=['GET','POST'])
def register():
    # check to see if the user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # create a hashed password to store in the database
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        # create a user object to store i the database with form data and hashed password as parametes
        user = User(username = form.username.data, email = form.email.data, password = hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created, you may now login!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title = 'Register', form = form)

@app.route("/login", methods=['GET','POST'])
def login():
    # check to see if the user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        # create a user variable if the email is in the database
        user = User.query.filter_by(email=form.email.data).first()
        # if the user is in the database and the hashed password returns true open the door
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login failed! Please check your email and password.', 'danger')
    return render_template('login.html', title = 'Login', form = form)

# function to log the current user out
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

# Function to convert images before saving
def save_picure(form_picture):
    # create a random hex to store the image file in database without losing file ext
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path =os.path.join(app.root_path, 'static/profile_pictures', picture_fn)
    output_size = (125,125)
    newImage = Image.open(form_picture)
    newImage.thumbnail(output_size)
    newImage.save(picture_path)
    return picture_fn

@app.route("/account", methods=['GET','POST'])
# require a user to be logged in before they can access this page
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picure(form.picture.data)
        current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Account updated successfully!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pictures/' + current_user.image_file)
    return render_template('account.html', title = 'Account', image_file = image_file, form = form)
