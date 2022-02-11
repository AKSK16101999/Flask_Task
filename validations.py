from flask import Flask, render_template, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from datetime import date
from wtforms import StringField, SubmitField, DateField, RadioField
from wtforms.validators import data_required, length, InputRequired, Regexp, ValidationError
import re
app = Flask(__name__)
app.config.update(
    SECRET_KEY="topsecrete@$",
    SQLALCHEMY_DATABASE_URI='postgresql://postgres:12345678@localhost/postgres',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)


class UserInfo(db.Model):
    __tablename__ = 'data'
    Id = db.Column(db.Integer, primary_key=True)
    First_Name = db.Column(db.String(20), )
    Last_Name = db.Column(db.String(20))
    Cnic = db.Column(db.String(20))
    Date_of_Birth = db.Column(db.Date)
    Province = db.Column(db.String(20))

    def __init__(self, fname, lname, cnic, dob, province):
        self.First_Name = fname
        self.Last_Name = lname
        self.Cnic = cnic
        self.Date_of_Birth = dob
        self.Province = province

    def json(self):
        return {'First_Name': self.First_Name, 'Last_Name': self.Last_Name,
                'Cnic': self.Cnic, 'Date_of_Birth': self.Date_of_Birth}


def check_age(form, field):
    today = date.today()
    print(today)
    print('in the function',field.data)
    my_date = field.data
    if my_date > today:
        raise ValidationError('Date should be 16 years old')
    elif abs(today - my_date).days < 5840:
        raise ValidationError("Younger than 16 years Not allowed !")


def uppercase(form, field):
    if re.search('[A-Z]', field.data):
        raise ValidationError('uppercase letter not allowed')
    elif re.search('[^\w+$]', field.data):
        raise ValidationError('Spaces are not allowed')


def num_len(form, field):
    field.data = re.sub(r'-', "", field.data)
    if len(str(field.data)) > 13:
        raise ValidationError('cnic number length should be less or equal to 13')


def province(form, field):
    data = field.data.capitalize()
    if (data or field.data.upper() or field.data.lower()) not in ['Sindh', 'Punjab', 'KPK', 'Gilgit Baltistan']:
        raise ValidationError("Province should be in ['Sindh', 'Punjab', 'KPK', 'Gilgit Baltistan']")


class Registration(FlaskForm):
    First_Name = StringField("First_Name", validators=[data_required(), length(3, 20), uppercase])
    Last_Name = StringField("Last_Name", validators=[data_required(), length(3, 20), uppercase])
    Cinic = StringField("Cinic", validators=[data_required(), num_len])
    Date_of_Birth = DateField("Date_of_Birth", validators=[check_age])
    Province = StringField("Province", validators=[data_required(), province])
    # Province = RadioField("Province",
    #                       choices=['Sindh', 'Punjab', 'KPK', 'Gilgit Baltistan'],
    #                       validators=[InputRequired()])
    Submit = SubmitField("Register")


@app.route('/')
def hello():
    return render_template('layout.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = Registration()

    print(form.Date_of_Birth.data)
    if form.validate_on_submit():
        user = UserInfo(
            fname=form.First_Name.data,
            lname=form.Last_Name.data,
            cnic=form.Cinic.data,
            dob=form.Date_of_Birth.data,
            province=form.Province.data
        )
        db.session.add(user)
        db.session.commit()
        flash("Registration Successful")
    return render_template('registration.html', form=form)


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
