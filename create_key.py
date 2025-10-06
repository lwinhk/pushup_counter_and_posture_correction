from google.cloud import iam_admin_v1
from google.cloud.iam_admin_v1 import types


def create_key(project_id: str, account: str) -> types.ServiceAccountKey:
    """
    Creates a key for a service account.

    project_id: ID or number of the Google Cloud project you want to use.
    account: ID or email which is unique identifier of the service account.
    """

    iam_admin_client = iam_admin_v1.IAMClient()
    request = types.CreateServiceAccountKeyRequest()
    request.name = f"projects/{project_id}/serviceAccounts/{account}"

    key = iam_admin_client.create_service_account_key(request=request)

    # The private_key_data field contains the stringified service account key
    # in JSON format. You cannot download it again later.
    # If you want to get the value, you can do it in a following way:
    # import json
    # json_key_data = json.loads(key.private_key_data)
    # key_id = json_key_data["private_key_id"]

    return key

create_key("pushup-counter-aut", "pushup_account")