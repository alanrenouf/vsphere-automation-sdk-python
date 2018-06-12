export PYTHONPATH=/Users/het/github/vsphere-automation-sdk-python/
export VC=vcenter.sddc-50-112-61-134.vmc.vmware.com
python /Users/het/github/vsphere-automation-sdk-python/samples/vsphere/contentlibrary/ovfimport/ovf_import_export.py -s $VC -u 'cloudadmin@vmc.local' -p '0ln*%e3Wxd' -c --datastorename 'WorkloadDatastore' -v