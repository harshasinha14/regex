from flask import Flask
from flaskext.markdown import Markdown  # this package renders the displacy on HTML page in flask app

app = Flask(__name__)
Markdown(app)
#from app import views
