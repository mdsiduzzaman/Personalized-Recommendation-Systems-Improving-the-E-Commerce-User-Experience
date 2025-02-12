from flask import Flask, request, render_template
import pandas as pd
import random
from flask_sqlalchemy import SQLAlchemy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Load files ==========================================================================================
try:
    trending_products = pd.read_csv("models/trending_products.csv")
    train_data = pd.read_csv("models/clean_data.csv")
    print("✅ Data loaded successfully!")
except Exception as e:
    print(f"❌ Error loading CSV files: {e}")

# Database Configuration -------------------------------------------------------------------------------
app.secret_key = "alskdjfwoeieiurlskdjfslkdjf"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:@localhost/ecom"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models ======================================================================================
class Signup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Signin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Recommendations Functions ============================================================================

def truncate(text, length):
    return text[:length] + "..." if len(text) > length else text

def content_based_recommendations(train_data, item_name, top_n=10):
    if 'Name' not in train_data.columns or 'Tags' not in train_data.columns:
        print("❌ Error: Missing required columns in dataset.")
        return pd.DataFrame()

    if item_name not in train_data['Name'].values:
        print(f"❌ Item '{item_name}' not found in dataset.")
        return pd.DataFrame()

    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(train_data['Tags'])
    
    print("✅ TF-IDF matrix shape:", tfidf_matrix.shape)

    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    item_index = train_data[train_data['Name'] == item_name].index[0]

    similar_items = list(enumerate(cosine_sim[item_index]))
    similar_items = sorted(similar_items, key=lambda x: x[1], reverse=True)[1:top_n+1]
    
    recommended_indices = [x[0] for x in similar_items]
    recommended_items = train_data.iloc[recommended_indices][['Name', 'ReviewCount', 'Brand', 'ImageURL', 'Rating']]
    
    print("✅ Recommended Items:", recommended_items)
    return recommended_items

# Routes ==============================================================================================

random_image_urls = [
    "static/img/img_1.png", "static/img/img_2.png", "static/img/img_3.png",
    "static/img/img_4.png", "static/img/img_5.png", "static/img/img_6.png"
]

@app.route("/")
def index():
    random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products.head(8)))]
    price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
    return render_template('index.html', trending_products=trending_products.head(8), truncate=truncate,
                           random_product_image_urls=random_product_image_urls, random_price=random.choice(price))

@app.route("/main")
def main():
    random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(train_data.head(8)))]
    price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]

    products = train_data[['Name', 'ReviewCount', 'Brand', 'ImageURL', 'Rating']].head(8)

    return render_template('main.html', trending_products=products, truncate=truncate,
                           random_product_image_urls=random_product_image_urls, random_price=random.choice(price))

@app.route("/signup", methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(train_data.head(8)))]
        price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]

        products = train_data[['Name', 'ReviewCount', 'Brand', 'ImageURL', 'Rating']].head(8)
        
        if Signup.query.filter_by(email=email).first():
            return render_template('index.html', signup_message="❌ Email already exists!",trending_products=products, truncate=truncate,
                               random_product_image_urls=random_product_image_urls, random_price=random.choice(price))
        
        new_signup = Signup(username=username, email=email, password=password)
        db.session.add(new_signup)
        db.session.commit()

        

        return render_template('index.html', signup_message="✅ User signed up successfully!", 
                               trending_products=products, truncate=truncate,
                               random_product_image_urls=random_product_image_urls, random_price=random.choice(price))

@app.route("/signin", methods=['POST', 'GET'])
def signin():
    random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(train_data.head(8)))]
    price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]

    products = train_data[['Name', 'ReviewCount', 'Brand', 'ImageURL', 'Rating']].head(8)

    if request.method == 'POST':
        username = request.form['signinUsername']
        password = request.form['signinPassword']

        user = Signin.query.filter_by(username=username, password=password).first()
        if not user:
            return render_template('index.html', signin_message="❌ Invalid login credentials!",
                                   trending_products=products, truncate=truncate,
                                   random_product_image_urls=random_product_image_urls, random_price=random.choice(price))
        
        return render_template('index.html', signin_message="✅ User signed in successfully!", 
                               trending_products=products, truncate=truncate,
                               random_product_image_urls=random_product_image_urls, random_price=random.choice(price))

@app.route("/recommendations", methods=['POST', 'GET'])
def recommendations():
    if request.method == 'POST':
        prod = request.form.get('prod')
        nbr = request.form.get('nbr')

        print(f"🛒 Received product: {prod}")
        print(f"🔢 Number of recommendations requested: {nbr}")

        random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(train_data.head(8)))]
        price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]

        products = train_data[['Name', 'ReviewCount', 'Brand', 'ImageURL', 'Rating']].head(8)

        if not prod or not nbr:
            return render_template('main.html', message="⚠️ Please enter valid inputs.",trending_products=products, truncate=truncate,
                                   random_product_image_urls=random_product_image_urls, random_price=random.choice(price))

        try:
            nbr = int(nbr)
        except ValueError:
            return render_template('main.html', message="⚠️ Please enter a valid number.",trending_products=products, truncate=truncate,
                                   random_product_image_urls=random_product_image_urls, random_price=random.choice(price))

        filtered_products = train_data[train_data['Name'].str.contains(prod, case=False, na=False)].head(nbr)

        if filtered_products.empty:
            return render_template('main.html', message="⚠️ No matching products found.",trending_products=products, truncate=truncate,
                                   random_product_image_urls=random_product_image_urls, random_price=random.choice(price))

        random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(filtered_products))]
        price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]

        return render_template('main.html', trending_products=filtered_products, truncate=truncate,
                               random_product_image_urls=random_product_image_urls, random_price=random.choice(price))

if __name__ == '__main__':
    app.run(debug=True)
