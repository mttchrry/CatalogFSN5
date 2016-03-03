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

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        return JSONEncoder.default(self, obj)

app.json_encoder = CustomJSONEncoder

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "FSN Catalog"


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

    login_session['provider'] = 'google'
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
    print "Got HERE!"
    print credentials
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print credentials
    access_token = credentials
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
        return redirect(url_for('showCatalog'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCatalog'))


# JSON APIs to view Catagory Information
@app.route('/catagory/<string:catagory_name>/json')
@app.route('/catagory/<string:catagory_name>/JSON')
def catagoryJSON(catagory_name):
    catagory = session.query(Catagory).filter_by(name=catagory_name).one()
    items = session.query(CatalogItem).filter_by(
        catagory_name=catagory_name).all()
    return jsonify(items=[i.serialize for i in items])

@app.route('/catagory/<string:catagory_name>/<string:item_name>/json')
@app.route('/catagory/<string:catagory_name>/<string:item_name>/JSON')
def catagoryItemJSON(catagory_name, item_name):
    catagory_Item = session.query(CatalogItem).filter_by(name=item_name).one()
    return jsonify(items=catagory_Item.serialize)

@app.route('/catagory/json')
@app.route('/catagory/JSON')
def catalogJSON():
    catalog = session.query(Catagory).all()
    return jsonify(catalog=[c.serialize for c in catalog])

@app.route('/catalog/json')
@app.route('/catalog/JSON')
def catalogItemJSON():
    print "we got to the jsoner"
    catalog = session.query(CatalogItem).all()
    return jsonify(catalog=[c.serialize for c in catalog])

# Show all catagories and recent items.
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    catagories = session.query(Catagory).order_by(asc(Catagory.name)).all()
    latestItems = session.query(CatalogItem).order_by(CatalogItem.created_date.desc()).limit(10)
    if 'username' in login_session:
      return render_template('catalog.html', catagories=catagories, items=latestItems)
    return render_template('publiccatalog.html', catagories=catagories, items=latestItems)

# Create a new catagory
@app.route('/catagory/new/', methods=['GET', 'POST'])
def newCatagory():
    if 'username' not in login_session: 
        return redirect(url_for('showLogin'))
    if request.method == 'POST':
        existing_name = session.query(Catagory).filter_by(name=request.form['name']).first()
        if existing_name is not None:
            flash('A catagory with the name %s already exists, Catagory not created.' % (request.form['name']))
            return redirect(url_for('showCatalog'))
            # '<script>function myFunction() {alert("A catagory with this name already exists, Catagory not created.");}</script><body onload="myFunction()"">'
        newCatagory = Catagory(name=request.form['name'], 
            user_id=login_session['user_id'])
        session.add(newCatagory)
        flash('New Catagory %s Successfully Created' % newCatagory.name)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('newcatagory.html')

# Edit a catagory
@app.route('/catagory/<string:catagory_name>/edit/', methods=['GET', 'POST'])
def editCatagory(catagory_name):
    if 'username' not in login_session: 
        return redirect(url_for('showLogin'))
    editedCatagory = session.query(
        Catagory).filter_by(name=catagory_name).one()
    if editedCatagory.user_id != login_session['user_id']:
        return '<script>function myFunction() {alert("You are not authorized to edit this catagory. Please create your own catagory in order to Edit.");}</script><body onload="myFunction()"">'
    if request.method == 'POST':
        existing_name = session.query(Catagory).filter_by(name=request.form['name']).one()
        if existing_name is not None:
            flash('A catagory with the name %s alread exists, Catagory not edited.' % (request.form['name']))
            return redirect(url_for('showCatalog'))
        if request.form['name']:
            editedCatagory.name = request.form['name']
            flash('Catagory Successfully Edited %s' % editedCatagory.name)
            return redirect(url_for('showCatalog'))
    else:
        return render_template('editcatagory.html', catagory=editedCatagory)


# Delete a catagory
@app.route('/catagory/<string:catagory_name>/delete/', methods=['GET', 'POST'])
def deleteCatagory(catagory_name):
    if 'username' not in login_session: 
        return redirect(url_for('showLogin'))
    catagoryToDelete = session.query(
        Catagory).filter_by(name=catagory_name).one()
    if catagoryToDelete.user_id != login_session['user_id']:
        return '<script>function myFunction() {alert("You are not authorized to delete this catagory. Please create your own catagory in order to delete.");}</script><body onload="myFunction()"">'    
    if request.method == 'POST':
        itemsInCatagory = session.query(CatalogItem).filter_by(catagory_name=catagoryToDelete.name).all()
        for item in itemsInCatagory:
            session.delete(item)
        session.delete(catagoryToDelete)
        flash('%s Successfully Deleted' % catagoryToDelete.name)
        session.commit()
        return redirect(url_for('showCatalog', catagory_name=catagory_name))
    else:
        return render_template('deletecatagory.html', catagory=catagoryToDelete)

# Show a catagory
@app.route('/catagory/<string:catagory_name>/')
def showCatagory(catagory_name):
    catagory = session.query(Catagory).filter_by(name=catagory_name).first()
    if catagory is None:
        flash('No Catagory with the name %s.' % (catagory_name))
        return redirect(url_for('showCatalog'))  
    items = session.query(CatalogItem).filter_by(
        catagory_name=catagory_name).all()
    creator = getUserInfo(catagory.user_id)
    if ('username' not in login_session) or (login_session['user_id'] != catagory.user_id):
        print items
        return render_template('publiccatagory.html', items=items, catagory=catagory, creator = creator)
    return render_template('catagory.html', items=items, catagory=catagory, creator = creator)

#show a catalog item
@app.route('/catagory/<string:catagory_name>/<string:item_name>')
def showCatalogItem(catagory_name, item_name):
    userId = ''
    if 'username' in login_session: 
        userId = login_session['user_id']
    catalogItem = session.query(CatalogItem).filter_by(name=item_name, catagory_name=catagory_name).one()
    return render_template('showcatalogitem.html', catagory_name=catagory_name, item=catalogItem, user_id=userId)


# Create a new item
@app.route('/catagory/<string:catagory_name>/new/', methods=['GET', 'POST'])
def newCatalogItem(catagory_name):
    if 'username' not in login_session: 
        return redirect(url_for('showLogin'))
    catagories = session.query(Catagory).order_by(asc(Catagory.name)).all()
    if request.method == 'POST':
        selectedCatagory = session.query(Catagory).filter_by(name=request.form['catagory']).first()
        existing_item = session.query(CatalogItem).filter_by(name=request.form['name'], catagory_name=selectedCatagory.name).first()
        if existing_item is not None:
            flash('An item with the name %s alread exists in Catagory %s. Item not created.' % (request.form['name'], selectedCatagory.name))
            return redirect(url_for('showCatalog'))       
        newItem = CatalogItem(name=request.form['name'], description=request.form['description'], 
            catagory_name=selectedCatagory.name, user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash('New %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showCatagory', catagory_name=selectedCatagory.name))
    else:
        return render_template('newcatalogitem.html', catagory_name=catagory_name, catagories=catagories)

@app.route('/new/', methods=['GET'])
def brandNewCatalogItem():
    if 'username' not in login_session: 
        return redirect(url_for('showLogin'))
    catagory = session.query(Catagory).order_by(asc(Catagory.name)).first()
    return redirect(url_for('newCatalogItem', catagory_name=catagory.name))

# Edit an item
@app.route('/catagory/<string:catagory_name>/<string:item_name>/edit', methods=['GET', 'POST'])
def editCatalogItem(catagory_name, item_name):
    if 'username' not in login_session: 
        return redirect(url_for('showLogin'))
    editedItem = session.query(CatalogItem).filter_by(name=item_name, catagory_name=catagory_name).first()
    if editedItem is None:
        return '<script>function myFunction() {alert("No Item here. Return to Main Page.");}</script><body onload="myFunction()"">'
    if editedItem.user_id != login_session['user_id']:
        return '<script>function myFunction() {alert("You are not authorized to edit this item. Please create your own catalog item in order to Edit.");}</script><body onload="myFunction()"">'
    if request.method == 'POST':
        selectC = session.query(Catagory).filter_by(name=request.form['catagory'])
        selectedCatagory = session.query(Catagory).filter_by(name=request.form['catagory']).one()
        # If we've changed the name or description, we need to make sure we don't duplciate another item
        if  editedItem.name != request.form['name'] or editedItem.catagory_name != selectedCatagory.name:
            existing_item = session.query(CatalogItem).filter_by(name=request.form['name'], catagory_name=selectedCatagory.name).first()
            if existing_item is not None:
                flash('An item with the name %s alread exists in Catagory %s. Item not edited' % (request.form['name'], selectedCatagory.name))
                return redirect(url_for('showCatalog'))    
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['catagory']:
            editedItem.catagory = selectedCatagory
            editedItem.catagory_name = selectedCatagory.name
        session.add(editedItem)
        session.commit()
        flash('Catalog Item Successfully Edited')
        return redirect(url_for('showCatagory', catagory_name=catagory_name))
    else:
        catagories = session.query(Catagory).order_by(asc(Catagory.name)).all()
        return render_template('editcatalogitem.html', catagory_name=catagory_name, item=editedItem, catagories=catagories)


# Delete a item item
@app.route('/catagory/<string:catagory_name>/<string:item_name>/delete', methods=['GET', 'POST'])
def deleteCatalogItem(catagory_name, item_name):
    if 'username' not in login_session: 
        return redirect(url_for('showLogin'))
    itemToDelete = session.query(CatalogItem).filter_by(name=item_name).first()
    if itemToDelete is None:
        return '<script>function myFunction() {alert("Item Does not exist, return to main page.");}</script><body onload="myFunction()"">'
    if itemToDelete.user_id != login_session['user_id']:
        return '<script>function myFunction() {alert("You are not authorized to delete this item. Please create your own Catalog item in order to delete.");}</script><body onload="myFunction()"">'
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Catalog Item Successfully Deleted')
        return redirect(url_for('showCatagory', catagory_name=catagory_name))
    else:
        return render_template('deleteitem.html', item=itemToDelete)


def getUserID(email):
  try:
    user = session.query(User).filter_by(email=email).one()
    return user.id
  except:
    return None


def getUserInfo(user_id):
    try:
        user = session.query(User).filter_by(id=user_id).one()
        return user
    except:
        return None


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
