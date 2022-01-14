import os


def parse_instance(instance, project) -> object:
    network_interface = instance['networkInterfaces'][0]
    return {
        'name': instance['name'],
        'project': project,
        'user_id': '',
        'gcp_id': instance['id'],
        'status': instance['status'],
        'zone': instance['zone'].split('/')[-1],
        'created_at': instance['creationTimestamp'],
        'machine_type': instance['machineType'].split('/')[-1],
        'internal_ip': network_interface['networkIP'],
        'external_ip': 
            network_interface['accessConfigs'][0]['natIP'] 
            if 'natIP' in network_interface['accessConfigs'][0].keys()
            else '',
        'boot_disk_size': instance['disks'][0]['diskSizeGb'],
        'local_disk_size': 
            instance['disks'][1]['diskSizeGb'] 
            if len(instance['disks']) > 1 else '',
        'tailscale_user': '',
        'tailscale_status': '',
        'tailscale_ip': '',
        'notify_issues': False,
        'notify_cost': False,
        'notify_inactive':  False
    }
    
def parse_instances(instances, project) -> list:
    ret = []

    for instance in instances:
        ret.append(parse_instance(instance, project))
    
    return ret

def create_instance_config(compute, zone, name, has_local):
    machine_type = f'zones/{zone}/machineTypes/n2-highmem-4'

    image_response = compute.images().getFromFamily(
        project='debian-cloud', family='debian-11').execute()
    source_disk_image = image_response['selfLink']

    disk_type = f'zones/{zone}/diskTypes/local-ssd'

    startup_script = open(
        os.path.join(
            os.path.dirname(__file__), 'setup_cloud_vm.sh'), 'r').read()

    config = {
        'name': name,
        'tags': {
            'items': ['sap', 'http']
        },
        'machineType': machine_type,
        'zone': zone,
        'disks': [
            {
                'boot': True,
                'autoDelete': True,
                'initializeParams': {
                    'sourceImage': source_disk_image,
                    'diskSizeGb': 50
                }
            }
        ],
        'networkInterfaces': [{
            'network': 'global/networks/default',
            'accessConfigs': [
                {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
            ]
        }],
        'serviceAccounts': [{
            'scopes': [
                'https://www.googleapis.com/auth/servicecontrol',
                'https://www.googleapis.com/auth/service.management.readonly',
                'https://www.googleapis.com/auth/logging.write',
                'https://www.googleapis.com/auth/monitoring.write',
                'https://www.googleapis.com/auth/trace.append',
                'https://www.googleapis.com/auth/devstorage.read_write'
            ]
        }],
        'metadata': {
            'items': [{
                'key': 'startup-script',
                'value': startup_script
            }]
        }
    }

    if has_local:
        config['disks'].append(
            {
                'type': 'SCRATCH',
                'boot': False,
                'autoDelete': True,
                'initializeParams': {
                    'diskSizeGb': 375,
                    'diskType': disk_type
                },
                'interface': 'NVME'
            }
        )

    return config
