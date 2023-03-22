###
# Copyright 2013-2023 AFI, Inc. All Rights Reserved.
###

DUCKDB_SCHEMA = {
    "id": "VARCHAR",
    "type": "VARCHAR",
    "actor": "STRUCT(id INTEGER, login VARCHAR, display_login VARCHAR, gravatar_id VARCHAR, url VARCHAR, avatar_url VARCHAR)",
    "repo": "STRUCT(id INTEGER, name VARCHAR, url VARCHAR)",
    "created_at": "VARCHAR",
    "org": "STRUCT(id INTEGER, login VARCHAR, gravatar_id VARCHAR, url VARCHAR, avatar_url VARCHAR)",
}
