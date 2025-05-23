import random
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, db

# Initialize Firebase app (make sure this points to your correct JSON)
cred = credentials.Certificate('lostandfound.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://lostandfound-88035-default-rtdb.firebaseio.com/'
})

def add_random_lost_dates():
    ref = db.reference('items')
    items = ref.get()

    if not items:
        print("No items found.")
        return

    for key, item in items.items():
        if item.get('status') == 'lost' and 'lost_date' not in item:
            # Generate a random date within the last 30 days
            random_days_ago = random.randint(0, 30)
            random_date = (datetime.now() - timedelta(days=random_days_ago)).strftime('%Y-%m-%d')

            # Update item
            ref.child(key).update({'lost_date': random_date})
            print(f"✅ Updated '{item['title']}' with lost_date: {random_date}")

    print("✅ All applicable items updated.")

if __name__ == '__main__':
    add_random_lost_dates()
