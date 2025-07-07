from flask import Flask, render_template, request, jsonify, redirect, url_for,flash
from flask import session as flask_session
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from requests import session
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, BooleanField
from wtforms.fields.simple import PasswordField
from wtforms.validators import DataRequired, URL, Email
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import LoginManager,UserMixin,login_user,login_required,current_user,logout_user
import os
from dotenv import load_dotenv
from flask_mail import Mail,Message
import google.generativeai as genai

load_dotenv()
GEMINI_API_KEY= os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print('Warning: GEMINI_API_KEY not found in environment variables. AI chat will not work.')

app = Flask(__name__)
app.secret_key=os.environ.get('SECRET_KEY')
class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)


app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
db.init_app(app)
bootstrap = Bootstrap5(app)
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view= 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User,int(user_id))

class User(db.Model,UserMixin):
    __tablename__ = 'users'
    id : Mapped[int] = mapped_column(Integer,primary_key=True)
    email : Mapped[str] = mapped_column(String(100),unique=True,nullable=False)
    password : Mapped[str] = mapped_column(String(100),nullable=False)
    name : Mapped[str] =mapped_column(String(100),nullable=False)
with app.app_context():
    db.create_all()

class Park(db.Model):
    __tablename__ = 'parks'
    id : Mapped[int] =mapped_column(Integer,primary_key=True)
    name : Mapped[str] = mapped_column(String(250), unique=True,nullable=False)
    map_url : Mapped[str] = mapped_column(String(500),nullable=False)
    has_wc : Mapped[bool] = mapped_column(Boolean,default=False,nullable=False)
    has_shop : Mapped[bool] = mapped_column(Boolean,default=False,nullable=False)
    has_sport_area : Mapped[bool] = mapped_column(Boolean,default=False,nullable=False)
    playground_condition : Mapped[int] = mapped_column(Integer,nullable=False)
    playground_variety : Mapped [int] = mapped_column(Integer,nullable=False)
    security : Mapped[int] = mapped_column(Integer,nullable=False)
    tree_coverage : Mapped[int] = mapped_column(Integer,nullable=False)
    img_url : Mapped[str] = mapped_column(String(500),nullable=True)
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

with app.app_context():
    db.create_all()

class LoginForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(),Email()])
    password = PasswordField('Password',validators=[DataRequired()])
    submit = SubmitField('Login')


