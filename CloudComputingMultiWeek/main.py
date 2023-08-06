import os
from flask import Flask, render_template, redirect, url_for, request, session
from flask_wtf import FlaskForm
from wtforms.fields import IntegerField, EmailField
from wtforms import SubmitField, StringField, PasswordField
from wtforms.validators import DataRequired, Email
from flask_sqlalchemy import SQLAlchemy
import pymysql
import boto3

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config['SECRET_KEY'] = 'Amulya'

Database_Name = 'defaultdb'
User = 'admin'
Password = 'multiweekdb'
Port='3306'
Endpoint = 'multiweekdb.clnopyq3sfwe.us-east-1.rds.amazonaws.com'


bas_Access_key = 'AKIATPJEI4R673PT6FFJ'
bas_secret_key = '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'
bas_region = 'us-east-1'

logged_user = ""

class SignInForm(FlaskForm):
    email_address = StringField("Email ID", validators=[
                                DataRequired(), Email()])
    password = PasswordField("Password",
                             validators=[DataRequired()])
    login = SubmitField("Login")


class SignUpForm(FlaskForm):
    firstname = StringField("First Name")
    lastname = StringField("Last Name")
    email_address = StringField("Email ID")
    password = PasswordField("Password")
    confirm_password = PasswordField("Confirm Password")
    signup = SubmitField("Signup")

def createdatabase():
    try:
        connection_variables = pymysql.connect(host=Endpoint, user=User, password=Password, database=Database_Name)
        db_tracker = connection_variables.cursor()
        db_tracker.execute("USE defaultdb;")
        db_tracker.execute("create table if not exists basuserdetails(firstname varchar(100), lastname varchar(100), email varchar(100) unique, password varchar(100));")
        db_tracker.execute("create table if not exists basfiletrackers(email varchar(100), filename varchar(100));")
        connection_variables.commit()
        print("Tables created on cloud")
    except Exception as e:
        print("table error", e)

def loaduser(user):
    connection_variables = pymysql.connect(host=Endpoint, user=User, password=Password, database=Database_Name)
    db_tracker = connection_variables.cursor()
    result = db_tracker.execute("select email, password from basuserdetails where email=%s;", (user))
    password = db_tracker.fetchone()
    print(password)
    if result:
        return password
    else:
        return 0



@app.route('/', methods=('GET', 'POST'))
def index():
    title = "Login"
    form = SignInForm()
    if form.validate_on_submit():
        email = form.email_address.data
        password = form.password.data
        result = loaduser(email)
        # print("calling", result)
        print(result[1][0])
        if result:
            if password == result[1]:
                session['user'] = email
                return render_template("secretpage.html", title=title)
        else:
            message = "Invalid email and password combination. Try again."
            return render_template("index.html", form=form, title=title, message=message)
    return render_template("index.html", form=form, title=title)




@app.route('/signup', methods=['GET', 'POST'])
def signup():
    title = "Sign Up"
    form = SignUpForm()
    if form.validate_on_submit():
        firstname = form.firstname.data
        lastname = form.lastname.data
        emailAddress = form.email_address.data
        password = form.password.data
        confirmPassword = form.confirm_password.data
        print(firstname, lastname, emailAddress, password, confirmPassword)
        errors = {}
        if password != confirmPassword or len(password) < 8:
            message = "Check the password rules or passwords doesn't match or password must be greater the 8 characters"
            return render_template("signup.html", form=form, title=title, message=message)
        
        try:
            connection_variables = pymysql.connect(host=Endpoint, user=User, password=Password, database=Database_Name)
            cursor = connection_variables.cursor()
            cursor.execute("INSERT INTO basuserdetails(firstname, lastname, email, password) VALUES (%s, %s, %s, %s);",(firstname, lastname, emailAddress, password))
            connection_variables.commit()
            return render_template("thankyou.html")
        except Exception as e:
            print("signup",e)
            return render_template("signup.html", errors= "Use a different email..", form=form)
    return render_template("signup.html", form=form, title=title)


@app.route('/thank-you')
def thank_you():
    title = "Success"
    return render_template("thankyou.html", title=title)

def generate_url(file):
    link_bucket = boto3.client('s3', aws_access_key_id=bas_Access_key, aws_secret_access_key=bas_secret_key, region_name=bas_region)
    url_for_bucket_object = link_bucket.generate_presigned_url('get_object', Params={'Bucket': 'mymultiweekbucket', 'Key': file}, ExpiresIn=7000)
    return url_for_bucket_object

def emailsubscription(ARN, protocal, endpoint):
    sns_email_variables = boto3.client('sns', aws_access_key_id=bas_Access_key, aws_secret_access_key=bas_secret_key, region_name=bas_region)
    subscription = sns_email_variables.subscribe(TopicArn = ARN, Protocol = protocal, Endpoint = endpoint, ReturnSubscriptionArn=True)
    return subscription['SubscriptionArn']

def billing(filename, user):
    try:
        connection_variables = pymysql.connect(host=Endpoint, user=User, password=Password, database=Database_Name)
        db_tracker = connection_variables.cursor()
        
        cursor.execute("INSERT INTO basfiletrackers(email, filename) VALUES (%s, %s);",(user, filename))
        connection_variables.commit()
        return 1
    except Exception as e:
        print("upload",e)
        return 0

@app.route('/fileupload', methods=['POST', 'GET'])
def fileupload():
    try:
        inputfile = request.files['file']
        filename = inputfile.filename
        link_bucket = boto3.client('s3', aws_access_key_id=bas_Access_key, aws_secret_access_key=bas_secret_key, region_name=bas_region)
        link_bucket.upload_fileobj(inputfile, "mymultiweekbucket", filename)
        object_url = generate_url(filename)
        user1 = request.form['user1']
        user2 = request.form['user2']
        user3 = request.form['user3']
        user4 = request.form['user4']
        user5 = request.form['user5']
        users = (user1, user2, user3, user4, user5)
        sns_email_variables = boto3.client('sns', aws_access_key_id=bas_Access_key, aws_secret_access_key=bas_secret_key, region_name=bas_region)
        topic = sns_email_variables.create_topic(Name="emailtopic")
        for user in users:
            if len(user)>1:
                ARN = topic['TopicArn']
                protocol = 'email'
                endpoint = user
                response = emailsubscription(ARN, protocol, endpoint)
                sns_email_variables.publish(TopicArn=ARN, Subject = "Download the file by clicking on the link ",  Message=object_url)

        upload = billing(filename, session['user'])
        return "File Uploaded and Email has been sent to users "
    except Exception as e:
        print(e)
        return "something happend while uploading or sending email"

@app.before_request
def initial():
    createdatabase()


    

if __name__ == "__main__":
    app.run(debug=True)


  

        

        

        #     lower_case = [True if a.islower() else False for a in password]
        #     if True not in lower_case:
        #         errors['lower_case'] = 'Your Password should contain a lowercase letter.'

        #     upper_case = [True if a.isupper() else False for a in password]
        #     if True not in upper_case:
        #         errors['upper_case'] = 'Your Password should contain an uppercase letter.'

        #     if not password[-1].isdigit():
        #         errors['number'] = 'Your Password should have a number at the end.'

        # if errors:
        #     return render_template("signup.html", errors=errors, form=form, title=title)