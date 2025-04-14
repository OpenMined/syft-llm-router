import json
from pathlib import Path

from syft_core import Client

LLM_ROUTE_INDEX_FILENAME = "index.html"


def discover():
    """Discover all the llm_routers in the syft network
    and creates/updates a common index file"""

    client = Client.load()

    # Get all the datasites
    datasites = client.datasites

    # LLM Router from each datasite
    # datasite_name/public/llm_routers
    # Get all the llm_routers
    llm_index = []
    # Get all the llm_routers
    for datasite in datasites.glob("*"):
        llm_routers = datasite / "public" / "llm_routers"
        if not llm_routers.exists():
            continue
        for router in llm_routers.glob("*"):
            if not (router.exists() and router.is_dir()):
                continue

            metadata_path = router / "metadata.json"
            llm_index.append(
                {
                    "datasite": datasite.name,
                    "router": router.name,
                    "metadata": json.loads(metadata_path.read_text()),
                    "my_model": datasite.name == client.my_datasite.name,
                }
            )

    # Create the directory if it doesn't exist
    my_datasite = client.my_datasite
    html_dir = my_datasite / "public" / "llm_routers"
    html_dir.mkdir(parents=True, exist_ok=True)

    # Read the template HTML file
    current_dir = Path(__file__).parent
    template_path = current_dir / LLM_ROUTE_INDEX_FILENAME
    html_template = template_path.read_text()

    # Replace the template variable with the actual JSON data
    json_data = json.dumps(llm_index)
    html_content = html_template.replace("/*__ROUTER_DATA__*/[]", json_data)

    # Write the final HTML with injected data
    html_path = html_dir / LLM_ROUTE_INDEX_FILENAME
    html_path.write_text(html_content)


if __name__ == "__main__":
    discover()
