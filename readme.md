# CRUD instances with Google Cloud API

## Requirement

-   Get your client secrets json file for your service account and name it client_secrets.json.
-   Link to the service accounts: https://console.cloud.google.com/iam-admin/serviceaccounts.
-   Put your client_secrets.json in the root directory.
-   Check ouput.json for sample ouput data after project is finish running.

## Key files

-   **instance_crud.py** includes all the GC API instance CRUD related functions:

    -   get_credentials
    -   get_compute
    -   list_zones
    -   list_instances
    -   get_instance
    -   create_instance
    -   delete_instance
    -   stop_instance
    -   start_instance
    -   suspend_instance
    -   resume_instance
    -   wait_for_operation

-   **instance_crud_healper.py** includes all the helper functions for the instance_crud.py file:
    -   parse_instance
    -   parse_instances
    -   create_instance_config

## Running the project

```
$ pipenv install
$ pipenv shell
$ python3 instance_crud_test.py
```

## Successful terminal output

```
### START ###
Getting credentials...
Got credentials
Getting compute_v1...
Got compute_v1
Getting compute_beta...
Got compute_beta
Creating instance 'instance-with-local-test'...
Created instance 'instance-with-local-test'
Suspending instance 'instance-with-local-test'...
Suspended instance 'instance-with-local-test'
Resuming instance 'instance-with-local-test'...
Resumed instance 'instance-with-local-test'
Getting instance 'instance-with-local-test'...
Got instance 'instance-with-local-test'
Saving instance 'instance-with-local-test'...
Saved instance 'instance-with-local-test'
Creating instance 'instance-no-local-test'...
Created instance 'instance-no-local-test'
Stopping instance 'instance-no-local-test'...
Stopped instance 'instance-no-local-test'
Starting instance 'instance-no-local-test'...
Started instance 'instance-no-local-test'
Getting instance 'instance-no-local-test'...
Got instance 'instance-no-local-test'
Saving instance 'instance-no-local-test'...
Saved instance 'instance-no-local-test'
List zones...
Listed zones
List instances...
Listed instances
Saving instances...
Saved instances
Deleting instance 'instance-with-local-test'...
Deleted instance 'instance-with-local-test'...
Deleting instance 'instance-no-local-test'...
Deleted instance 'instance-no-local-test'...
### END ###
```

## Ouput

-   local_ssd_instance.json
-   no_local_ssd_instance.json
-   list_instances.json
