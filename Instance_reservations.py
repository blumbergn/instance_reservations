import json
import pprint
import os,sys
import boto3
from collections import Counter,defaultdict
import datetime

# #################################################################################
# Changes needed:
## - separate by OS type
## - make AWS profile an input
## - write totals and percentage
## - better output format

# #################################################################################

# Global vars
cur_dir = os.path.dirname(sys.argv[0])
data_dir = os.path.join(cur_dir,'reservations/data/')
reservation_dir = os.path.join(cur_dir, 'reservations/')
os.environ["AWS_SHARED_CREDENTIALS_FILE"]="{PATH_TO_YOUR_CREDENTIALS_FILE}"
pp = pprint.PrettyPrinter()
regions = ['us-east-1','us-east-2','us-west-1','us-west-2']
profile = '{PROFILE_TO_RUN_SCRIPT_AGAINST}'
reservation_file_name = profile + '.xlsx'
reservations_file = os.path.join(reservation_dir,reservation_file_name)

def get_expired_reservations(data):
    reservations = data[0]["Reservations"]
    print(reservations)
    for instance in reservations:
        instance_type = instance["Instances"][0]["InstanceType"]
        instance_os = instance["Instances"][0]["Platform"]
        
           
  

    return

def get_client(resource,region):
    client = boto3.Session(profile_name=profile,region_name=region).client(resource)
    
    
    return client

def get_total_snap_size(region):
    total_gb = 0
    ec2_cli = get_client('ec2',region)
    snap_shots = ec2_cli.describe_snapshots(OwnerIds=OwnerIds)

    total_snaps = len(snap_shots['Snapshots'])

    for snap in snap_shots['Snapshots']:
        
        total_gb = total_gb + snap['VolumeSize']
 
    return total_snaps, total_gb

def get_total_volumes(region):
    
    available_volume_size = 0
    available_volumes = 0
    ec2_cli = get_client('ec2',region)
    volumes = ec2_cli.describe_volumes()

    for volume in volumes['Volumes']:
        if volume['State'] == 'available':
            available_volumes += 1
            available_volume_size = available_volume_size + volume['Size']


    return available_volumes, available_volume_size

def get_snapshot_servers(region):


    ec2_cli = get_client('ec2',region)
    snap_shots = ec2_cli.describe_snapshots(MaxResults=10,OwnerIds=OwnerIds)
    for snap_shot in snap_shots['Snapshots']:
        if 'Created by CreateImage' in snap_shot['Description']:
            snap_shot_desc = snap_shot['Description']
            server_source = snap_shot_desc.split()
            server_source = str(server_source[2])
            server_source = server_source.split("(")
            server_source = str(server_source[1])
            server_source = server_source.replace(")","")
            print(server_source)
            try:
                instance = ec2_cli.describe_instances(InstanceIds=[server_source])
                pp.pprint(instance['Reservations'])
            
            except Exception as e:
                print(e)
    

    return 

def get_reservations(region):

    res_by_type = {}
    total_res = 0
    ec2_cli = get_client('ec2',region)
    reservations = ec2_cli.describe_reserved_instances(Filters=[{'Name':'state','Values':['active']}])
    for reservation in reservations['ReservedInstances']:
        # pp.pprint(reservation)
        total_res = total_res + reservation['InstanceCount']
        # print(str(reservation['InstanceCount']) + ' ' + str(reservation['InstanceType']) + '\n')
        res_by_type[reservation['InstanceType']] = reservation['InstanceCount']

    # print('Total Reserverations: ' + str(total_res))
    return res_by_type

def instances_by_type(region):
    
    instance_types = []
    
    ec2_cli = get_client('ec2',region)
    instances = ec2_cli.describe_instances(Filters=[{'Name': 'instance-state-name','Values':['running']}])
    for instance in instances['Reservations']:
        for inst in instance['Instances']:
            
            instance_types.append(inst["InstanceType"])
            

            
    instance_type_count = {}
    for item in instance_types:
        if item in instance_type_count:
            instance_type_count[item] = instance_type_count.get(item)+1
        else:
            instance_type_count[item] = 1
    
 

     
    return instance_type_count

