from flask import request, jsonify, Blueprint
recommend = Blueprint('recommend', __name__)


@recommend.route("/", methods=['GET'])
def main_route():
    return 'OK'