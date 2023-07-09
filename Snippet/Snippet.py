import json
import csv
import requests

cu_url = 'https://krjbj95w08.execute-api.us-east-2.amazonaws.com/dev/create_user'
ut_url = 'https://krjbj95w08.execute-api.us-east-2.amazonaws.com/dev/upload_transactions'
ft_url = 'https://krjbj95w08.execute-api.us-east-2.amazonaws.com/dev/fetch_transactions'


cu_payload = {
    "Email": "raul.sosa.cortes@gmail.com",
    "Name": "raul"
}

response = requests.post(cu_url, json=cu_payload)
if(response.status_code==200):
    result = json.loads(response.text)
    client_id = result["id"]

    with open("transactions.csv", 'r') as file:
        csvreader = csv.reader(file)
        header = next(csvreader)
        for row in csvreader:
            ut_payload = {
                "Date": row[0],
                "Client_ID": client_id, # Uses Client ID instead of the one in the CSV
                "Transaction": row[2],
                "Amount": float(row[3])
            }

            ut_response = requests.post(ut_url, json=ut_payload)

    ft_payload={
      "Client_ID": client_id # Sends Mail to the Client We Updated
    }
    ft_response = requests.post(ft_url, json=ft_payload)