class ParkForm(FlaskForm):
    name = StringField('Park name', validators=[DataRequired()])
    map_url =StringField('Park Location on Google Maps(URL)',validators=[DataRequired(),URL()])
    has_wc = BooleanField('Is there a WC?')
    has_shop = BooleanField('Is there a Shop?')
    has_sport_area= BooleanField('Is there a sport equipments for adult?')
    playground_condition = SelectField('Playground Condition Rating',choices=[(1,'🔧'),(2,'🔧🔧'),(3,'🔧🔧🔧'),(4,'🔧🔧🔧🔧'),(5,'🔧🔧🔧🔧🔧')],validators=[DataRequired()],coerce=int)
    playground_variety = SelectField('Playground Variety Rating',choices=[(1,'⭐'),(2,'⭐⭐'),(3,'⭐⭐⭐'),(4,'⭐⭐⭐⭐'),(5,'⭐⭐⭐⭐⭐')],validators=[DataRequired()],coerce=int)
    security = SelectField('How secure is the Park?',choices=[(1,'🛡️'),(2,'🛡️🛡️'),(3,'🛡️🛡️🛡️'),(4,'🛡️🛡️🛡️🛡️'),(5,'🛡️🛡️🛡️🛡️🛡️')],validators=[DataRequired()],coerce=int)
    tree_coverage = SelectField('Tree coverage in the Park?',choices=[(1,'🌳'),(2,'🌳🌳'),(3,'🌳🌳🌳'),(4,'🌳🌳🌳🌳'),(5,'🌳🌳🌳🌳🌳')],validators=[DataRequired()],coerce=int)
    img_url=StringField('Do you have a photo link for the park?',validators=[URL()])
    submit = SubmitField('Submit')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if not user:
            flash('No user found with this email address. Please try again.','danger')
            return redirect(url_for('login'))
        elif not check_password_hash(user.password,password):
            flash('Wrong password, please try again.','danger')
            return redirect(url_for('login'))
        else:
            login_user(user)
            flash('Login Successfully!','success')
            return redirect(url_for('parks'))
    return render_template('login.html',form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add_park',methods = ['GET','POST'])
def add_park():
    form = ParkForm()
    if form.validate_on_submit():
        new_park = Park(
            name=form.name.data,
            map_url = form.map_url.data,
            has_wc = form.has_wc.data,
            has_shop = form.has_shop.data,
            has_sport_area = form.has_sport_area.data,
            playground_condition = form.playground_condition.data,
            playground_variety= form.playground_variety.data,
            security = form.security.data,
            tree_coverage = form.tree_coverage.data,
            img_url = form.img_url.data if form.img_url.data else None
        )
        db.session.add(new_park)
        db.session.commit()
        return redirect(url_for('parks'))
    return render_template('add_park.html',form=form)

@app.route('/parks')
def parks():
    result = db.session.execute(db.select(Park).order_by(Park.name))
    all_parks = result.scalars().all()
    return render_template('parks.html',parks=all_parks)

@app.route('/edit_park/<int:park_id>',methods = ['GET','POST'])
def edit_park(park_id):
    park_to_edit = db.session.get(Park,park_id)
    if not park_to_edit:
        flash('Park not found.','danger')
        return redirect(url_for('parks'))
    form = ParkForm(obj=park_to_edit)

    if form.validate_on_submit():
        if current_user.is_authenticated:
            park_to_edit.name = form.name.data
            park_to_edit.map_url=form.map_url.data
            park_to_edit.has_wc=form.has_wc.data
            park_to_edit.has_shop=form.has_shop.data
            park_to_edit.has_sport_area=form.has_sport_area.data
            park_to_edit.playground_condition=form.playground_condition.data
            park_to_edit.playground_variety=form.playground_variety.data
            park_to_edit.security=form.security.data
            park_to_edit.tree_coverage=form.tree_coverage.data
            park_to_edit.img_url=form.img_url.data if form.img_url.data else None
            db.session.commit()
            return redirect(url_for('parks'))
        else:
            try:
                msg = Message(
                    subject=f'Park suggestion: {park_to_edit.name}',
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[os.environ.get('MAIL_RECIPIENTS')]
                )
                msg.body=f"""
                Park ID: {park_id}
                Park Name: {park_to_edit.name}
                Suggested changes:
                -Park Name: {form.name.data}
                -Map URL: {form.map_url.data}
                -Is there a WC?: {form.has_wc.data}
                -Is there a Shop?: {form.has_shop.data}
                -Is there a sport area?: {form.has_sport_area.data}
                -Playground condition rating: {form.playground_condition.data}
                -Playground variert rating: {form.playground_variety.data}
                -Security rating: {form.security.data}
                -Tree coverage rating: {form.tree_coverage.data}
                -Photo URL: {form.img_url.data}
                """
                mail.send(msg)
                flash('Your suggestion has been successfully submitted! It will be updated after review.','info')
            except Exception as e:
                flash('An error occurred while sending the email.','danger')
                print(f"Mail error: {e}")
            return redirect(url_for('parks'))
    return render_template('edit_park.html',form = form,park=park_to_edit,logged_in=current_user.is_authenticated)

@app.route('/delete_park/<int:park_id>',methods=['POST'])
@login_required
def delete_park(park_id):
    park_to_delete = db.session.get(Park,park_id)
    db.session.delete(park_to_delete)
    db.session.commit()
    flash(f"'{park_to_delete.name}' deleted successfully.",'success')
    return redirect(url_for('parks'))



@app.route('/chat',methods=['GET','POST'])
def chat_page():

    if 'chat_history' not in flask_session:
        flask_session['chat_history'] = []

    user_question = None
    if request.method== 'POST':
        user_question=request.form.get('user_question')

        if user_question:
            flask_session['chat_history'].append({'sender':'user','message':user_question})

            if not GEMINI_API_KEY:
                ai_answer = 'AI API key is not configured.'
            else:
                try:
                    all_parks = db.session.execute(db.select(Park)).scalars().all()
                    parks_info = '\n'.join([
                        f"- {park.name} (ID: {park.id}): Wc: {'Yes' if park.has_wc else 'No'}, Shop: {'Yes' if park.has_shop else 'No'},"
                        f"Sport Area: {'Yes' if park.has_sport_area else 'No'},Playgroun Condition: {park.playground_condition}/5,Tree coverage: {park.tree_coverage}/5,"
                        f"Security: {park.security}/5" for park in all_parks
                    ])
                    prompt=(
                            "You are a child-friendly park information assistant. Do not answer questions other than the park information provided to you and focus only on questions about these parks. "

                            "The following park information is available:\n\n"
                            f"{parks_info}\n\n"
                            "You can ask me questions about these parks. Do not answer general information or other topics. "
                            "Try to answer questions using the park name or ID. For example, you can ask questions like 'Ayşe Park has a restroom?' or 'What is the security status of park ID 5?'.\n\n"
                            f"User's question: {user_question}"
                        )
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    response = model.generate_content(prompt)
                    ai_answer= response.text

                except Exception as e:
                    print(f"Gemini API error: {e}")
                    ai_answer="Sorry, I can't respond right now. Please try again later."

            flask_session['chat_history'].append({'sender':'ai', 'message':ai_answer})

            flask_session.permanent = True
            flask_session.modified = True
            return redirect(url_for('chat_page'))

    return render_template('chat.html',chat_history = flask_session.get('chat_history'),user_question = user_question)




# API func's

@app.route('/api/all')
def get_all_parks():
    result =db.session.execute(db.select(Park))
    all_parks =result.scalars().all()
    return jsonify(parks=[park.to_dict() for park in all_parks])

@app.route('/api/add',methods = ['POST'])
def post_new_park():
    new_park=Park(
        name=request.form.get('name'),
        map_url = request.form.get('map_url'),
        has_wc = bool(request.form.get('has_wc')),
        has_shop = bool(request.form.get('has_shop')),
        has_sport_area = bool(request.form.get('has_sport_area')),
        playground_condition = request.form.get('playground_condition'),
        playground_variety= request.form.get('playground_variety'),
        security = request.form.get('security'),
        tree_coverage = request.form.get('tree_coverage'),
        img_url = request.form.get('img_url') if request.form.get('img_url') else None,
    )
    db.session.add(new_park)
    db.session.commit()
    return jsonify(response={'success':'Successfully added the new park.'}),201

@app.route('/api/update/<int:park_id>',methods=['PATCH'])
def update_park(park_id):
    try:
        park = Park.query.get(park_id)
        if not park:
            return jsonify(error={'Not found':'Park not found.'}),404
        for key,value in request.json.items():
            if hasattr(park,key):
                setattr(park,key,value)
        db.session.commit()
        return jsonify(response={'success':'Park updated successfully.'}),200
    except Exception as e:
        return jsonify(error={'Database Error':str(e)}), 500



if __name__ == '__main__':
  app.run(debug=True)
