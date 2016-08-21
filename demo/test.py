from flask import Flask,request,json, jsonify
from flask_restful import Api, Resource
from plaid import Client
from plaid import errors as plaid_errors
from plaid.utils import json
from peewee import *


webapp = Flask(__name__)
api = Api(webapp)


# Base model class, created to cause other models to automatically be stored in called database
class BaseModel(Model):
    class Meta:
        database = database

# the user model specifies its fields (or columns) declaratively, like django
class User(BaseModel):
    username = CharField(unique=True)
    password = CharField()
    accessToken = CharField()

    class Meta:
        order_by = ('username',)

# the user model specifies its fields (or columns) declaratively, like django
class Credentials(BaseModel):
    id = CharField(unique=True)
    secret = CharField()

    class Meta:
        order_by = ('id',)

def answer_mfa(data):
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


Client.config({
    'url': 'https://tartan.plaid.com'
})


def answer_question(questions):
    # We have magically inferred the answer
    # so we respond immediately
    # In the real world, we would present questions[0]
    # to our user and submit their response
    answer = 'dogs'
    return client.connect_step(account_type, answer)


def answer_list(devices):
    # You should specify the device to which the passcode is sent.
    # The available devices are present in the devices list
    code = input("Enter code: ")
    return client.connect_step('chase', code, options={
        'send_method': {'type': 'email'}
    })


def answer_selections(selections):
    # We have magically inferred the answers
    # so we respond immediately
    # In the real world, we would present the selection
    # questions and choices to our user and submit their responses
    # in a JSON-encoded array with answers provided
    # in the same order as the given questions
    answer = json.dumps(['Yes', 'No'])
    return client.connect_step(account_type, answer)


@api.resource('/users/<user>')
class api_users(Resource):
    id = '57b4faff66710877408d0856'             # obtain id and secret from db, same for all queries
    secret = '45d1a44d9c7a4f3ede7d61bfc32630'
    client = Client(client_id=id, secret=secret)
    account_type = 'chase'


id = '57b4faff66710877408d0856'
secret = '45d1a44d9c7a4f3ede7d61bfc32630'
client = Client(client_id=id, secret=secret)
account_type = 'chase'

#endpoint: username, password

try:
    response = client.connect(account_type, {
        'username': 'tedwerbel0901',
        'password': '#Saverly7114#'
    })
except plaid_errors.UnauthorizedError:
    print("Password Error")
else:
    if response.status_code == 200:
        # User connected
        data = response.json()
        print(data)
        access_token = data['access_token']
        print(access_token)
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
            print(data)
            access_token = data['access_token']
            print(access_token)


institutions = client.institutions().json()
print(institutions)

categories = client.categories().json()
print(categories)

#client = Client(client_id=id, secret=secret, access_token=access_token)
#response = client.upgrade("auth")

#accounts = client.auth_get().json()
#print(accounts)

balance = client.balance()
print(balance)

response = client.connect_get()
transactions = response.json()
print(transactions)

#response = client.info_get()
#info = response.json()
#print(info)

if __name__ == '__main__':
    database = SqliteDatabase("test.db")
    webapp.run(debug=True)