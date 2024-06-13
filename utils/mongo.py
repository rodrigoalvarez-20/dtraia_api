"""
DTRAIA_API - Research Project
Script for the MongoDB client used in the API
Authors: Rodrigo Alvarez, Adrian Rodriguez, Uriel Perez
Created on: 2023 
"""

from pymongo import MongoClient

# Custom imports
from dtraia_api.utils.configs import get_mongo_creds

def get_mongo_conn_url():
    host, port = get_mongo_creds()
    con_str = "mongodb://{}:{}".format(host, port)
    return con_str

def get_mongo_connection():
    host, port = get_mongo_creds()
    con_str = "mongodb://{}:{}".format(host, port)
    return MongoClient(con_str)


if __name__ == "__main__":
    print(get_mongo_conn_url())