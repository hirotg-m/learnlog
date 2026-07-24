from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Any

import boto3
import pytest
from moto import mock_aws

from app.repositories.dynamodb_store import DynamoDBStore

# infra/dynamodb.yaml と同じテーブル名・キー・GSI 構成を再現する (docs/api-spec.md 10 章参照)
QUALIFICATIONS_TABLE = "learnlog-qualifications-test"
STUDY_LOGS_TABLE = "learnlog-study-logs-test"
MILESTONES_TABLE = "learnlog-milestones-test"
LOGIN_ATTEMPTS_TABLE = "learnlog-login-attempts-test"
SESSIONS_TABLE = "learnlog-sessions-test"


@pytest.fixture(autouse=True)
def aws_credentials() -> None:
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
    os.environ.setdefault("AWS_SECURITY_TOKEN", "testing")
    os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
    os.environ.setdefault("AWS_DEFAULT_REGION", "ap-northeast-1")


@pytest.fixture
def dynamodb_resource(aws_credentials: None) -> Iterator[Any]:
    with mock_aws():
        resource = boto3.resource("dynamodb", region_name="ap-northeast-1")
        _create_tables(resource)
        yield resource


def _create_tables(resource: Any) -> None:
    resource.create_table(
        TableName=QUALIFICATIONS_TABLE,
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
    )
    resource.create_table(
        TableName=STUDY_LOGS_TABLE,
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "qualificationId", "AttributeType": "S"},
            {"AttributeName": "date", "AttributeType": "S"},
            {"AttributeName": "month", "AttributeType": "S"},
        ],
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "ByQualification",
                "KeySchema": [
                    {"AttributeName": "qualificationId", "KeyType": "HASH"},
                    {"AttributeName": "date", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "ByMonth",
                "KeySchema": [
                    {"AttributeName": "month", "KeyType": "HASH"},
                    {"AttributeName": "date", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    resource.create_table(
        TableName=MILESTONES_TABLE,
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "qualificationId", "AttributeType": "S"},
        ],
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "ByQualification",
                "KeySchema": [{"AttributeName": "qualificationId", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    resource.create_table(
        TableName=LOGIN_ATTEMPTS_TABLE,
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
    )
    resource.create_table(
        TableName=SESSIONS_TABLE,
        AttributeDefinitions=[{"AttributeName": "token", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "token", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
    )


@pytest.fixture
def dynamodb_store(dynamodb_resource: Any) -> DynamoDBStore:
    return DynamoDBStore(
        qualifications_table=QUALIFICATIONS_TABLE,
        study_logs_table=STUDY_LOGS_TABLE,
        milestones_table=MILESTONES_TABLE,
        login_attempts_table=LOGIN_ATTEMPTS_TABLE,
        sessions_table=SESSIONS_TABLE,
        resource=dynamodb_resource,
    )
