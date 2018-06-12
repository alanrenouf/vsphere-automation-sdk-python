export PYTHONPATH=/Users/het/github/vsphere-automation-sdk-python/
export VC=10.192.169.156
python /Users/het/github/vsphere-automation-sdk-python/samples/vsphere/contentlibrary/ovfdeploy/deploy_ovf_template.py -s $VC -u administrator@vsphere.local -p 'Admin!23' -v -clustername 'Cluster1' -libitemname 'vm'