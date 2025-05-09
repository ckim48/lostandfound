from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import os
import firebase_admin
from firebase_admin import credentials, db
from flask import jsonify
from flask_mail import Mail, Message





cred = credentials.Certificate('lostandfound.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://lostandfound-88035-default-rtdb.firebaseio.com/'
})

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'madckkim@gmail.com'
app.config['MAIL_PASSWORD'] = 'Dpdltm1212!'
app.config['MAIL_DEFAULT_SENDER'] = 'your_gmail@gmail.com'

mail = Mail(app)

# Dummy users and items (sample data)
users = {
    'alice': {'password': 'pass123', 'points': 40},
    'bob': {'password': 'pass123', 'points': 70},
    'carol': {'password': 'pass123', 'points': 20},
    'david': {'password': 'pass123', 'points': 90},
}
items = [
    {
        'title': 'Blue Water Bottle',
        'description': 'Found in the library next to the vending machine.',
        'image': 'water_bottle.jpg',
        'owner': 'alice',
        'status': 'lost',
        'returned': False
    },
    {
        'title': 'Samsung Galaxy Phone',
        'description': 'Black case, screen slightly cracked. Found in cafeteria.',
        'image': 'phone.jpg',
        'owner': 'bob',
        'status': 'lost',
        'returned': True
    },
    {
        'title': 'Physics Textbook',
        'description': 'Heavy textbook with a red cover. Found in lecture hall B.',
        'image': 'textbook.jpg',
        'owner': 'carol',
        'status': 'lost',
        'returned': False
    },
    {
        'title': 'Black Backpack',
        'description': 'Nike logo, contains folders and calculator. Left in gym.',
        'image': 'backpack.jpg',
        'owner': 'david',
        'status': 'lost',
        'returned': False
    },
    {
        'title': 'USB Drive',
        'description': 'Small black USB found in the computer lab.',
        'image': 'usb.jpg',
        'owner': 'eve',
        'status': 'found',
        'returned': False
    }

]
@app.route('/api/mark_returned', methods=['POST'])
def api_mark_returned():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.json
    title = data.get('title')

    items_ref = db.reference('items')
    all_items = items_ref.get()

    if all_items:
        for key, item in all_items.items():
            if item['owner'] == session['username'] and item['title'] == title and not item['returned']:
                items_ref.child(key).update({'returned': True})

                user_ref = db.reference(f'users/{session["username"]}')
                current_points = user_ref.child('points').get() or 0
                user_ref.update({'points': current_points + 10})

                return jsonify({'success': True})

    return jsonify({'error': 'Item not found or already returned'}), 404
@app.route('/contact_owner', methods=['POST'])
def contact_owner():
    if 'username' not in session:
        return redirect(url_for('login'))

    from_user = session['username']
    to_user = request.form.get('owner')
    item_title = request.form.get('item_title')

    finder_name = request.form.get('finder_name')
    finder_grade = request.form.get('finder_grade')
    finder_contact = request.form.get('finder_contact')
    finder_message = request.form.get('finder_message')

    user_ref = db.reference(f'users/{to_user}')
    recipient = user_ref.get()

    if not recipient:
        return "❌ Could not find the user.", 404

    recipient_email = recipient.get('email', 'no@email.com')

    # Email sending (requires Flask-Mail config)
    subject = f"[Lost & Found] {finder_name} may have found your item!"
    body = f"""
Hi {to_user},

Someone may have found your item titled: "{item_title}".

Message:
---------
{finder_message}

Finder Info:
- Name: {finder_name}
- Grade: {finder_grade}
- Contact: {finder_contact}

Please follow up if this seems like your lost item.

- Lost & Found System
    """

    try:
        msg = Message(subject, recipients=[recipient_email])
        msg.body = body
        mail.send(msg)
    except Exception as e:
        print(f"❌ Email failed: {e}")

    # Save to Firebase
    db.reference('messages').push({
        'from': from_user,
        'to': to_user,
        'item': item_title,
        'finder_name': finder_name,
        'finder_grade': finder_grade,
        'finder_contact': finder_contact,
        'message': finder_message,
        'seen': False
    })

    flash('Your message was successfully sent to the item owner! 🎉')
    return redirect(url_for('home'))


def insert_mock_items():
    mock_items = [
        {
            'title': 'Lost Math Notebook',
            'description': 'Blue spiral notebook with math notes. Left in Room 203.',
            'image': 'placeholder.jpg',
            'owner': 'alice',
            'status': 'lost',
            'returned': False
        },
        {
            'title': 'Black Umbrella',
            'description': 'Forgotten near cafeteria door. Handle slightly bent.',
            'image': 'placeholder.jpg',
            'owner': 'bob',
            'status': 'lost',
            'returned': False
        },
        {
            'title': 'Found Water Bottle',
            'description': 'Purple bottle with sticker. Found near the library stairs.',
            'image': 'placeholder.jpg',
            'owner': 'carol',
            'status': 'found',
            'returned': False
        },
        {
            'title': 'Found Wallet',
            'description': 'Brown leather wallet. Turned in from parking lot.',
            'image': 'placeholder.jpg',
            'owner': 'david',
            'status': 'found',
            'returned': False
        }
    ]

    ref = db.reference('items')
    for item in mock_items:
        ref.push(item)

    print("✅ Mock data inserted into Firebase.")

