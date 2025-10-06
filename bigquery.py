from google.cloud import bigquery_storage_v1
from google.cloud.bigquery_storage_v1 import types, writer
from google.protobuf import descriptor_pb2
from google.oauth2 import service_account
import logging
import requests
import json
import pushup_session_data_pb2
from google.cloud import bigquery

#pushup-account@pushup-counter-aut.iam.gserviceaccount.com

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

creds = service_account.Credentials.from_service_account_file(
    "pushup-counter-aut-ac7461b01fea.json"
)
credentials_path = "pushup-counter-aut-ac7461b01fea.json"
credentials = service_account.Credentials.from_service_account_file(credentials_path)

def create_row_data(data):
    row = pushup_session_data_pb2.PushupSessionData()

    for field in TABLE_COLUMNS_TO_CHECK:
        if field in data:
            setattr(row, field, data[field])
    return row.SerializeToString()

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

    def send(self, data): # data is in json format
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        request_body = {
            "rows": [ {"json": row} for row in data ]
        }
        
        try:
            self.api_endpoint = f"https://bigquery.googleapis.com/bigquery/v2/projects/{self.project_id}/datasets/{self.dataset_id}/tables/{self.table_id}/_insertAll" # Example for legacy insertAll
            response = requests.post(self.api_endpoint, headers = headers, data = json.dumps(request_body))
            response.raise_for_status()

            print("Data successfully sent to BigQuery!")
        except:
            print(f"Error sending data to BigQuery: {e}!")
            if response:
                print(f"Response content: {response.text}")

    def storage_write(self, data):
        write_client = bigquery_storage_v1.BigQueryWriteClient(credentials=creds)
        parent = write_client.table_path(self.project_id, self.dataset_id, self.table_id)
        stream_name = f"{parent}/_default"
        write_stream = types.WriteStream()

        request_template = types.AppendRowsRequest()
        request_template.write_stream = stream_name

        proto_schema = types.ProtoSchema()
        proto_descriptor = descriptor_pb2.DescriptorProto()
        pushup_session_data_pb2.PushupSessionData.DESCRIPTOR.CopyToProto(proto_descriptor)
        proto_schema.proto_descriptor = proto_descriptor
        proto_data = types.AppendRowsRequest.ProtoData()
        proto_data.writer_schema = proto_schema
        request_template.proto_rows = proto_data

        append_rows_stream = writer.AppendRowsStream(write_client, request_template)

        proto_rows = types.ProtoRows()
        for row in data:
            proto_rows.serialized_rows.append(create_row_data(row))

        request = types.AppendRowsRequest()
        proto_data = types.AppendRowsRequest.ProtoData()
        proto_data.rows = proto_rows
        request.proto_rows = proto_data

        append_rows_stream.send(request)

        print(f"Rows to table: {parent} have been written.")

    def test(self):
        print("Test Big Query")