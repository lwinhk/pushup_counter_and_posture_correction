from google.oauth2 import service_account
from google.cloud import bigquery

TABLE_COLUMNS_TO_CHECK = [
    "id",
    "user_id",
    "counter",
    "incorrect_counter",
    "correct_counter",
    "timestamp",
    "incorrect_counter_perc",
    "correct_counter_perc",
    "created_at"
]

# this credentials JSON file cannot be put in GitHub repository.
# you will need to contact developer or create own GoogleCloud credentials and use it
credentials_path = "pushup-counter-aut-ac7461b01fea.json"
credentials = service_account.Credentials.from_service_account_file(credentials_path)

class BigQuery(object):
    project_id = ""
    dataset_id = ""
    table_id = ""
    access_token = ""
    api_endpoint = ""

    def __init__(self, project_id, dataset_id, table_id, access_token):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.access_token = access_token

    def simple_send(self, data):
        # Initialize the BigQuery client
        client = bigquery.Client(credentials=credentials, project=self.project_id)

        # Insert the row
        errors = client.insert_rows_json(f"{self.dataset_id}.{self.table_id}", [data])

        if errors:
            print(f"Encountered errors while inserting rows: {errors}")
        else:
            print("Row successfully inserted.")