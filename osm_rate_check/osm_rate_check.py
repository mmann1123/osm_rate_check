# %%
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import time


def fetch_changesets(username, days=10):
    """Fetch changesets for a user within the last 'days' days."""
    end_date = datetime.now()
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
        raise Exception(f"Error fetching changesets: {response.status_code}")
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
        raise Exception(f"Error fetching changeset {cs_id}: {response.status_code}")
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
    weighted_rates = {}
    period_total_hours = 0
    i = 0
    for group in grouped_changesets:
        start_time = group[0]["created_at"]
        end_time = group[-1]["created_at"]
        total_seconds = (end_time - start_time).total_seconds()
        total_hours = total_seconds / 3600
        total_nodes = 0
        total_ways = 0
        for cs in group:
            cs_id = cs["id"]
            nodes_added, ways_added = fetch_changeset_diff(cs_id)
            total_nodes += nodes_added
            total_ways += ways_added

        rate_nodes = total_nodes / total_hours if total_hours > 0 else 0
        rate_ways = total_ways / total_hours if total_hours > 0 else 0
        print(f"From {start_time} to {end_time} ({total_hours:.2f} hours):")
        print(f"  Nodes added: {total_nodes}, Rate: {rate_nodes:.2f} nodes/hour")
        print(f"  Ways added: {total_ways}, Rate: {rate_ways:.2f} ways/hour")
        print("-" * 50)
        # get stats for weighted rates
        period_total_hours += total_hours
        weighted_rates[i] = {
            "group_hours": total_hours,
            "group_node_rate": rate_nodes,
            "group_ways_rate": rate_ways,
        }
        i += 1

    # calculate weighted rates
    weighted_node_rate = 0
    for key, value in weighted_rates.items():
        weighted_node_rate += (value["group_hours"] / period_total_hours) * value[
            "group_node_rate"
        ]
    print("-" * 50, "\n", "-" * 50)
    print(f"Weighted node rate: {weighted_node_rate:.2f} nodes/hour")


def main():
    username = input("Enter the OSM username: ")
    print("Fetching changesets...")
    changesets = fetch_changesets(username)
    if not changesets:
        print("No changesets found for this user.")
        return
    print("Grouping changesets...")
    grouped_changesets = group_changesets(changesets)
    if not grouped_changesets:
        print("No days with multiple changesets within one hour found.")
        return
    print("Calculating rates...")
    calculate_rates(grouped_changesets)


# if __name__ == "__main__":
main()

# %%
