#!/usr/bin/env python

"""
* *******************************************************
* Copyright VMware, Inc. 2018. All Rights Reserved.
* SPDX-License-Identifier: MIT
* *******************************************************
*
* DISCLAIMER. THIS PROGRAM IS PROVIDED TO YOU "AS IS" WITHOUT
* WARRANTIES OR CONDITIONS OF ANY KIND, WHETHER ORAL OR WRITTEN,
* EXPRESS OR IMPLIED. THE AUTHOR SPECIFICALLY DISCLAIMS ANY IMPLIED
* WARRANTIES OR CONDITIONS OF MERCHANTABILITY, SATISFACTORY QUALITY,
* NON-INFRINGEMENT AND FITNESS FOR A PARTICULAR PURPOSE.
"""
from com.vmware.vcenter_client import Datastore
from vmware.vapi.vsphere.client import create_vsphere_client

from samples.vsphere.common import sample_cli, sample_util
from samples.vsphere.common.service_manager import ServiceManager
from samples.vsphere.contentlibrary.lib.cls_api_client import ClsApiClient

__author__ = 'VMware, Inc.'
__vcenter_version__ = 'VMware Cloud on AWS'

import tempfile

try:
    import urllib2
except ImportError:
    import urllib.request as urllib2

from com.vmware.content_client import LibraryModel
from com.vmware.content.library_client import StorageBacking, ItemModel
from samples.vsphere.common.id_generator import generate_random_uuid
from samples.vsphere.contentlibrary.lib.cls_api_helper import ClsApiHelper


class OvfImportExportCloud:
    """
    Demonstrates the workflow to import an OVF package into the content library,
    as well as download of an OVF template from the content library.

    Note: the workflow needs an existing VC DS with available storage.
    """

    def __init__(self):
        parser = sample_cli.build_arg_parser()
        parser.add_argument('--datastorename',
                            default='WorkloadDatastore',
                            help='The name of the datastore.')
        args = sample_util.process_cli_args(parser.parse_args())

        self.lib_name = "demo-lib"
        self.lib_item_name = "simpleVmTemplate"
        self.datastore_name = args.datastorename
        self.cleardata = args.cleardata

        # Connect to vAPI Endpoint on vCenter Server
        self.client = create_vsphere_client(server=args.server,
                                            username=args.username,
                                            password=args.password)

        self.service_manager = ServiceManager(args.server,
                                              args.username,
                                              args.password,
                                              args.skip_verification)
        self.service_manager.connect()

        self.client = ClsApiClient(self.servicemanager)
        self.helper = ClsApiHelper(self.client, self.skip_verification)

    def create_library_item(self):
        # Find the datastore by the given datastore name
        filter_spec = Datastore.FilterSpec(names=set([self.datastore_name]))
        datastore_summaries = self.client.vcenter.Datastore.list(filter_spec)
        if not datastore_summaries:
            raise ValueError('Datastore with name ({}) not found'.
                             format(self.datastore_name))
        self.datastore_id = datastore_summaries[0].datastore
        print('Datastore: {} ID: {}'.format(self.datastore_name, self.datastore_id))

        # Build the storage backing for the library to be created
        storage_backings = []
        storage_backing = StorageBacking(type=StorageBacking.Type.DATASTORE, datastore_id=self.datastore_id)
        storage_backings.append(storage_backing)

        # Build the specification for the library to be created
        create_spec = LibraryModel()
        create_spec.name = self.lib_name
        create_spec.description = "Local library backed by VC datastore"
        create_spec.type = create_spec.LibraryType.LOCAL
        create_spec.storage_backings = storage_backings

        # Create a local content library backed the VC datastore using vAPIs
        library_id = self.client.content.LocalLibrary.create(create_spec=create_spec,
                                                             client_token=generate_random_uuid())
        print('Local library created: ID: {0}'.format(library_id))
        self.local_library = self.client.content.LocalLibrary.get(library_id)

        # Create a new library item in the content library for uploading the files
        lib_item_spec = ItemModel(name=self.lib_item_name,
                                  description='Sample simple VM template',
                                  library_id=library_id,
                                  type='ovf')

        # Create a library item
        self.library_item_id = self.client.content.library.Item.create(
            create_spec=lib_item_spec,
            client_token=generate_random_uuid())
        assert self.client.content.library.Item.get(self.library_item_id) is not None
        print('Library item created id: {}'.format(self.library_item_id))

    def import_ovf_template(self):
        # Upload a VM template to the CL
        ovf_files_map = self.helper.get_ovf_files_map(ClsApiHelper.SIMPLE_OVF_RELATIVE_DIR)
        self.helper.upload_files(library_item_id=self.library_item_id, files_map=ovf_files_map)
        print('Uploaded ovf and vmdk files to library item {0}'.format(self.library_item_id))

    def export_ovf_template(self):
        # Download the library item from the CL
        temp_dir = tempfile.mkdtemp(prefix='simpleVmTemplate-')
        print('Downloading library item {0} to directory {1}'.format(self.library_item_id, temp_dir))
        downloaded_files_map = self.helper.download_files(library_item_id=self.library_item_id, directory=temp_dir)
        assert len(downloaded_files_map) == len(ovf_files_map)

    def delete_library(self):
        if self.cleardata:
            self.client.content.LocalLibrary.delete(library_id=self.local_library.id)
            print('Deleted Library Id: {0}'.format(self.local_library.id))


def main():
    ovf_import_export_cloud = OvfImportExportCloud()
    ovf_import_export_cloud.create_library_item()
    # ovf_import_export_cloud.import_ovf_template()
    # ovf_import_export_cloud.export_ovf_template()
    # ovf_import_export_cloud.delete_library()


if __name__ == '__main__':
    main()
