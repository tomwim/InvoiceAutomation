from datetime import datetime, timedelta, timezone

from common.utils.base_service import BaseService
from .receipt import AnalyzedReceipt

from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas

# Wrapper for azure credentials
class AzureCredentials():
    def __init__(self, container_name : str, account_name : str, endpoint : str, key : str):
        self.endpoint = endpoint
        self.key = key
        self.container_name = container_name
        self.account_name = account_name

# Handles the azure user delegation key for the blob service client. Checks if key is valid and refreshes it.
class DelegationKeyHandler():
    def __init__(self, service_client : BlobServiceClient, life_time : int = 60, refresh_margin_time = 5):
        self._start_time = None
        self._life_time = life_time
        self._refresh_margin_time = refresh_margin_time
        self._service_client = service_client
        self._user_delegation_key = None

    def get_key(self):
        return self._user_delegation_key

    def is_key_valid(self):
        if self._user_delegation_key == None or self._start_time == None:
            return False
        
        refresh_margin = timedelta(minutes=self._refresh_margin_time)
        return datetime.now(timezone.utc) + refresh_margin < self._start_time + timedelta(minutes=self._life_time)

    def refresh_key(self):
        self._user_delegation_key = self.create_key()

    def create_key(self):
        self._start_time = datetime.now(timezone.utc)
        return self._service_client.get_user_delegation_key(self._start_time, self._start_time + timedelta(minutes=self._life_time))

# Creates a new blob service client
def create_blob_client(credential : DefaultAzureCredential, account_name : str):
    # Create a BlobServiceClient
    return BlobServiceClient(
        f"https://{account_name}.blob.core.windows.net",
        credential=credential
    )

# Creates a new sas blob token
def create_sas_token(account_name : str, container_name : str, blob_name : str, user_delegation_key, validation_time : int = 60):
    return generate_blob_sas(
        account_name=account_name,
        container_name=container_name,
        blob_name=blob_name,
        user_delegation_key=user_delegation_key,
        permission=BlobSasPermissions(read=True, list=True), # only allow reading
        expiry=datetime.now(timezone.utc) + timedelta(minutes=validation_time)
    )

# Extracts the file name in the blob url from the account and container.
def extract_file_name_from_blob_url(account_name : str, container_name : str, blob_url : str):
    return blob_url.removeprefix(f"https://{account_name}.blob.core.windows.net/{container_name}/")

class ReceiptReader(BaseService):
    def __init__(self, dispatcher, credentials : AzureCredentials):
        super().__init__(dispatcher=dispatcher)
        self._credentials = credentials

        azure_credential = DefaultAzureCredential()

        self._blob_client = create_blob_client(credential=azure_credential, account_name=credentials.account_name)
        self._delegation_key_handler = DelegationKeyHandler(service_client=self._blob_client)
        self._client = DocumentIntelligenceClient(endpoint=credentials.endpoint, credential=AzureKeyCredential(key=credentials.key))

    def get_result_event_name(self) -> str:
        return "ai_receipt_reader"
    
    async def execute(self, service_id, file_url : str):
        await self._analyze_receipt(service_id, file_url)

    async def _analyze_receipt(self, service_id, file_url : str):
        print(f"Analyze: {file_url}", flush=True)

        if self._delegation_key_handler.is_key_valid() == False:
            self._delegation_key_handler.refresh_key()

        sas_token = create_sas_token(
            account_name=self._credentials.account_name, 
            container_name=self._credentials.container_name, 
            blob_name=extract_file_name_from_blob_url(
                account_name=self._credentials.account_name, 
                container_name=self._credentials.container_name,
                blob_url=file_url),
            user_delegation_key=self._delegation_key_handler.get_key()
        )

        poller = await self._client.begin_analyze_document(
            "prebuilt-receipt", 
            {
                "urlSource": f"{file_url}?{sas_token}"
            }
        )

        result = await poller.result()


        for document in result.documents:
            print(f"Receipt type: {document.doc_type}", flush=True)
            print(f"Document: {document}", flush=True)
            print(f"{document.fields}", flush=True)

            for field_name, field in document.fields.items():
                print(f"{field_name} -> {field}", flush=True)

        await self.dispatcher.publish(self.get_result_event_name(), 
            {
                "service_id" : service_id,
                "result" : result
            })
            # for field_name, field_value in document.fields.items():
            #     print(f"{field_name}: {field_value.value} (confidence: {field_value.confidence})", flush=True)
                

        

    

    
