from flask import (
    Flask,
    flash,
    render_template,
    request,
    url_for,
    redirect,
    jsonify
)


import sys

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship, backref
from flask import make_response


from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

from sqlalchemy import create_engine
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import os
import random
import string
import httplib2
import json
import requests
app = Flask(__name__)
Base = declarative_base()
# creating a admin data base to vendor


class Admin(Base):
    __tablename__ = "admin"
    admin_id = Column(Integer, primary_key=True)
    admin_mail = Column(String(100), nullable=False)


# database to store fan categories
class Fans(Base):
    __tablename__ = "fan"
    fan_id = Column(Integer, primary_key=True)
    fan_name = Column(String(100), nullable=False)
    fan_admin = Column(Integer, ForeignKey('admin.admin_id'))
    fan_relation = relationship(Admin)


# items databse to store item details
class Items(Base):
    __tablename__ = "items"
    item_id = Column(Integer, primary_key=True)
    item_name = Column(String(100), nullable=False)
    item_price = Column(Integer, nullable=False)
    item_weight = Column(Integer, nullable=False)
    item_brand = Column(String(100), nullable=False)
    item_image = Column(String(1000), nullable=False)
    fan_id = Column(Integer, ForeignKey('fan.fan_id'))
    item_relation = relationship(
        Fans, backref=backref("items", cascade="all,delete"))

    @property
    def details(self):
        return {
                'name': self.item_name,
                'price': self.item_price,
                'weight': self.item_weight,
                'brand': self.item_brand,
                'img_url': self.item_image

        }


CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())
CLIENT_ID = CLIENT_ID['web']['client_id']

# end of line
engine = create_engine('sqlite:///fans.db')
Base.metadata.create_all(engine)

session = scoped_session(sessionmaker(bind=engine))


@app.route('/read')
def read():
    fan = session.query(Items).all()
    msg = ""
    for each in fan:
        msg += str(each.item_name)
    return msg


# home page of website
@app.route('/home')
def home():
    items = session.query(Items).all()
    return render_template('display_items.html', Items=items)


# to show categories
@app.route('/category', methods=['GET'])
def display_category():
    if request.method == 'GET':
        category_list = session.query(Fans).all()
        return render_template('show_category.html', categories=category_list)


# to show all the data in form of json
@app.route('/fans/all.json')
def all_fan():
    fan = session.query(Items).all()
    return jsonify(Items=[each.details for each in fan])


# showing the each category in the json format
@app.route('/fans/category/<int:id>.json')
def catjason(id):
    fan = session.query(Items).filter_by(fan_id=id).all()
    return jsonify(Items=[each.details for each in fan])


# add a new category in the website by a vendor
@app.route('/category/new', methods=['GET', 'POST'])
def newcategory():
    if not login_session.get('email', None):
        flash('you should login')
        return redirect(url_for('home'))
    if request.method == 'GET':
        return render_template('insert_category.html')
    else:
        category_name = request.form['category_name']
        if category_name:
            admin = session.query(Admin).filter_by(
                admin_mail=login_session['email']
                ).one_or_none()
            if not admin:
                return redirect(url_for('home'))
            admin_id = admin.admin_id
            new_fan = Fans(fan_name=category_name, fan_admin=admin_id)
            session.add(new_fan)
            session.commit()
            flash('your category added')
            return redirect(url_for('home'))
        else:
            flash('retry........')
            return redirect(url_for('home'))


# edit the category by authenticated people only
@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
def editcategory(category_id):
    if not login_session.get('email', None):
        flash('you should login')
        return redirect(url_for('home'))
    admin = session.query(Admin).filter_by(
        admin_mail=login_session['email']
        ).one_or_none()
    if not admin:
        return redirect(url_for('home'))
    fan = session.query(Fans).filter_by(fan_id=category_id).one_or_none()
    if not fan:
        flash('no category')
        return redirect(url_for('home'))
    login_admin_id = admin.admin_id
    admin_id = fan.fan_admin
    if login_admin_id != admin_id:
        flash('ur not authencated so try later...........')
        return redirect(url_for('home'))
    if request.method == 'POST':
        category_name = request.form['category_name']

        fan.fan_name = category_name
        session.add(fan)
        session.commit()
        flash('updated successfully')
        return redirect(url_for('home'))
    else:
        return render_template(
            'modify_category.html',
            fan_name=fan.fan_name,
            id_category=category_id
            )


