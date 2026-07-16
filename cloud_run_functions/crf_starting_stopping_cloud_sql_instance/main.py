import functions_framework
from googleapiclient.discovery import build
from flask import Request

PROJECT_ID = "lavuscloudtech-prod"
INSTANCE_ID = "lavuscloudtech-sql-server-asia"


@functions_framework.http
def manage_cloudsql_instance(request: Request):

    action = request.args.get("action")

    service = build("sqladmin", "v1beta4")

    body = {}

    if action == "start":
        body = {
            "settings": {
                "activationPolicy": "ALWAYS"
            }
        }

    elif action == "stop":
        body = {
            "settings": {
                "activationPolicy": "NEVER"
            }
        }

    else:
        return ("Invalid action", 400)

    request = service.instances().patch(
        project=PROJECT_ID,
        instance=INSTANCE_ID,
        body=body
    )

    response = request.execute()

    return response
