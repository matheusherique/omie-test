from flask import Flask
from flask_restful import Api
from bill import Bill

app = Flask(__name__)
api = Api(app)

api.add_resource(Bill, '/nota_fiscal')

if __name__ == '__main__':
    app.run(debug=True)