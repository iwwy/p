"""Settings
"""

import os.path

ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
PYRATEMP_PATH = ROOT_PATH + "/templates/"
STATIC_PATH = ROOT_PATH + "/static/"
STATIC_URL = "/static/"
SQLITE_DBNAME = ROOT_PATH + "/data.db"
SESSION_LENGTH = 60 * 60 * 24 * 14  # 14 days
