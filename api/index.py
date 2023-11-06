# Utilities.
import requests
import json
import os

# Backend server.
from flask import Flask, request
from flask_cors import CORS

# Database.
from pymongo import MongoClient

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