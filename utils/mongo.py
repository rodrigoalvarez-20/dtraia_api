from pymongo import MongoClient

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