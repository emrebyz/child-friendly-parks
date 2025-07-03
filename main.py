from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, URL

app = Flask(__name__)

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)

app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

bootstrap = Bootstrap5(app)

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

class ParkForm(FlaskForm):
    park = StringField('Park name', validators=[DataRequired()])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/parks')
def parks():
    return render_template('parks.html')
@app.route('/chat')
def chat():
    return render_template('chat.html')
if __name__ == '__main__':
  app.run(debug=True)