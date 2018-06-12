import argparse
import atexit
import os
from random import randrange

import requests
from com.vmware.vapi.std.errors_client import InvalidRequest
from com.vmware.vmc.model_client import AwsSddcConfig, ErrorResponse, AccountLinkSddcConfig, SddcConfig
from tabulate import tabulate
from vmware.vapi.vmc.client import create_vmc_client

token='1111ef56-a2fa-4df7-942e-88191bba3d93'
org_id ='058f47c4-92aa-417f-8747-87f3ed61cb45'
client = create_vmc_client(token)

client.orgs.account_link.CompatibleSubnets.get(org_id)

try:
    client.orgs.account_link.CompatibleSubnets.get(org_id)
except Exception as e:
    # error_response = e.data.convert_to(ErrorResponse)
    # raise Exception(error_response.error_messages)
    print(e)