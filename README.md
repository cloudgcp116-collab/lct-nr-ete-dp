# Insurance Dynamic Dataproc Pipeline (Cloud Composer)

A config-driven Airflow DAG that dynamically provisions **ephemeral Dataproc
clusters** and runs a PySpark ETL job per insurance entity (`customer`,
`claims`, `policy`, `billing`) - with **zero DAG code changes needed** to add
a new entity.

![Architecture](architecture.png)

## How it works

1. **`configs/*.json`** describes each entity: source/target tables, which
   job script and SQL file to use, cluster sizing, and validation thresholds.
2. **`dags/config_loader.py`** loads and validates those configs (GCS first,
   local fallback) at DAG-parse time.
3. **`dags/cluster_factory.py`** and **`dags/job_factory.py`** translate each
   config into a Dataproc cluster spec and a PySpark job spec.
4. **`dags/insurance_dynamic_dag.py`** loops over the loaded configs and
   builds one `TaskGroup` per entity:

   ```
   create_cluster_<entity> >> submit_job_<entity> >> validate_<entity> >> delete_cluster_<entity>
   ```

   Entities run **in parallel**, each on its own short-lived cluster that is
   always torn down (`trigger_rule="all_done"`), even if the job fails.
5. **`jobs/<entity>_etl.py`** are plain PySpark scripts (no Airflow
   dependency) that read from BigQuery, apply `sql/<entity>.sql` (where
   present), and write the curated result back to BigQuery.
6. **`utils/notifications.py`** posts Slack alerts on DAG success/failure;
   **`utils/validation.py`** runs a post-load row-count check before the
   cluster is deleted.

### Adding a new entity

Drop in `configs/<name>.json` + `jobs/<name>_etl.py` (+ optional
`sql/<name>.sql`), add `<name>` to `ENTITIES` in `dags/constants.py` -
done. No changes to `insurance_dynamic_dag.py` required.

## Repository layout

```
dags/            Airflow DAG + factories (cluster/job) + config loader
configs/         Per-entity JSON configs (source/target tables, cluster sizing)
jobs/            Standalone PySpark ETL scripts, one per entity
utils/           Shared code: BigQuery/GCS helpers, logging, Slack alerts, validation
                 (zipped as utils.zip and shipped to the Dataproc cluster)
sql/             SQL transforms used by the PySpark jobs (customer/claims/policy)
terraform/       Composer environment, Dataproc autoscaling policy, IAM
```

## Deployment

1. **Sync the whole project root** (not just `dags/`) to the Composer
   environment's DAGs GCS bucket, preserving structure:
   ```
   gsutil -m rsync -r . gs://<composer-bucket>/dags/
   ```
   Composer recursively scans the DAGs bucket and adds its root to
   `sys.path`, which is what makes `from dags import constants` and
   `from utils.notifications import ...` resolve inside
   `insurance_dynamic_dag.py`.

2. **Ship the runtime artifacts** the Dataproc clusters read at job-submit
   time to the *dataproc* bucket (`terraform/composer.tf` ->
   `google_storage_bucket.dataproc_bucket`):
   ```
   gsutil cp configs/*.json gs://<dataproc-bucket>/configs/
   gsutil cp jobs/*.py      gs://<dataproc-bucket>/jobs/
   gsutil cp sql/*.sql      gs://<dataproc-bucket>/sql/
   (cd utils && zip -r ../jobs/utils.zip .) && gsutil cp jobs/utils.zip gs://<dataproc-bucket>/jobs/utils.zip
   ```

3. **Set Airflow Variables** (or rely on the defaults baked into
   `dags/constants.py`):

   | Variable | Purpose |
   |---|---|
   | `gcp_project_id` | Target GCP project |
   | `gcp_region` / `gcp_zone` | Dataproc region/zone |
   | `gcs_bucket` | The dataproc bucket from step 2 |
   | `dataproc_service_account` | SA the ephemeral clusters run as |
   | `alert_emails` | Comma-separated failure-notification recipients |

4. **Provision infra with Terraform**:
   ```
   cd terraform
   terraform init
   terraform apply -var="project_id=<PROJECT>" -var="dataproc_bucket_name=<BUCKET>"
   ```

## Requirements

See `requirements.txt` - install these as PyPI packages on the Composer
environment (they are not needed on the Dataproc image, which already ships
PySpark and the BigQuery connector).

## Notes

- Cluster names are deterministic per entity + execution date
  (`dp-<entity>-<ds_nodash>`), so backfills and retries never collide.
- `billing` has no `sql/billing.sql` by design - its aggregation is simple
  enough to express directly with the DataFrame API in `billing_etl.py`.
- Validation queries run from Airflow via the BigQuery client (cheap),
  rather than re-using Spark, to avoid paying for a second Spark job just
  to `COUNT(*)`.
