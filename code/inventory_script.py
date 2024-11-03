"""
Ansible Dynamic Inventory Generator

This script generates a dynamic Ansible inventory from an Excel file containing
host details. The inventory is formatted as a JSON object compatible with Ansible,
allowing for flexible grouping and filtering based on specified criteria.

Modules:
    - pandas: for reading and processing Excel data.
    - json: for formatting the output as JSON for Ansible compatibility.
    - os: for accessing environment variables to filter inventory generation.

Functions:
    - load_data: Reads the Excel file, processes the data into a structured format,
      and splits any notes into lists based on a ";" delimiter.
    - generate_inventory: Constructs an inventory grouped by "Server Environment" 
      and "Server Type" fields, applying filters if specified via environment variables. 
      Each host entry includes metadata like the ansible_host (hostname), notes, 
      server environment, server type, and Ansible user.

Usage:
    - This script can be run as a standalone executable to print the inventory in JSON format.
    - To filter the inventory by "Server Environment" and/or "Server Type", set the 
      environment variables `SERVER_ENVIRONMENT` and `SERVER_TYPE` before executing the script.

Example Command:
    SERVER_ENVIRONMENT="Production" SERVER_TYPE="Database" ./inventory_script.py

Ensure that each "Host Name" in the Excel file has a corresponding entry in the 
~/.ssh/config file for Ansible SSH connectivity.
"""

import pandas as pd
import json
import os

# Load data from Excel file
def load_data(filename="hosts_data.xlsx"):
    # Read the Excel file
    df = pd.read_excel(filename)

    # Convert the DataFrame to a list of dictionaries
    hosts_data = df.to_dict(orient="records")

    # Process notes: split each note by the delimiter ";" if multiple notes are present
    for host in hosts_data:
        host["Notes"] = host["Notes"].split(";") if isinstance(host["Notes"], str) else []

    return hosts_data

# Function to build inventory with secondary grouping by server type
def generate_inventory(hosts_data, server_environment=None, server_type=None):
    inventory = {"_meta": {"hostvars": {}}}

    # Filter hosts based on provided criteria
    filtered_hosts = [
        host for host in hosts_data
        if (server_environment is None or host["Server Environment"] == server_environment) and
           (server_type is None or host["Server Type"] == server_type)
    ]
    
    # Group hosts by Server Environment and Server Type
    for host in filtered_hosts:
        environment_group = host["Server Environment"]
        type_group = host["Server Type"]
        hostname = host["Host Name"]

        # Add host to the Server Environment group
        if environment_group not in inventory:
            inventory[environment_group] = {"hosts": []}
        inventory[environment_group]["hosts"].append(hostname)

        # Add host to the Server Type group
        if type_group not in inventory:
            inventory[type_group] = {"hosts": []}
        inventory[type_group]["hosts"].append(hostname)

        # Set host variables using the Host Name for SSH connection
        inventory["_meta"]["hostvars"][hostname] = {
            "ansible_host": hostname,  # Uses Host Name for SSH connection
            "notes": host.get("Notes", []),
            "server_environment": environment_group,
            "server_type": type_group,
            "ansible_user": host["Ansible User"]
        }

    return inventory

# Main function to print inventory in JSON format
if __name__ == "__main__":
    # Read filter values from environment variables
    server_environment = os.getenv("SERVER_ENVIRONMENT")
    server_type = os.getenv("SERVER_TYPE")

    # Load data and generate inventory based on the provided filters
    hosts_data = load_data()
    inventory = generate_inventory(hosts_data, server_environment, server_type)
    print(json.dumps(inventory, indent=2))