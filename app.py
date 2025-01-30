# Install dependencies
# pip install flask pandas sqlalchemy scikit-learn flask-sqlalchemy mysqlclient

from flask import Flask, request, render_template
import pandas as pd
import random
from flask_sqlalchemy import SQLAlchemy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Load datasets
trending_products = pd.read_csv("models/trending_products.csv")
train_data = pd.read_csv("models/clean_data.csv")

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:@localhost/ecom"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Signup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Signin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Helper functions
def truncate(text, length=30):
    return text[:length] + "..." if len(text) > length else text

def content_based_recommendations(item_name, top_n=10):
    if item_name not in train_data['Name'].values:
        return pd.DataFrame()
    
    tfidf_matrix = TfidfVectorizer(stop_words='english').fit_transform(train_data['Tags'])
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    item_idx = train_data[train_data['Name'] == item_name].index[0]
    similar_items = sorted(enumerate(cosine_sim[item_idx]), key=lambda x: x[1], reverse=True)[1:top_n+1]
    
    return train_data.iloc[[x[0] for x in similar_items]][['Name', 'ReviewCount', 'Brand', 'ImageURL', 'Rating']]

# Predefined images
random_image_urls = [f"static/img/img_{i}.png" for i in range(1, 9)]

# Routes
@app.route("/")
def index():
    return render_template('index.html', trending_products=trending_products.head(8), truncate=truncate,
                           random_product_image_urls=[random.choice(random_image_urls) for _ in range(8)],
                           random_price=random.choice([40, 50, 60, 70, 100, 122, 106, 50, 30, 50]))

@app.route("/main")
def main():
    return render_template('main.html')

@app.route("/signup", methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        db.session.add(Signup(username=request.form['username'], email=request.form['email'], password=request.form['password']))
        db.session.commit()
    return index()

@app.route("/signin", methods=['POST', 'GET'])
def signin():
    if request.method == 'POST':
        db.session.add(Signin(username=request.form['signinUsername'], password=request.form['signinPassword']))
        db.session.commit()
    return index()

@app.route("/recommendations", methods=['POST', 'GET'])
def recommendations():
    if request.method == 'POST':
        content_based_rec = content_based_recommendations(request.form.get('prod'), int(request.form.get('nbr')))
        return render_template('main.html', content_based_rec=content_based_rec if not content_based_rec.empty else None,
                               message="No recommendations available." if content_based_rec.empty else None,
                               truncate=truncate,
                               random_product_image_urls=[random.choice(random_image_urls) for _ in range(8)],
                               random_price=random.choice([40, 50, 60, 70, 100, 122, 106, 50, 30, 50]))

if __name__ == '__main__':
    app.run(debug=True)