@app.route('/insert_mock_data')
def insert_mock_data():
    insert_mock_items()
    return "Mock data inserted successfully!"

@app.route('/')
def home():
    sorted_users = sorted(users.items(), key=lambda x: x[1]['points'], reverse=True)
    firebase_items = db.reference('items').get()
    items = list(firebase_items.values()) if firebase_items else []
    return render_template('index.html', items=items, sorted_users=sorted_users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.reference(f'users/{username}').get()
        if user and user['password'] == password:
            session['username'] = username
            return redirect(url_for('home'))
    return render_template('login.html')
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        name = request.form['name']
        grade = request.form['grade']
        email = request.form['email']
        role = request.form['role']

        ref = db.reference('users')
        if ref.child(username).get():
            return "Username already exists.", 400
        if password != confirm_password:
            return "Passwords do not match.", 400

        ref.child(username).set({
            'password': password,
            'points': 0,
            'name': name,
            'grade': grade,
            'email': email,
            'role': role
        })

        session['username'] = username
        return redirect(url_for('home'))

    return render_template('signup.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))


@app.route('/report_lost', methods=['GET', 'POST'])
def report_lost():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        image = request.files.get('image')
        sorted_users = sorted(users.items(), key=lambda x: x[1]['points'], reverse=True)

        # Handle image (optional)
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = 'placeholder.jpg'

        # Save to Firebase
        item_ref = db.reference('items')
        item_ref.push({
            'title': title,
            'description': description,
            'image': filename,
            'owner': session['username'],
            'status': 'lost',
            'returned': False
        })

        return redirect(url_for('home'))

    return render_template('report_lost.html', sorted_users=sorted_users)
@app.route('/report_found', methods=['POST'])
def report_found():
    if 'username' not in session:
        return redirect(url_for('login'))

    title = request.form['title']
    description = request.form['description']
    image = request.files.get('image')

    if image and image.filename != '':
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    else:
        filename = 'placeholder.jpg'

    item_ref = db.reference('items')
    item_ref.push({
        'title': title,
        'description': description,
        'image': filename,
        'owner': session['username'],
        'status': 'found',
        'returned': False
    })

    return redirect(url_for('home'))


@app.route('/mark_returned/<int:item_id>')
def mark_returned(item_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    if 0 <= item_id < len(items):
        items[item_id]['returned'] = True
        users[session['username']]['points'] += 10  # Reward points
    return redirect(url_for('home'))

@app.route('/explore')
def explore_items():
    all_items = db.reference('items').get()
    items = list(all_items.values()) if all_items else []
    return render_template('explore.html', items=items)

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    user = db.reference(f'users/{username}').get()
    all_items = db.reference('items').get()
    all_msgs = db.reference('messages').get()
    sorted_users = sorted(users.items(), key=lambda x: x[1]['points'], reverse=True)

    user_items = [item for item in all_items.values() if item['owner'] == username] if all_items else []
    received_messages = [msg for msg in all_msgs.values() if msg.get('to') == username] if all_msgs else []

    lost_items = [item for item in user_items if item['status'] == 'lost' and not item['returned']]
    found_items = [item for item in user_items if item['status'] == 'found' and not item['returned']]
    returned_items = [item for item in user_items if item['returned']]

    return render_template('profile.html',
                           username=username,
                           user=user,  # ✅ Add this line
                           points=user.get('points', 0),
                           lost_items=lost_items,
                           found_items=found_items,
                           returned_items=returned_items,
                           received_messages=received_messages,
                           sorted_users=sorted_users)




@app.route('/mark_returned_from_profile', methods=['POST'])
def mark_returned_from_profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    title = request.form.get('title')
    items_ref = db.reference('items')
    all_items = items_ref.get()

    # Find and update the first match (you can refine by ID if you later use them)
    if all_items:
        for key, item in all_items.items():
            if item['owner'] == session['username'] and item['title'] == title and not item['returned']:
                items_ref.child(key).update({'returned': True})
                # Add 10 points
                user_ref = db.reference(f'users/{session["username"]}')
                current_points = user_ref.child('points').get() or 0
                user_ref.update({'points': current_points + 10})
                break

    return redirect(url_for('profile'))


if __name__ == '__main__':
    os.makedirs('static/uploads', exist_ok=True)
    app.run(debug=True)
