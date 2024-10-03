# %%
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import time
import yaml
import csv
import tkinter as tk
from tkinter import filedialog


def fetch_changesets(username, days=10):
    """Fetch changesets for a user within the last 'days' days."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    time_param = f"{start_date.strftime('%Y-%m-%dT%H:%M:%SZ')},{end_date.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    url = "https://api.openstreetmap.org/api/0.6/changesets"
    params = {
        "display_name": username,
        "time": time_param,
    }
    response = requests.get(url, params=params)
    time.sleep(1)  # Respect API rate limits
    if response.status_code != 200:
        print(f"Error fetching changesets for {username}: {response.status_code}")
        return []
    changesets = []
    root = ET.fromstring(response.content)
    for cs in root.findall("changeset"):
        cs_id = cs.attrib["id"]
        created_at = datetime.strptime(cs.attrib["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        changesets.append(
            {
                "id": cs_id,
                "created_at": created_at,
            }
        )
    return changesets


def group_changesets(changesets):
    """Group changesets by day and time proximity."""
    from collections import defaultdict

    # Group by date
    day_groups = defaultdict(list)
    for cs in changesets:
        day = cs["created_at"].date()
        day_groups[day].append(cs)
    # Filter days with more than one changeset
    day_groups = {
        day: cs_list for day, cs_list in day_groups.items() if len(cs_list) > 1
    }
    # Group changesets within one hour of each other
    grouped_changesets = []
    for day, cs_list in day_groups.items():
        cs_list.sort(key=lambda x: x["created_at"])
        group = [cs_list[0]]
        for cs in cs_list[1:]:
            if (cs["created_at"] - group[-1]["created_at"]).total_seconds() <= 3600:
                group.append(cs)
            else:
                if len(group) > 1:
                    grouped_changesets.append(group)
                group = [cs]
        if len(group) > 1:
            grouped_changesets.append(group)
    return grouped_changesets


def fetch_changeset_diff(cs_id):
    """Fetch changeset diff and count added nodes and ways."""
    url = f"https://api.openstreetmap.org/api/0.6/changeset/{cs_id}/download"
    response = requests.get(url)
    time.sleep(1)  # Respect API rate limits
    if response.status_code != 200:
        print(f"Error fetching changeset {cs_id}: {response.status_code}")
        return 0, 0
    root = ET.fromstring(response.content)
    nodes_added = 0
    ways_added = 0
    for action in root:
        if action.tag == "create":
            for element in action:
                if element.tag == "node":
                    nodes_added += 1
                elif element.tag == "way":
                    ways_added += 1
    return nodes_added, ways_added


def calculate_rates(grouped_changesets):
    """Calculate rates for each group of changesets."""
    weighted_rates = []
    period_total_hours = 0
    for group in grouped_changesets:
        start_time = group[0]["created_at"]
        end_time = group[-1]["created_at"]
        total_seconds = (end_time - start_time).total_seconds()
        total_hours = (
            total_seconds / 3600 if total_seconds > 0 else 0.0001
        )  # Avoid division by zero
        total_nodes = 0
        total_ways = 0
        for cs in group:
            cs_id = cs["id"]
            nodes_added, ways_added = fetch_changeset_diff(cs_id)
            total_nodes += nodes_added
            total_ways += ways_added

        rate_nodes = total_nodes / total_hours if total_hours > 0 else 0
        rate_ways = total_ways / total_hours if total_hours > 0 else 0
        period_total_hours += total_hours
        weighted_rates.append(
            {
                "group_hours": total_hours,
                "group_node_rate": rate_nodes,
                "group_way_rate": rate_ways,
            }
        )

    # Calculate weighted rates
    weighted_node_rate = 0
    weighted_way_rate = 0
    if period_total_hours > 0:
        for rate in weighted_rates:
            weight = rate["group_hours"] / period_total_hours
            weighted_node_rate += weight * rate["group_node_rate"]
            weighted_way_rate += weight * rate["group_way_rate"]
    return weighted_node_rate, weighted_way_rate


def process_users(yaml_file):
    """Process users from YAML file and generate CSV report."""
    with open(yaml_file, "r") as file:
        data = yaml.safe_load(file)

    results = []
    missing_users = []  # Initialize the missing users list
    users = data.get("users", [])
    default_days = data.get("default_days", 10)

    for entry in users:
        username = entry.get("username")
        days = entry.get("days", default_days)
        print(f"Processing user: {username} for the past {days} days")
        try:
            changesets = fetch_changesets(username, days)
            if not changesets:
                print(f"No changesets found for user {username}.")
                missing_users.append(username)  # Append to missing_users
                continue
            grouped_changesets = group_changesets(changesets)
            if not grouped_changesets:
                print(
                    f"No days with multiple changesets within one hour found for user {username}."
                )
                missing_users.append(username)  # Append to missing_users
                continue
            weighted_node_rate, weighted_way_rate = calculate_rates(grouped_changesets)
            results.append(
                {
                    "username": username,
                    "weighted_node_rate": round(weighted_node_rate, 2),
                    "weighted_way_rate": round(weighted_way_rate, 2),
                }
            )
        except Exception as e:
            print(f"An error occurred while processing user {username}: {e}")
            missing_users.append(username)  # Append to missing_users in case of error

    if results:
        # Determine the number of days for the report filename
        report_days = max([entry.get("days", default_days) for entry in users])
        # Write results to CSV
        current_date = datetime.now().strftime("%Y%m%d")
        csv_filename = f"OSM_Rates_{current_date}_{report_days}days.csv"
        with open(csv_filename, "w", newline="") as csvfile:
            fieldnames = ["username", "weighted_node_rate", "weighted_way_rate"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in results:
                writer.writerow(row)
        print(f"Report saved to {csv_filename}")
    else:
        print("No data to write to CSV.")

    # Handle missing users
    if missing_users:
        print("\nThe following users did not produce any results:")
        for user in missing_users:
            print(f" - {user}")
        # Optionally, write missing users to a separate CSV file
        missing_csv_filename = f"OSM_MissingUsers_{current_date}_{report_days}days.csv"
        with open(missing_csv_filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["username"])
            for user in missing_users:
                writer.writerow([user])
        print(f"Missing users saved to {missing_csv_filename}")


if __name__ == "__main__":
    # Initialize Tkinter and open file dialog
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    yaml_file = filedialog.askopenfilename(
        title="Select YAML File",
        filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")],
    )
    if yaml_file:
        process_users(yaml_file)
    else:
        print("No YAML file selected.")

# %%