@app.route('/category/<int:category_id>/delete')
def deletecategory(category_id):
    if not login_session.get('email', None):
        flash('you should login')
        return redirect(url_for('home'))
    admin = session.query(Admin).filter_by(
        admin_mail=login_session['email']
        ).one_or_none()
    if not admin:
        return redirect(url_for('home'))
    fan = session.query(Fans).filter_by(fan_id=category_id).one_or_none()
    if not fan:
        flash('no category')
        return redirect(url_for('home'))
    login_admin_id = admin.admin_id
    admin_id = fan.fan_admin
    if login_admin_id != admin_id:
        flash('ur not authencated so try later...........')
        return redirect(url_for('home'))
    name = fan.fan_name
    session.delete(fan)
    session.commit()
    flash('deleted successfully '+str(name))
    return redirect(url_for('home'))


@app.route('/latestitems')
def latestitems():
    if request.method == 'GET':
        category_list = session.query(Items).all()
    return render_template('latestitems.html', categories=category_list)


@app.route('/category/<int:category_id>/items')
def showcategoryitems(category_id):
    if request.method == 'GET':
        items = session.query(Items).filter_by(fan_id=category_id)
    return render_template('display_items.html', Items=items)


# showing details of particular item
@app.route(
    '/category/<int:category_id>/items/<int:itemid>',
    methods=['GET', 'POST']
    )
def iteminfo(category_id, itemid):
    if not login_session.get('email', None):
        flash('you should login')
        return redirect(url_for('home'))
    if request.method == 'GET':
        item = session.query(Items).filter_by(
            fan_id=category_id, item_id=itemid
            ).one_or_none()
        return render_template(
            'item_info.html',
            iname=item.item_name,
            iprice=item.item_price, iweight=item.item_weight,
            ibrand=item.item_brand, image=item.item_image
        )


# add new item in the selected category
@app.route('/category/<int:categoryid>/items/new', methods=['GET', 'POST'])
def newitem(categoryid):
    if not login_session.get('email', None):
        flash('you should login')
        return redirect(url_for('home'))
    admin = session.query(Admin).filter_by(
        admin_mail=login_session['email']
        ).one_or_none()
    if not admin:
        return redirect(url_for('home'))
    catname = session.query(Fans).filter_by(fan_id=categoryid).one_or_none()
    if catname is None:
        flash('category unavailable')
        return redirect(url_for('home'))
    login_admin_id = admin.admin_id
    admin_id = catname.fan_admin
    if login_admin_id != admin_id:
        flash('ur not correct person to add')
        return redirect(url_for('home'))
    if request.method == 'GET':
        return render_template('insert_item.html', cat_id=categoryid)
    else:
        name = request.form['iname']
        image = request.form['iimage']
        price = request.form['iprice']
        weight = request.form['iweight']
        brand = request.form['ibrand']
        sid = categoryid
        new_item = Items(
            item_name=name, item_price=price,
            item_weight=weight, item_brand=brand,
            item_image=image, fan_id=sid
            )
        session.add(new_item)
        session.commit()
        flash('your item added')
        return redirect(url_for('home'))


# editing item by authorised perons only
@app.route(
    '/category/<int:categoryid>/items/<int:itemid>/edit',
    methods=['GET', 'POST']
    )
def modifyitem(categoryid, itemid):
    if not login_session.get('email', None):
        flash('you should login')
        return redirect(url_for('home'))
    admin = session.query(Admin).filter_by(
        admin_mail=login_session['email']
        ).one_or_none()
    if not admin:
        return redirect(url_for('home'))
    catname = session.query(Fans).filter_by(fan_id=categoryid).one_or_none()
    if catname is None:
        flash('category unavailable')
        return redirect(url_for('home'))
    itname = session.query(Items).filter_by(
        fan_id=categoryid, item_id=itemid
        ).one_or_none()
    if not itname:
        flash('invalkid item')
        return redirect(url_for('home'))
    login_admin_id = admin.admin_id
    admin_id = catname.fan_admin
    if login_admin_id != admin_id:
        flash('ur not correct person to edit')
        return redirect(url_for('home'))
    if request.method == 'POST':
        name = request.form['iname']
        image = request.form['iimage']
        price = request.form['iprice']
        weight = request.form['iweight']
        brand = request.form['ibrand']
        item = session.query(Items).filter_by(
            fan_id=categoryid, item_id=itemid
            ).one_or_none()
        if item:
            item.item_name = name
            item.item_image = image
            item.item_price = price
            item.item_weight = weight
            item.item_brand = brand
        else:
            flash('no items')
            return redirect(url_for('home'))
        session.add(item)
        session.commit()
        flash('updated successfully')
        return redirect(url_for('home'))
    else:
        edit = session.query(Items).filter_by(item_id=itemid).one_or_none()
        if edit:
            return render_template(
                'modify_item.html', iname=edit.item_name,
                iprice=edit.item_price, iweight=edit.item_weight,
                ibrand=edit.item_brand, iimage=edit.item_image,
                catid=categoryid, iid=itemid
                )
        else:
            flash('no elements')
            return redirect(url_for('home'))


