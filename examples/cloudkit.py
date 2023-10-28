import sys 
sys.path.append(".")

import requests
import uuid
import plistlib
from base64 import b64encode, b64decode
import json
import random
import icloud.gsa as gsa
import icloud.cloudkit as cloudkit
import icloud

from rich.logging import RichHandler
import logging
logging.basicConfig(
    level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)

def main():
    CONFIG_PATH = "config/cloudkit.json"
    # See if we have a search party token saved
    import os
    if os.path.exists(CONFIG_PATH):
        logging.info("Using saved config...")
        #print("Found search party token!")
        with open(CONFIG_PATH, "r") as f:
            j = json.load(f)
            cloudkit_token = j["cloudkit_token"]
            ds_prs_id = j["ds_prs_id"]
            mme_token = j["mme_token"]
        
    else:
        # Prompt for username and password
        USERNAME = input("Username: ")
        PASSWORD = input("Password: ")

        r = icloud.login(USERNAME, PASSWORD, delegates=["com.apple.mobileme"])
        print(r)

        cloudkit_token = r['delegates']['com.apple.mobileme']['service-data']['tokens']['cloudKitToken']
        mme_token = r['delegates']['com.apple.mobileme']['service-data']['tokens']['mmeAuthToken']
        #ds_prs_id = r['delegates']['com.apple.mobileme']['service-data']['appleAccountInfo']['dsPrsID'] # This can also be obtained from the grandslam response
        ds_prs_id = r['dsid']

        logging.info("Logged in!")

        with open(CONFIG_PATH, "w") as f:
            json.dump({
                "cloudkit_token": cloudkit_token,
                "ds_prs_id": ds_prs_id,
                "mme_token": mme_token,
                }, f, indent=4)
            
    logging.debug("CloudKit token: ", cloudkit_token)

    ck = cloudkit.CloudKit(ds_prs_id, cloudkit_token, mme_token, sandbox=True)
    #ck.container("iCloud.dev.jjtech.experiments.cktest").save_record(cloudkit.Record("test", "ToDoItem", {"title": "Test2"}))

    # Read the test file
    with open("/Users/jjtech/Downloads/test.rtf", "rb") as f:
        file = f.read()


    a = cloudkit.CloudKitAsset("test", "rtf", file)
    print(a.hash().hex())

    #cloudkit._build_authorize_put(cloudkit.Record("testassset", "test", None), a, "iCloud.dev.jjtech.experiments.cktest")
    a._authorize_put(ck.container("iCloud.dev.jjtech.experiments.cktest"), cloudkit.Record("testassset", "test", None), a)
    #c = cloudkit.CloudKitAsset.Chunk(file, None)
    #print(c.checksum().hex())
        


if __name__ == "__main__":
    main()