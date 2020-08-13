"""
TODO:
 -

Def conns:
 - kafka
 - dynamo
 - system

Alt conns:
 - salesforce
 - pagerduty
 - jira
"""
from omnibus import lang


class Connector(lang.Abstract):
    pass


class SqlConnector(Connector):
    """
    postgres/mysql/snowflake
    """


class FileConnector(Connector):
    """
    local/s3/sftp?
    csv/yaml/parquet
    """


class MongoConnector(Connector):
    pass