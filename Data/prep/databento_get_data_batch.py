import os
import databento as db
import json

def load_key():
    key = os.getenv("DATABENTO_API_KEY")
    if not key:
        from dotenv import load_dotenv, find_dotenv
        load_dotenv(find_dotenv(), override=True)
        key = os.getenv("DATABENTO_API_KEY")
    if not key:
        raise RuntimeError("DATABENTO_API_KEY missing.")
    return key


def cost_estimate():
    client = db.Historical()
    
    cost = client.metadata.get_cost(
        dataset="GLBX.MDP3",
        symbols=["YM.FUT"],
        schema="ohlcv-1m",
        start="2010-06-06T00:00:00",
        end="2025-11-18T00:00:00",
        stype_in="parent",
    )
    print(cost)

def batch_request():
    client = db.Historical()

    details = client.batch.submit_job(
        dataset="GLBX.MDP3",
        symbols=["NQ.FUT"],
        schema="ohlcv-1m",
        encoding="csv",
        start="2025-06-04T00:00:00",
        end="2025-11-18T00:00:00",
        stype_in="parent",
        split_duration="none", # Returns a single file instead of daily splits
        pretty_px=True,  # Format prices as decimals
        pretty_ts=True,  # Format timestamps as ISO 8601
        map_symbols=True,  # Include symbol column in output
    )
    print(details)

def list_jobs():
    client = db.Historical()

    jobs = client.batch.list_jobs(
        states=["queued", "processing", "done"],
        since="2025-11-01",
    )
    with open('list_jobs.json', 'w') as f:
        json.dump(jobs, f, indent=2)

    print(f"Saved jobs list to list_jobs.json")

def download_job():
    client = db.Historical()
    
    # Download all files for the batch job
    client.batch.download(
        job_id="GLBX-20251121-LW69NAX5TA",
        output_dir="/Users/blakerodenbeck/Projects/Data/raw/",
    )

def list_files():
    client = db.Historical()

    files = client.batch.list_files(job_id="GLBX-20251118-46B3WSW6JX")
    # Save to JSON file
    with open("batch_files.json", "w") as f:
        json.dump(files, f, indent=2)
    
    print(f"Saved files list to batch_files.json")

def download_specific_file():
    client = db.Historical()

    # Alternatively, you can download a specific file
    client.batch.download(
        job_id="GLBX-20251119-V5HTPMLHT5",
        output_dir="/Users/blakerodenbeck/Projects/Data/raw/GLBX-20251119-V5HTPMLHT5/",
        filename_to_download="glbx-mdp3-20250803.ohlcv-1m.csv.zst",
    )

if __name__ == "__main__":
    load_key()
    #cost_estimate()
    #batch_request()
    #list_jobs()
    download_job()
    #list_files()
    #download_specific_file()