#!/usr/bin/env python

"""
* *******************************************************
* Copyright (c) VMware, Inc. 2018. All Rights Reserved.
* SPDX-License-Identifier: MIT
* *******************************************************
*
* DISCLAIMER. THIS PROGRAM IS PROVIDED TO YOU "AS IS" WITHOUT
* WARRANTIES OR CONDITIONS OF ANY KIND, WHETHER ORAL OR WRITTEN,
* EXPRESS OR IMPLIED. THE AUTHOR SPECIFICALLY DISCLAIMS ANY IMPLIED
* WARRANTIES OR CONDITIONS OF MERCHANTABILITY, SATISFACTORY QUALITY,
* NON-INFRINGEMENT AND FITNESS FOR A PARTICULAR PURPOSE.
"""

__author__ = 'VMware, Inc.'
__vcenter_version__ = 'VMware Cloud on AWS'

import argparse
from six.moves.urllib import parse

from com.vmware.content.library_client import Item
from com.vmware.vapi.std.errors_client import NotFound
from com.vmware.vcenter.ovf_client import LibraryItem
from com.vmware.vmc.model_client import ErrorResponse

from vmware.vapi.vsphere.client import create_vsphere_client
from vmware.vapi.vmc.client import create_vmc_client

from samples.vsphere.common.id_generator import generate_random_uuid
from samples.vsphere.vcenter.helper.resource_pool_helper import get_resource_pool
from samples.vsphere.vcenter.helper.folder_helper import get_folder


class DeployVM(object):
    """
    Demonstrates how to deploy a VM in a SDDC

    Sample Prerequisites:
        - A SDDC in the org
        - A firewall rule to access the vSphere
        - An existing library item with an OVF template
        - An existing cluster with resources for deploying the VM.
    """

    def __init__(self):
        parser = argparse.ArgumentParser()

        parser.add_argument('-r', '--refresh-token',
                            required=True,
                            help='VMware Cloud API refresh token')

        parser.add_argument('-o', '--org-id',
                            required=True,
                            help='Organization identifier.')

        parser.add_argument('-s', '--sddc-id',
                            required=True,
                            help='Sddc Identifier.')

        parser.add_argument('--libitem-name',
                            required=True,
                            help='The name of the library item to deploy.'
                                 'The library item should contain an OVF package.')

        parser.add_argument('--datacenter-name',
                            default='SDDC-Datacenter',
                            help='The name of the datacenter to be used.')

        parser.add_argument('--resourcepool-name',
                            default='Compute-ResourcePool',
                            help='The name of the resourcepool to be used.')

        parser.add_argument('--folder-name',
                            default='Workloads',
                            help='The name of the folder to be used.')

        parser.add_argument('-c', '--cleardata',
                            action='store_true',
                            help='Clean up after sample run.')

        args = parser.parse_args()

        self.refresh_token = args.refresh_token
        self.org_id = args.org_id
        self.sddc_id = args.sddc_id
        self.resourcepool_name = args.resourcepool_name
        self.datacenter_name = args.datacenter_name
        self.folder_name = args.folder_name
        self.libitem_name = args.libitem_name
        self.cleardata = args.cleardata

        # Connect to VMware Cloud on AWS
        self.vmc_client = create_vmc_client(self.refresh_token)

        # Check if the organization exists
        orgs = self.vmc_client.Orgs.list()
        if self.org_id not in [org.id for org in orgs]:
            raise ValueError("Org with ID {} doesn't exist".format(self.org_id))

        # Check if the SDDC exists
        try:
            self.sddc = self.vmc_client.orgs.Sddcs.get(self.org_id, self.sddc_id)
        except NotFound as e:
            error_response = e.data.convert_to(ErrorResponse)
            raise ValueError(error_response.error_messages)

        self.vm_name = 'Deploy VM Sample - ' + generate_random_uuid()

        # Get VC hostname
        server = parse.urlparse(self.sddc.resource_config.vc_url).hostname

        # Connect to vSphere client
        self.client = create_vsphere_client(server,
                                            username=self.sddc.resource_config.cloud_username,
                                            password=self.sddc.resource_config.cloud_password)

    def run(self):

        resourcepool_id = get_resource_pool(self.client, self.datacenter_name, self.resourcepool_name)
        print("\n# Example: Found resource pool '{}' with ID {}".format(self.resourcepool_name, resourcepool_id))

        folder_id = get_folder(self.client, self.datacenter_name, self.folder_name)
        print("\n# Example: Found folder '{}' with ID {}".format(self.folder_name, folder_id))

        deployment_target = LibraryItem.DeploymentTarget(resource_pool_id=resourcepool_id,
                                                         folder_id=folder_id)

        # Find ovf in the content library
        find_spec = Item.FindSpec(name=self.libitem_name)
        item_ids = self.client.content.library.Item.find(find_spec)
        if not item_ids:
            raise ValueError("Can't find content library item {}".format(self.libitem_name))
        item_id = item_ids[0]

        ovf_summary = self.client.vcenter.ovf.LibraryItem.filter(ovf_library_item_id=item_id,
                                                                 target=deployment_target)
        print("\n# Example: Found an OVF template '{0}' to deploy.".format(ovf_summary.name))

        deployment_spec = LibraryItem.ResourcePoolDeploymentSpec(
            name=self.vm_name,
            annotation=ovf_summary.annotation,
            accept_all_eula=True,
            network_mappings=None,
            storage_mappings=None,
            storage_provisioning=None,
            storage_profile_id=None,
            locale=None,
            flags=None,
            additional_parameters=None,
            default_datastore_id=None)

        # Deploy the ovf template
        result = self.client.vcenter.ovf.LibraryItem.deploy(item_id,
                                                            deployment_target,
                                                            deployment_spec,
                                                            client_token=generate_random_uuid())

        # The type and ID of the target deployment is available in the deployment result.
        if result.succeeded:
            print("\n# Example: Deployment successful. Result resource: {}, ID: {}, Name: '{}'"
                  .format(result.resource_id.type, result.resource_id.id, self.vm_name))
            self.vm_id = result.resource_id.id
            error = result.error
            if error is not None:
                for warning in error.warnings:
                    print('OVF warning: {}'.format(warning.message))

        else:
            print('Deployment failed.')
            for error in result.error.errors:
                print('OVF error: {}'.format(error.message))

    def cleanup(self):
        if self.cleardata:
            self.client.vcenter.VM.delete(self.vm_id)
            print('\n# Cleanup: Virtual Machine {} is deleted.'.format(self.vm_id))


def main():
    deploy_vm = DeployVM()
    deploy_vm.run()
    deploy_vm.cleanup()


if __name__ == '__main__':
    main()
