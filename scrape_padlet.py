import argparse
import re
import requests
from urllib.parse import urljoin
from collections import defaultdict
import sys
import json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    args = ap.parse_args()

    start_html = requests.get(args.url).text
    starting_state_url = (
        urljoin(args.url, re.search("[^\"]+/padlet_starting_state?[^\"]+", start_html).group()))
    starting_state = requests.get(starting_state_url).json()
    wall_id = starting_state["wall"]["id"]
    data_urls = {name: f"https://api.padlet.com/api/5/{name}?wall_id={wall_id}"
                 for name in ["reactions", "comments", "wishes"]}

    data = {name: requests.get(url).json() for name, url in data_urls.items()}
    if any(collection["meta"]["next"] for collection in data.values()):
        return RuntimeError("data pagination not currently handled")
    wishes = [obj["attributes"] for obj in data.pop("wishes")["data"]]
    wishes.sort(key=lambda wish: wish["sort_index"], reverse=True)
    starting_state["wishes"] = wishes

    grouped_by_wish = defaultdict(lambda: defaultdict(list))
    types = set()
    for collection in data.values():
        for obj in collection["data"]:
            type_ = obj["type"]
            if type_ == "reaction":
                type_ = obj["attributes"]["reaction_type"]
            types.add(type_)

            wish_id = obj["attributes"]["wish_id"]
            grouped_by_wish[wish_id][type_].append(obj["attributes"])

    for wish in starting_state["wishes"]:
        annotations = wish["annotations"] = {}
        for type_ in types:
            annotations[type_] = grouped_by_wish[wish["id"]][type_]

    json.dump(starting_state, sys.stdout)


if __name__ == '__main__':
    main()
