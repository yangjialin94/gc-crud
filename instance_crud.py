import time
import instance_crud_helper

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/compute']


def get_credentials(service_account_file) -> object:
    """
    :param str service_account_file: The service account file name
    :return: credentials object
    :rtype: object
    """
    return service_account.Credentials.from_service_account_file(
        service_account_file, scopes=SCOPES)

def get_compute(version, credentials) -> object:
    """
    :param str version: The api version
    sparam object credentials: The credentials object
    :return: credentials object
    :rtype: object
    """
    return build('compute', version, credentials=credentials)

def list_zones(compute, project) -> list:
    """
    :param object compute: The compute instance
    :param str project: The project name
    :return: list of zones
    :rtype: list of str
    """
    result = compute.zones().list(project=project).execute()
    zones = result['items'] if 'items' in result else None

    if zones != None:
        zones = [zone['name'] for zone in zones]
    
    return zones

def list_instances(compute, project, zone) -> list:
    """
    :param object compute: The compute instance
    :param str project: The project name
    :param str zone: The instance zone
    :return: list of instances
    :rtype: list of object
    """
    result = compute.instances().list(project=project, zone=zone).execute()
    instances = result['items'] if 'items' in result else None

    if instances != None:
        instances = instance_crud_helper.parse_instances(instances, project)

    return instances

def get_instance(compute, project, zone, name) -> object:
    """
    :param object compute: The compute instance
    :param str project: The project name
    :param str zone: The instance zone
    :param str name: The instance name
    :return: instance
    :rtype: object
    """
    instance = compute.instances().get(
        project=project, 
        zone=zone, 
        instance=name).execute()

    if instance != None: 
        instance = instance_crud_helper.parse_instance(instance, project)

    return instance

def create_instance(compute, project, zone, name, has_local) -> object:
    """
    :param object compute: The compute instance
    :param str project: The project name
    :param str zone: The instance zone
    :param str name: The instance name
    :return: ?
    :rtype: object
    """
    config = instance_crud_helper.create_instance_config(
        compute, 
        zone, 
        name, 
        has_local)

    return compute.instances().insert(
        project=project,
        zone=zone,
        body=config).execute()

def delete_instance(compute, project, zone, name) -> object:
    """
    :param object compute: The compute instance
    :param str project: The project name
    :param str zone: The instance zone
    :param str name: The instance name
    :return: ?
    :rtype: object
    """
    return compute.instances().delete(
        project=project,
        zone=zone,
        instance=name).execute()

def stop_instance(compute, project, zone, name) -> object:
    """
    :param object compute: The compute instance
    :param str project: The project name
    :param str zone: The instance zone
    :param str name: The instance name
    :return: ?
    :rtype: object
    """
    return compute.instances().stop(
        project=project,
        zone=zone,
        instance=name).execute()

def start_instance(compute, project, zone, name) -> object:
    """
    :param object compute: The compute instance
    :param str project: The project name
    :param str zone: The instance zone
    :param str name: The instance name
    :return: ?
    :rtype: object
    """
    return compute.instances().start(
        project=project,
        zone=zone,
        instance=name).execute()

def suspend_instance(compute, project, zone, name) -> object:
    """
    :param object compute: The compute instance
    :param str project: The project name
    :param str zone: The instance zone
    :param str name: The instance name
    :return: ?
    :rtype: object
    """
    return compute.instances().suspend(
        project=project,
        zone=zone,
        instance=name,
        discardLocalSsd=True).execute()

def resume_instance(compute, project, zone, name) -> object:
    """
    :param object compute: The compute instance
    :param str project: The project name
    :param str zone: The instance zone
    :param str name: The instance name
    :return: ?
    :rtype: object
    """
    return compute.instances().resume(
        project=project,
        zone=zone,
        instance=name).execute()

def wait_for_operation(compute, project, zone, operation):
    """
    :param object compute: The compute instance
    :param str project: The project name
    :param str zone: The instance zone
    :param object operation: The operation that's currenlty running
    """
    while True:
        result = compute.zoneOperations().get(
            project=project,
            zone=zone,
            operation=operation).execute()

        if result['status'] == 'DONE':
            if 'error' in result:
                raise Exception(result['error'])
            return result

        time.sleep(1)
