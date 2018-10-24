# instance_reservations

## To Use:

- Update the following line to point to your AWS credentials file:\
os.environ["AWS_SHARED_CREDENTIALS_FILE"]="{PATH_TO_YOUR_CREDENTIALS_FILE}"

- Update the following line to select which AWS profile to run against:\
profile = '{PROFILE_TO_RUN_SCRIPT_AGAINST}'


## Running this code performs the following items:

1. Create folder reservations/ (if it doesn't exist)
2. Create folder reservations/data/ (if it doesn't exist)
3. For the specified AWS account:
* For each reagion in the regions array create a data text file with the following information by Instance Type:
    * Number of active reservations for each instance type
    * Number of running instances for each instance type
    * 