import requests
import json
import os
from dotenv import load_dotenv


def get_ngrok_url(api_endpoint_url):
    """
    Retrieves the public URL and port from the ngrok API.

    Args:
        api_endpoint_url (str): The ngrok API endpoint URL.

    Returns:
        tuple: A tuple containing the host and port, or (None, None) on error.
    """
    try:
        response = requests.get(api_endpoint_url)
        if response.status_code != 200:
            print(f"Error fetching ngrok URL: HTTP {response.status_code}")
            return None, None
        tunnels = json.loads(response.text)["tunnels"]
        for tunnel in tunnels:
            if tunnel["proto"] == "tcp":
                return tunnel["public_url"].replace("tcp://", "").split(":")
    except requests.exceptions.RequestException as e:
        print(f"Network error occurred: {e}")
        return None, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None


def update_cloudflare_dns(
        api_token, zone_id, record_id, name, content, service, proto, ttl=60
):
    """
    Updates a Cloudflare DNS record with the provided details.

    Args:
        api_token (str): The API token for Cloudflare authentication.
        zone_id (str): The Zone ID of the DNS record in Cloudflare.
        record_id (str): The Record ID of the DNS entry to be updated.
        name (str): The name of the DNS record.
        content (str): The content of the DNS record (typically the address).
        service (str): The service name for the SRV record.
        proto (str): The protocol for the SRV record.
        ttl (int): The time to live for the DNS record. Default is 60 seconds.

    Returns:
        dict: The response from Cloudflare API as a dictionary.
    """
    url = (
        f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
    )
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    data = {
        "type": "SRV",
        "name": name,
        "content": content,
        "data": {
            "service": service,
            "proto": proto,
            "name": name,
            "priority": 0,
            "weight": 0,
            "port": int(content.split(":")[1]),
            "target": content.split(":")[0],
        },
        "ttl": ttl,
    }
    try:
        response = requests.put(url, headers=headers, json=data)
        if response.status_code != 200:
            print(f"Error updating Cloudflare DNS: HTTP {response.status_code}")
            print(response.json())
            return None
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Network error occurred: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


if __name__ == "__main__":
    """
    Main script execution:
    - Loads environment variables
    - Retrieves the ngrok URL and port
    - Updates the Cloudflare DNS record with the ngrok details
    """
    load_dotenv(override=True)

    cf_api_token = os.getenv("CLOUDFLARE_API_TOKEN")
    cf_zone_id = os.getenv("CLOUDFLARE_ZONE_ID")
    cf_record_id = os.getenv("CLOUDFLARE_RECORD_ID")
    ngrok_endpoint = os.getenv("NGROK_API_ENDPOINT")
    cf_record_name = os.getenv("CLOUDFLARE_RECORD_NAME", "default_record_name")
    cloudflare_service_name = os.getenv("CLOUDFLARE_SERVICE_NAME", "_minecraft")

    if not all([cf_api_token, cf_zone_id, cf_record_id, ngrok_endpoint]):
        print("Missing one or more required environment variables.")
        exit(1)

    ngrok_host, ngrok_port = get_ngrok_url(ngrok_endpoint)
    if ngrok_host and ngrok_port:
        print(f"Ngrok Host: {ngrok_host}, Port: {ngrok_port}")
        update_response = update_cloudflare_dns(
            cf_api_token,
            cf_zone_id,
            cf_record_id,
            cf_record_name,
            f"{ngrok_host}:{ngrok_port}",
            cloudflare_service_name,
            "_tcp",
        )
        print(json.dumps(update_response, indent=4))
    else:
        print("Failed to retrieve ngrok URL and port.")

