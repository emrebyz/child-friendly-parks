from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

app = Flask(__name__)

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bootstrap = Bootstrap5(app)

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