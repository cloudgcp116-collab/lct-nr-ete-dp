## Step 1. Enable APIs

Enable:

Cloud Functions
Cloud Scheduler
Cloud SQL Admin API
Cloud Build
Cloud IAM
Cloud Logging

## Step 2. Service Account Permissions

The Cloud Function service account needs:

Cloud SQL Admin

or the permissions

cloudsql.instances.get
cloudsql.instances.update

## Run following command
## gcloud command to deploy the cloud function from local machine
gcloud functions deploy crf-manage-cloudsql \
    --gen2 \
    --runtime python311 \
    --region asia-south1 \
    --entry-point manage_cloudsql_instance \
    --trigger-http \
    --allow-unauthenticated

## Cloud Scheduler Job (Morning)
Name:
start-cloudsql

Schedule:
0 8 * * *

Timezone:
Asia/Kolkata

Target:
HTTP

URL:
https://....cloudfunctions.net/manage_cloudsql?action=start

Method:
GET

## Cloud Scheduler Job (Night)
Name:
stop-cloudsql

Schedule:
0 22 * * *

Timezone:
Asia/Kolkata

Target:
HTTP

URL:
https://....cloudfunctions.net/manage_cloudsql?action=stop

Method:
GET
