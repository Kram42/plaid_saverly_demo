from flask import Flask,request,json, jsonify
from flask_restful import Api, Resource
from plaid import Client
from plaid import errors as plaid_errors
from plaid.utils import json
from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model


webapp = Flask(__name__)
api = Api(webapp)
database = SqliteDatabase("test.db")
database.connect()


# Base model class, created to cause other models to automatically be stored in called database
class BaseModel(Model):
    class Meta:
        database = database

# the user model specifies its fields (or columns) declaratively, like django
class User(BaseModel):
    username = CharField(unique=True)
    #password = CharField()
    accessToken = CharField()

    class Meta:
        order_by = ('username',)

# the user model specifies its fields (or columns) declaratively, like django
"""class Credentials(BaseModel):
    name = CharField(unique=True)
    id = CharField()
    secret = CharField()

    class Meta:
        order_by = ('name',)"""


database.create_table(User, safe=True)


Client.config({
    'url': 'https://tartan.plaid.com'
})
#ident = Person.get(Person.name == 'Grandma L.')
#print(ident)
id = "57b4faff66710877408d0856"             # obtain id and secret from db, same for all queries
secret = "45d1a44d9c7a4f3ede7d61bfc32630"
"""ident = Credentials(name = 'main', id = id, secret = secret)
ident.save()
ident = Credentials.get(Credentials.name == 'main')
print(ident)"""
client = Client(client_id=id, secret=secret)
account_type = 'chase'


def answer_mfa(data, client):
    if data['type'] == 'questions':
        # Ask your user for the answer to the question[s].
        # Although questions is a list, there is only ever a
        # single element in this list, at present
        return answer_question([q['question'] for q in data['mfa']])
    elif data['type'] == 'list':
        return answer_list(data['mfa'])
    elif data['type'] == 'selection':
        return answer_selections(data['mfa'])
    else:
        raise Exception('Unknown mfa type from Plaid')

def answer_question(questions): #questions
    # We have magically inferred the answer
    # so we respond immediately
    # In the real world, we would present questions[0]
    # to our user and submit their response
    answer = 'dogs'
    return client.connect_step('chase', answer) #replace 'chase' with account_type in full program

def answer_list(devices): #devices
    # You should specify the device to which the passcode is sent.
    # The available devices are present in the devices list
    code = input("Enter code: ")
    return client.connect_step('chase', code, options={
        'send_method': {'type': 'email'}
    })

def answer_selections(selections): #selections
    # We have magically inferred the answers
    # so we respond immediately
    # In the real world, we would present the selection
    # questions and choices to our user and submit their responses
    # in a JSON-encoded array with answers provided
    # in the same order as the given questions
    answer = json.dumps(['Yes', 'No'])
    return client.connect_step('chase', answer)


@api.resource('/users/<user>')
class api_user(Resource):
    # params: Json data - {'password':[password here]}
    # returns: Json data - stored info {"accesstoken", "id", "username"}
    # Creates a connect user based on url username and parameter password, then stores relevant information in the database.
    def post(self, user):
        jsonData = request.get_json(cache=False)

        try:
            response = client.connect(account_type, {
                'username': user,  # tedwerbel0901
                'password': jsonData['password']   # #Saverly7114#
            })
        except plaid_errors.UnauthorizedError:
            print("Password Error")
        else:
            if response.status_code == 200:
                # User connected
                data = response.json()
                #print(data)
                access_token = data['access_token']
                #print(access_token)
                newUser = User(username = user, accessToken = access_token)
                newUser.save()
                userData = User.get(User.username == user)
                userData = jsonify(model_to_dict(userData))
                client.upgrade('info')
                return userData
            elif response.status_code == 201:
                # MFA required
                try:
                    mfa_response = answer_mfa(response.json())
                    print(mfa_response)
                except plaid_errors.PlaidError:
                    print("MFA Error")
                else:
                    # User connected
                    data = response.json()
                    #print(data)
                    access_token = data['access_token']
                    #print(access_token)
                    newUser = User(username = user, accessToken = access_token)
                    newUser.save()
                    userData = User.get(User.username == user)
                    userData = jsonify(model_to_dict(userData))
                    client.upgrade('info')
                    return userData

@api.resource('/users/<user>/info') #Change to 'get' command for user?
class api_info(Resource):
   # params: None
   # returns: Json data - user info {"accesstoken", "id", "username"}
   # Connects to connect user (if it exists - need to create user first) and returns user info
   def get(self, user):
       userData = User.get(User.username == user)
       userData = model_to_dict(userData)
       access_token = userData['accessToken']
       #print(access_token)
       client = Client(client_id=id, secret=secret, access_token=access_token)
       #client.upgrade('info')
       info = client.info_get().json()
       return info

@api.resource('/users/<user>/balances')
class api_balances(Resource):
   # params: None
   # returns: Json data - user balance info {"accounts"[... "balance" {"available", "current"} ...], "access_token"}
   # Connects to connect user (if it exists - need to create user first) and returns user balance info
   def get(self, user):
       userData = User.get(User.username == user)
       userData = model_to_dict(userData)
       access_token = userData['accessToken']
       #print(access_token)
       client = Client(client_id=id, secret=secret, access_token=access_token)
       balance = client.balance().json()
       return balance

@api.resource('/users/<user>/transactions')
class api_transactions(Resource):
   # params: None
   # returns: Json data - user transaction info {"accounts"[...], "transactions"[...]}
   # Connects to connect user (if it exists - need to create user first) and returns user info
   def get(self, user):
       userData = User.get(User.username == user)
       userData = model_to_dict(userData)
       access_token = userData['accessToken']
       #print(access_token)
       client = Client(client_id=id, secret=secret, access_token=access_token)
       transactions = client.connect_get().json()
       return transactions

@api.resource('/institutions')
class api_institutions(Resource):
   # params: None
   # returns: Json data - institution info {"accesstoken", "id", "username"}
   # Connects to plaid api and returns institution info
   def get(self):
       institutions = client.institutions().json()
       return institutions

#institutions = client.institutions().json()
#print(institutions)

#categories = client.categories().json()
#print(categories)

#client = Client(client_id=id, secret=secret, access_token=access_token)
#response = client.upgrade("auth")

#accounts = client.auth_get().json()
#print(accounts)

#balance = client.balance()
#print(balance)

#response = client.connect_get()
#transactions = response.json()
#print(transactions)

#response = client.info_get()
#info = response.json()
#print(info)

if __name__ == '__main__':
    webapp.run(debug=True)