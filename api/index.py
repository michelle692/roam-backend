# Utilities.
import requests
import json
import os

# Backend server.
from flask import Flask, request
from flask_cors import CORS

# Database.
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson import json_util

def parse_json(data):
    return json.loads(json_util.dumps(data))

# Google API.
GOOGLE_MAPS_KEY = 'key=' + os.environ['MAPS_KEY']
GOOGLE_MAPS_API_URL = 'https://maps.googleapis.com/maps/api/'
PLACES_API_URL = GOOGLE_MAPS_API_URL + 'place/autocomplete/json?types=locality&' + GOOGLE_MAPS_KEY
GEOCODING_API_URL = GOOGLE_MAPS_API_URL + 'geocode/json?' + GOOGLE_MAPS_KEY

# Create the backend server and enable CORS for frontend.
app = Flask(__name__)
CORS(app)

# Login into database.
mongo = MongoClient(os.environ['MONGODB'])
roam = mongo['roam']

# Access the db tables.
users = roam['users']
history = roam['history']

def hash_password(password):
    # Should hash the password here.
    return password

@app.route('/search')
def search():
    text = request.args.get("text")

    if text is None:
        return {'error': 'invalid args.'}

    return json.loads(requests.get(PLACES_API_URL + '&input=' + text).content)

@app.route('/info')
def info():
    place_id = request.args.get('place_id')

    if place_id is None:
        return {'error': 'invalid args.'}

    return json.loads(requests.get(GEOCODING_API_URL + '&place_id=' + place_id).content)

@app.route('/create')
def create():
    args = request.args
    if 'username' not in args or 'password' not in args or 'name' not in args:
        return {'error': 'missing args.'}

    username = args.get('username')

    # Make sure there is no account already.
    matches = list(users.find({ "username": username }))
    if len(matches) > 0:
        return {'error': 'username already exists.'}

    password = hash_password(args.get('password'))
    name = args.get('name')

    data = {
        'username': username,
        'password': password,
        'name': name
    }

    # Insert the data into the users table.
    result = users.insert_one(data)

    # Append unique user id into data and remove password.
    data['_id'] = str(result.inserted_id)
    data.pop('password')

    # Return this user back to the requester.
    return data

@app.route('/login')
def login():
    args = request.args
    if 'username' not in args or 'password' not in args:
        return {'error': 'missing args.'}
    
    username = args.get('username')

    # Search for this user in the database.
    matches = list(users.find({ "username": username }))
    if len(matches) == 0:
        return {'error': 'username not found.'}
    account = matches[0]

    # Verify the passwords are the same.
    if hash_password(args.get('password')) != account['password']:
        return {'error': 'password is incorrect.'}

    # Clean out the account object into a returnable account.
    output = {
        '_id': str(account['_id']),
        'username': account['username'],
        'name': account['name']
    }

    return output

@app.route('/history/add')
def add():
    args = request.args
    if 'user_id' not in args or 'city' not in args or 'place_id' not in args or 'notes' not in args or 'country' not in args or 'date' not in args or 'lat' not in args or 'lng' not in args:
        return {'error': 'missing args.'}

    user_id = ObjectId(args.get('user_id'))

    matches = list(users.find({ "_id": user_id }))
    if len(matches) == 0:
        return {'error': 'user_id does not exist.'}
    
    city = args.get('city')
    place_id = args.get('place_id')
    notes = args.get('notes')
    country = args.get('country')
    date = args.get('date')
    lat = args.get('lat')
    lng = args.get('lng')

    data = {
        'user_id': user_id,
        'city': city,
        'place_id': place_id,
        'notes': notes,
        'country': country,
        'date': date,
        'lat': lat,
        'lng': lng
    }

    # Insert the data into the users table.
    result = history.insert_one(data)

    # Return this user back to the requester.
    return parse_json(data)

@app.route('/history/get')
def get():
    args = request.args
    if 'user_id' not in args:
        return {'error': 'missing args.'}
    user_id = ObjectId(args.get('user_id'))

    usermatch = list(users.find({ "_id": user_id }))
    if len(usermatch) == 0:
        return {'error': 'user_id does not exist.'}
    
    matches = list(history.find({'user_id': user_id}))
    return parse_json(matches)

@app.route('/history/edit')
def edit():
    args = request.args
    if 'history_id' not in args:
        return {'error': 'missing args.'}
    
    history_id = ObjectId(args.get('history_id'))

    match = history.find_one({ "_id": history_id })

    if match is None:
        return {'error': 'history_id does not exist.'}

    if 'city' in args:
        match['city'] = args.get('city')
    if 'place_id' in args:
        match['place_id'] = args.get('place_id')
    if 'notes' in args:
        match['notes'] = args.get('notes')
    if 'country' in args:
        match['country'] = args.get('country')
    if 'date' in args:
        match['date'] = args.get('date')
    if 'lat' in args:
        match['lat'] = args.get('lat')
    if 'lng' in args:
        match['lng'] = args.get('lng')

    history.replace_one({'_id':history_id}, match)
    return parse_json(match)

@app.route('/history/remove')
def remove():
    args = request.args
    if 'history_id' not in args:
        return {'error': 'missing args.'}
    
    history_id = ObjectId(args.get('history_id'))

    match = history.find_one({ "_id": history_id })

    if match is None:
        return {'error': 'history_id does not exist.'}
    
    history.delete_one({'_id':history_id})
    return parse_json(match)
    