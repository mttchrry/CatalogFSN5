# Ctrl+Shift+R reformats python code according to the Python PEP8
# AutoFormat package
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catagory, CatalogItem, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "FSN Menu Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///catalogwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

# Facebook Response method for Login attempt
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]


    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output

@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

# response method from login attempt
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        print 'got 1'
        print request.args.get('state')
        print login_session['state']
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
   
    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

   
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    userId = getUserID(login_session['email'])
    if userId == None:
        userId = createUser(login_session)
    login_session['user_id'] = userId

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showRestaurants'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showRestaurants'))


# JSON APIs to view Catagory Information
@app.route('/catagory/<int:catagory_id>/menu/JSON')
def restaurantMenuJSON(catagory_id):
    catagory = session.query(Catagory).filter_by(id=catagory_id).one()
    items = session.query(CatalogItem).filter_by(
        catagory_id=catagory_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/catagory/<int:catagory_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(catagory_id, menu_id):
    Menu_Item = session.query(CatalogItem).filter_by(id=menu_id).one()
    return jsonify(Menu_Item=Menu_Item.serialize)


@app.route('/catagory/JSON')
def restaurantsJSON():
    restaurants = session.query(Catagory).all()
    return jsonify(restaurants=[r.serialize for r in restaurants])


# Show all restaurants
@app.route('/')
@app.route('/catagory/')
def showRestaurants():
    catagories = session.query(Catagory).order_by(asc(Catagory.name)).all()
    print catagories
    print "what the hell"
    if 'username' in login_session:
      return render_template('catalog.html', catagories=catagories)
    return render_template('publiccatalog.html', catagories=catagories)

# Create a new catagory
@app.route('/catagory/new/', methods=['GET', 'POST'])
def newRestaurant():
    if 'username' not in login_session: 
        return redirect(url_for('showLogin'))
    if request.method == 'POST':
        newRestaurant = Catagory(name=request.form['name'], 
            user_id=login_session['user_id'])
        session.add(newRestaurant)
        flash('New Catagory %s Successfully Created' % newRestaurant.name)
        session.commit()
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('newRestaurant.html')

# Edit a catagory
@app.route('/catagory/<int:catagory_id>/edit/', methods=['GET', 'POST'])
def editCatagory(catagory_id):
    if 'username' not in login_session: 
        return redirect(url_for('showLogin'))
    editedRestaurant = session.query(
        Catagory).filter_by(id=catagory_id).one()
    if editedRestaurant.user_id != login_session['user_id']:
        return '<script>function myFunction() {alert("You are not authorized to edit this catagory. Please create your own catagory in order to Edit.");}</script><body onload="myFunction()"">'
    if request.method == 'POST':
        if request.form['name']:
            editedRestaurant.name = request.form['name']
            flash('Catagory Successfully Edited %s' % editedRestaurant.name)
            return redirect(url_for('showRestaurants'))
    else:
        return render_template('editCatagory.html', catagory=editedRestaurant)


# Delete a catagory
@app.route('/catagory/<int:catagory_id>/delete/', methods=['GET', 'POST'])
def deleteRestaurant(catagory_id):
    if 'username' not in login_session: 
        return redirect(url_for('showLogin'))
    restaurantToDelete = session.query(
        Catagory).filter_by(id=catagory_id).one()
    if restaurantToDelete.user_id != login_session['user_id']:
        return '<script>function myFunction() {alert("You are not authorized to delete this catagory. Please create your own catagory in order to delete.");}</script><body onload="myFunction()"">'    
    if request.method == 'POST':
        session.delete(restaurantToDelete)
        flash('%s Successfully Deleted' % restaurantToDelete.name)
        session.commit()
        return redirect(url_for('showRestaurants', catagory_id=catagory_id))
    else:
        return render_template('deleteRestaurant.html', catagory=restaurantToDelete)

# Show a catagory menu
@app.route('/catagory/<int:catagory_id>/')
@app.route('/catagory/<int:catagory_id>/menu/')
def showCatagory(catagory_id):
    catagory = session.query(Catagory).filter_by(id=catagory_id).one()
    items = session.query(CatalogItem).filter_by(
        catagory_id=catagory_id).all()
    creator = getUserInfo(catagory.user_id)
    if ('username' not in login_session) or (login_session['user_id'] != catagory.user_id):
        print items
        return render_template('publiccatagory.html', items=items, catagory=catagory, creator = creator)
    return render_template('catagory.html', items=items, catagory=catagory, creator = creator)

# Create a new menu item
@app.route('/catagory/<int:catagory_id>/menu/new/', methods=['GET', 'POST'])
def newCatalogItem(catagory_id):
    if 'username' not in login_session: 
        return redirect(url_for('showLogin'))
    catagory = session.query(Catagory).filter_by(id=catagory_id).one()
    if request.method == 'POST':
        newItem = CatalogItem(name=request.form['name'], description=request.form['description'], 
            price=request.form['price'], course=request.form['course'], catagory_id=catagory_id, 
            user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash('New Menu %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showCatagory', catagory_id=catagory_id))
    else:
        return render_template('newmenuitem.html', catagory_id=catagory_id)

# Edit a menu item
@app.route('/catagory/<int:catagory_id>/menu/<int:menu_id>/edit', methods=['GET', 'POST'])
def editCatalogItem(catagory_id, menu_id):
    if 'username' not in login_session: 
        return redirect(url_for('showLogin'))
    editedItem = session.query(CatalogItem).filter_by(id=menu_id).one()
    if editedItem.user_id != login_session['user_id']:
        return '<script>function myFunction() {alert("You are not authorized to edit this item. Please create your own menu item in order to Edit.");}</script><body onload="myFunction()"">'
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['course']:
            editedItem.course = request.form['course']
        session.add(editedItem)
        session.commit()
        flash('Menu Item Successfully Edited')
        return redirect(url_for('showCatagory', catagory_id=catagory_id))
    else:
        return render_template('editmenuitem.html', catagory_id=catagory_id, menu_id=menu_id, item=editedItem)


# Delete a menu item
@app.route('/catagory/<int:catagory_id>/menu/<int:menu_id>/delete', methods=['GET', 'POST'])
def deleteMenuItem(catagory_id, menu_id):
    if 'username' not in login_session: 
        return redirect(url_for('showLogin'))
    itemToDelete = session.query(CatalogItem).filter_by(id=menu_id).one()
    if itemToDelete.user_id != login_session['user_id']:
        return '<script>function myFunction() {alert("You are not authorized to delete this item. Please create your own menu item in order to delete.");}</script><body onload="myFunction()"">'
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Menu Item Successfully Deleted')
        return redirect(url_for('showCatagory', catagory_id=catagory_id))
    else:
        return render_template('deleteMenuItem.html', item=itemToDelete)


def getUserID(email):
  try:
    user = session.query(User).filter_by(email=email).one()
    return user.id
  except:
    return None


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    newUser = User(name = login_session['username'], email =
        login_session['email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
