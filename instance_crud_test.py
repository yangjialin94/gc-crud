import os
import json
import instance_crud

SERVICE_ACCOUNT_FILE = 'client_secrets.json'
PROJECT = 'indigo-night-126317'
ZONE = 'us-central1-a'
LOCAL_SSD_INSTANCE = 'instance-with-local-test'
NO_LOCAL_SSD_INSTNACE = 'instance-no-local-test'

def write_to_file(obj, file_name):
    with open(
        os.path.join(
            os.path.dirname(__file__), file_name), 'w+') as writer:
        writer.write(json.dumps(obj))

def main(project, zone):
    '''
    Get credentials
    Get compute_v1
    Get compute_beta
    '''
    # get credentials
    print('Getting credentials...')
    credentials = instance_crud.get_credentials(SERVICE_ACCOUNT_FILE)
    print(f'Got credentials')

    # get compute_v1 instance
    print('Getting compute_v1...')
    compute_v1 = instance_crud.get_compute('v1', credentials)
    print('Got compute_v1')

    # get compute_beta instance
    print('Getting compute_beta...')
    compute_beta = instance_crud.get_compute('Beta', credentials)
    print('Got compute_beta')
    
    '''
    Instance with local SSD disk - LOCAL_SSD_INSTANCE

    Create
    Suspend
    Resume
    Get
    Save to file
    '''
    # create new instance - LOCAL_SSD_INSTANCE
    print(f'Creating instance \'{LOCAL_SSD_INSTANCE}\'...')
    operation = instance_crud.create_instance(
        compute_v1, 
        project, 
        zone, 
        LOCAL_SSD_INSTANCE, 
        True)
    instance_crud.wait_for_operation(
        compute_v1, 
        project, 
        zone, 
        operation['name'])
    print(f'Created instance \'{LOCAL_SSD_INSTANCE}\'')

    # suspend instance - LOCAL_SSD_INSTANCE
    print(f'Suspending instance \'{LOCAL_SSD_INSTANCE}\'...')
    operation = instance_crud.suspend_instance(
        compute_beta, 
        project, 
        zone, 
        LOCAL_SSD_INSTANCE)
    instance_crud.wait_for_operation(
        compute_beta, 
        project, 
        zone, 
        operation['name'])
    print(f'Suspended instance \'{LOCAL_SSD_INSTANCE}\'')

    # resume instance - LOCAL_SSD_INSTANCE
    print(f'Resuming instance \'{LOCAL_SSD_INSTANCE}\'...')
    operation = instance_crud.resume_instance(
        compute_beta, 
        project, 
        zone, 
        LOCAL_SSD_INSTANCE)
    instance_crud.wait_for_operation(
        compute_beta, 
        project, 
        zone, 
        operation['name'])
    print(f'Resumed instance \'{LOCAL_SSD_INSTANCE}\'')

    # get instance - LOCAL_SSD_INSTANCE
    print(f'Getting instance \'{LOCAL_SSD_INSTANCE}\'...')
    instance = instance_crud.get_instance(
        compute_v1, 
        project, 
        zone,
        LOCAL_SSD_INSTANCE)
    print(f'Got instance \'{LOCAL_SSD_INSTANCE}\'')

    # print instance - LOCAL_SSD_INSTANCE
    print(f'Saving instance \'{LOCAL_SSD_INSTANCE}\'...')
    write_to_file(instance, 'local_ssd_instance.json')
    print(f'Saved instance \'{LOCAL_SSD_INSTANCE}\'')

    '''
    Instance without local SSD disk - NO_LOCAL_SSD_INSTNACE

    Create
    Stop
    Start
    Get
    Save to file
    '''
    # create new instance - NO_LOCAL_SSD_INSTNACE
    print(f'Creating instance \'{NO_LOCAL_SSD_INSTNACE}\'...')
    operation = instance_crud.create_instance(
        compute_v1, 
        project, 
        zone, 
        NO_LOCAL_SSD_INSTNACE, 
        False)
    instance_crud.wait_for_operation(
        compute_v1, 
        project, 
        zone, 
        operation['name'])
    print(f'Created instance \'{NO_LOCAL_SSD_INSTNACE}\'')

    # stop instance - NO_LOCAL_SSD_INSTNACE
    print(f'Stopping instance \'{NO_LOCAL_SSD_INSTNACE}\'...')
    operation = instance_crud.stop_instance(
        compute_v1, 
        project, 
        zone, 
        NO_LOCAL_SSD_INSTNACE)
    instance_crud.wait_for_operation(
        compute_v1, 
        project, 
        zone, 
        operation['name'])
    print(f'Stopped instance \'{NO_LOCAL_SSD_INSTNACE}\'')

    # start instance - NO_LOCAL_SSD_INSTNACE
    print(f'Starting instance \'{NO_LOCAL_SSD_INSTNACE}\'...')
    operation = instance_crud.start_instance(
        compute_v1, 
        project, 
        zone, 
        NO_LOCAL_SSD_INSTNACE)
    instance_crud.wait_for_operation(
        compute_v1, 
        project, 
        zone, 
        operation['name'])
    print(f'Started instance \'{NO_LOCAL_SSD_INSTNACE}\'')

    # get instance - NO_LOCAL_SSD_INSTNACE
    print(f'Getting instance \'{NO_LOCAL_SSD_INSTNACE}\'...')
    instance = instance_crud.get_instance(
        compute_v1, 
        project, 
        zone,
        NO_LOCAL_SSD_INSTNACE)
    print(f'Got instance \'{NO_LOCAL_SSD_INSTNACE}\'')

    # print instance - NO_LOCAL_SSD_INSTNACE
    print(f'Saving instance \'{NO_LOCAL_SSD_INSTNACE}\'...')
    write_to_file(instance, 'no_local_ssd_instance.json')
    print(f'Saved instance \'{NO_LOCAL_SSD_INSTNACE}\'')

    '''
    List 
    Save to file
    Delete
    '''
    # get zones and list of instances
    print('List zones...')
    zones = instance_crud.list_zones(compute_v1, project)
    print('Listed zones')
    print('List instances...')
    instances = []

    for temp_zone in zones:
        new_instances = instance_crud.list_instances(
            compute_v1, 
            project, 
            temp_zone)
        
        if new_instances != None:
            instances += new_instances

    print('Listed instances')
   
    # print list of instances into log.json file
    print('Saving instances...')
    write_to_file(instances, 'list_instances.json')
    print(f'Saved instances')

    # delete instance - LOCAL_SSD_INSTANCE
    print(f'Deleting instance \'{LOCAL_SSD_INSTANCE}\'...')
    operation = instance_crud.delete_instance(
        compute_v1, 
        project, 
        zone, 
        LOCAL_SSD_INSTANCE)
    instance_crud.wait_for_operation(
        compute_v1, 
        project, 
        zone, 
        operation['name'])
    print(f'Deleted instance \'{LOCAL_SSD_INSTANCE}\'...')

    # delete instance - NO_LOCAL_SSD_INSTNACE
    print(f'Deleting instance \'{NO_LOCAL_SSD_INSTNACE}\'...')
    operation = instance_crud.delete_instance(
        compute_v1, 
        project, 
        zone, 
        NO_LOCAL_SSD_INSTNACE)
    instance_crud.wait_for_operation(
        compute_v1, 
        project, 
        zone, 
        operation['name'])
    print(f'Deleted instance \'{NO_LOCAL_SSD_INSTNACE}\'...')

if __name__ == '__main__':
    print('### START ###')
    main(PROJECT, ZONE)
    print('### END ###')