def instance_details_by_type(region,instance_type):
    inst_records = defaultdict(list)
    ec2_cli = get_client('ec2',region)
    instances = ec2_cli.describe_instances(Filters=[{'Name': 'instance-state-name','Values':['running'],'Name': 'instance-type','Values':[instance_type]}])
    instance = instances['Reservations']
    
    for inst in instance:
        for ins in inst['Instances']:
            instance_id = ins['InstanceId']
            try:
                tags_list = ins['Tags']
                for tag in tags_list:
                    if tag['Key'] == 'Name':
                        instance_name = tag['Value']
            except Exception as e:
                print(str(e))
            if ins['State']['Name'] == 'running':
                try:
                    for char in  ':}':
                        instance_name = instance_name.replace(char,'')
                    launch_time = str((ins['LaunchTime'])) 
                    launch_time = launch_time.split(' ')
                    launch_time = launch_time[0]
                    inst_records[instance_id].append({'InstanceType': ins['InstanceType']})
                    inst_records[instance_id].append({'Name': instance_name})
                    inst_records[instance_id].append({'LaunchTime': launch_time})
                    inst_records[instance_id].append({'AZ': ins['Placement']['AvailabilityZone']})
                    inst_records[instance_id].append({'PrivateIP': ins['PrivateIpAddress']})
                    inst_records[instance_id].append({'State': ins['State']['Name']})
                except Exception as e:
                    print("Failed on instance: " + instance_id + "Because of: " + str(e))
                
        
        

    return inst_records

def output_instances_by_type(inst_records,instance_type,reservations_by_type_count,in_count,out_file):
    
    with open(out_file, 'a') as f:
        
        f.write("\nINSTANCE TYPE %s : ACTIVE RESERVATIONS: %s : INSTANCE COUNT:  %s\n" % (instance_type, reservations_by_type_count,in_count))
        for instance in inst_records:
            
            f.write("\n%s\n" % instance)
            for ins in inst_records[instance]:
            
                f.write("%s\n" % ins)

    return

def main():
    
    if not os.path.exists(reservation_dir):
        os.mkdir(reservation_dir)
    
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)

    if not os.path.exists(reservations_file):
       with open(reservations_file, 'w'): pass

    for region in regions:
        all_instances = 0
        reservation_percent = 0
        total_instances = 0
        total_reservations = 0
        out_file_name = profile + '-' + region + '.txt'
        out_file = os.path.join(data_dir, out_file_name)
        if os.path.exists(out_file):
            try:
                os.remove(out_file)
            except Exception as e:
                print(str(e))
        
        # Get running instances by size 
        instance_types = instances_by_type(region)

        # Get active reservations 
        reservations_by_type = get_reservations(region)
        
        
        for instance_type in instance_types:
            reservations_by_type_count = 0

            # Get the number of active reservations for each instance type
            if instance_type in reservations_by_type:
                reservations_by_type_count = reservations_by_type[instance_type]

            
            inst_records = instance_details_by_type(region,instance_type)
            in_count = str(len(inst_records))
            all_instances = all_instances + len(inst_records)
            total_reservations = total_reservations + reservations_by_type_count
            output_instances_by_type(inst_records,instance_type,reservations_by_type_count,in_count,out_file)

        if ((total_reservations != 0) and (all_instances != 0)):
            reservation_percent =  total_reservations / all_instances   
        
        print("Total instances: " + str(all_instances))
        print("Total Reservations: " + str(total_reservations))
        print("Reservations percentages: " + "{:.0%}".format(reservation_percent))
        print(out_file)

        
        with open(out_file, 'a') as f:
            f.write("#################################################\n")
            f.write("Total instances: " + str(all_instances) + "\n") 
            f.write("Total reservations: " + str(total_reservations) + "\n") 
            f.write("Reservation percentage: " + "{:.0%}".format(reservation_percent)) 
            f.write("\n###############################################\n")

if __name__ == "__main__":
    main()