@app.route('/category/<int:categoryid>/items/<int:itemid>/delete')
def removeitem(categoryid, itemid):
    if not login_session.get('email', None):
        flash('you should login')
        return redirect(url_for('home'))
    admin = session.query(Admin).filter_by(
        admin_mail=login_session['email']
        ).one_or_none()
    if not admin:
        return redirect(url_for('home'))
    catname = session.query(Fans).filter_by(fan_id=categoryid).one_or_none()
    if catname is None:
        flash('category unavailable')
        return redirect(url_for('home'))
    itname = session.query(Items).filter_by(
        fan_id=categoryid, item_id=itemid
        ).one_or_none()
    if not itname:
        flash('invalkid item')
        return redirect(url_for('home'))
    login_admin_id = admin.admin_id
    admin_id = catname.fan_admin
    if login_admin_id != admin_id:
        flash('ur not correct person to edit')
        return redirect(url_for('home'))
    item = session.query(Items).filter_by(item_id=itemid).one_or_none()
    if item:
        name = item.item_name
        session.delete(item)
        session.commit()
        flash('deleted successfully '+str(name))
        return redirect(url_for('home'))
    else:
        flash('item not found')
        return redirect(url_for('home'))


# login routing
@app.route('/login')
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# it helps the user to loggedin and display flash profile


# GConnect
@app.route('/gconnect', methods=['POST', 'GET'])
def gConnect():
    if request.args.get('state') != login_session['state']:
        response.make_response(json.dumps('Invalid State paramenter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    request.get_data()
    code = request.data.decode('utf-8')

    # Obtain authorization code

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps("""Failed to upgrade the authorisation code"""), 401
            )
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.

    access_token = credentials.access_token
    myurl = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
        % access_token)
    header = httplib2.Http()
    result = json.loads(header.request(myurl, 'GET')[1].decode('utf-8'))

    # If there was an error in the access token info, abort.

    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.

    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps(
                            """Token's user ID does not
                            match given user ID."""),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.

    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps(
            """Token's client ID
            does not match app's."""),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200
            )
        response.headers['Content-Type'] = 'application/json'
        return response

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info

    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    # ADD PROVIDER TO LOGIN SESSION
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    admin_id = getEmailID(login_session['email'])
    if not admin_id:
        admin_id = new_User(login_session)
    login_session['owner_id'] = admin_id
    flash("welcome...... you are in  %s" % login_session['email'])
    return 'you are logged in .... Welcome'


def new_User(login_session):
    email = login_session['email']
    newUser = Admin(admin_mail=email)
    session.add(newUser)
    session.commit()
    admin = session.query(Admin).filter_by(admin_mail=email).first()
    adminId = admin.admin_id
    return adminId


def getEmailID(owner_email):
    try:
        owner = session.query(Admin).filter_by(admin_mail=owner_email).one()
        return owner.admin_id
    except Exception as e:
        print(e)
        return None


# Gdisconnect
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    del login_session['email']
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401
            )
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    header = httplib2.Http()
    result = header.request(url, 'GET')[0]

    if result['status'] == '200':

        # Reset the user's session.

        del login_session['access_token']
        del login_session['gplus_id']
        response = redirect(url_for('home'))
        response.headers['Content-Type'] = 'application/json'
        flash("successfully logged out", "success")
        return response
    else:

        # if given token is invalid, unable to revoke token
        response = make_response(json.dumps('Failed to revoke token for user'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/logout')
def logout():
    if login_session.get('email', None):
        gdisconnect()
        flash('you logged out')
        return redirect(url_for('home'))
    flash('you are logged out')
    return redirect(url_for('home'))


@app.context_processor
def inject_all():
    chai = session.query(Fans).all()
    return dict(mychai=chai)


if __name__ == '__main__':
    app.debug = True
    app.secret_key = "ramana"
    app.run(debug=True, host="localhost", port=5000)
