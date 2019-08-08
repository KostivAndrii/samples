#!/usr/bin/env python3
import sys
import os
import json
import yaml
import argparse
import boto3
import jinja2
import http.client

from botocore.client import ClientError

allowed_action = ['CREATE', 'UPDATE', 'VERIFY', 'BOTO']
valid_stack_states = '''\
CREATE_COMPLETE
UPDATE_COMPLETE'''.splitlines()

# CREATE_IN_PROGRESS
# UPDATE_IN_PROGRESS
# UPDATE_COMPLETE_CLEANUP_IN_PROGRESS

def read_cfg(inputfile):
    try:
        stream = open(inputfile, 'r')
    except FileNotFoundError:
        print("can''t open source file %s" % inputfile)
        sys.exit(1)
    datamap = yaml.safe_load(stream)
    stream.close()
    # print('json_obj =', datamap)
    return datamap

def write_json(outputfile, data, KeyName, ValueName):
    try:
        output=open(outputfile, 'w')
    except FileNotFoundError:
        print("can't open destiantion file %s " % outputfile)
        sys.exit(2)
    OutputParam = [ {KeyName: paramm, ValueName: data[paramm]} for paramm in data ]
    json.dump(OutputParam, output)
    output.flush()
    output.close()
    # print('OutputParam =', OutputParam)
    return OutputParam

def run(cmd):
    return os.popen(cmd).read()

def check_run_and_ready(ec2, STACK_name, ec2_amount):
    # ec2_client = ec2.meta.client
    instances = ec2.instances.filter(
        Filters=[{'Name':'tag:STACK', 'Values': [STACK_name]}, \
                 {'Name': 'instance-state-name', 'Values': ['running']}])

    ec2_run_amount = 0
    for instance in instances:
        inst_status = ec2.meta.client.describe_instance_status(InstanceIds = [instance.id])
        ec2_run_amount += 1
        print("Id1: %s Id2: %s InstanceStatus: %s SystemStatus %s " % (instance.id, \
            inst_status['InstanceStatuses'][0]['InstanceId'], \
            inst_status['InstanceStatuses'][0]['InstanceStatus']['Status'],\
            inst_status['InstanceStatuses'][0]['SystemStatus']['Status']))
        if inst_status['InstanceStatuses'][0]['SystemStatus']['Status'] == 'initializing':
            waiter = ec2.meta.client.get_waiter('system_status_ok')
            waiter.wait(InstanceIds=[instance.id])
        if inst_status['InstanceStatuses'][0]['InstanceStatus']['Status'] == 'initializing':
            waiter = ec2.meta.client.get_waiter('instance_status_ok')
            waiter.wait(InstanceIds=[instance.id])
    return True if ec2_run_amount == ec2_amount else False

def get_ec2_IP(ec2, STACK_name, VM, IpAddressLabel, state):
    custom_filter = [{'Name':'tag:STACK', 'Values': [STACK_name]}, \
                     {'Name':'tag:VM', 'Values': [VM]}, \
                     {'Name': 'instance-state-name', 'Values': [state]}]
    response = ec2.meta.client.describe_instances(Filters=custom_filter)
    return response['Reservations'][0]['Instances'][0][IpAddressLabel]

def check_opened_port(IpAddress, port):
    conn = http.client.HTTPConnection(IpAddress, 8080)
    try:
        conn.request("GET", "/")
    except ConnectionRefusedError:
        exit('No connection could be made because the target machine actively refused it')
    response = conn.getresponse()
    # headers = response.getheaders()
    print(response.status)
    return True if response.status == 200 else False
    # # https://www.journaldev.com/19213/python-http-client-request-get-post

def stack_exists(cf_client, stack_name, STACK_STATUS):
    if STACK_STATUS == '' :
        stacks = cf_client.list_stacks()['StackSummaries']
    else:
        stacks = cf_client.list_stacks(StackStatusFilter=STACK_STATUS)['StackSummaries']
    # https://www.oipapio.com/question-811760
    # https://docs.aws.amazon.com/en_us/AWSCloudFormation/latest/UserGuide/using-cfn-describing-stacks.html
    for stack in stacks:
        if stack['StackStatus'] == 'DELETE_COMPLETE':
            continue
        if stack_name == stack['StackName']:
            return True
    return False

class s3_bucket:
    "class for working with s3 bucket"
    def __init__(self, backet_name):
        # del first_bucket_name first_
        self.__s3 = boto3.resource('s3')
        self.backet_name = backet_name
        try:
            self.__s3.meta.client.head_bucket(Bucket=backet_name)
        except ClientError:
            self.__create_bucket(self.backet_name)
        return

    def __create_bucket(self, bucket_name):
        # del s3_connection
        s3_client =  self.__s3.meta.client
        session = boto3.session.Session()
        current_region = session.region_name
        # bucket_name = create_bucket_name(bucket_prefix)
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={
            'LocationConstraint': current_region})
        print('create_bucket: ',bucket_name, current_region)
        return

    def upload_obj(self, bucket, file, key):
        try:
            cf_file=open(file, 'rb')
        except FileNotFoundError:
            print("can''t open destiantion file %s " % cf_file)
            sys.exit(2)
        self.__s3.Bucket(bucket).put_object(Key=key, Body=cf_file)

    def get_obj_url(self, s3_bucket, s3_key):
        bucket_location = self.__s3.meta.client.get_bucket_location(Bucket=s3_bucket)
        return "https://{1}.s3.{0}.amazonaws.com/{2}".format(bucket_location['LocationConstraint'], s3_bucket, s3_key)

    def del_obj(self, obj_key):
        obj = self.__s3.Object(self.backet_name, obj_key)
        return obj.delete()

def main():
    # # procassing input parameters
    parser = argparse.ArgumentParser(description='Programm to work with AWS')
    parser.add_argument('-a','--action', help='what to do CREATE/UPDATE/BOTO/VERIFY')
    parser.add_argument('-s','--stack', help='STACK name', type=str)
    parser.add_argument('-cf','--cloud-formation', help='file with cloud-formation templates')
    parser.add_argument('-i','--input', help='file with input parameters and tags')
    parser.add_argument('-s3','--s3', help='AWS S3 bucked name to store cloud-formation templates')
    parser.add_argument('-cfk','--cloud-formation-key', help='AWS S3 bucked key to store cloud-formation templates')
    args = parser.parse_args()

    if args.action not in allowed_action:
        print('wrong action - we process only', allowed_action)
        sys.exit()

    print("script will convert %s into parameters.json and tags.json for ENVIRONMENT ... and %s STACK %s" \
        % (args.input, args.action, args.stack) )

    # # preparing input parameters
    # reading params,tsgs from input file
    cfg = read_cfg(args.input)
    print('cfg = ', cfg)

    # selecting parameters and tags
    parameters = cfg["parameters"]
    tags = cfg["tags"]
    # add to tags STACK name to separate this stack
    tags['STACK'] = args.stack
    print('parameters = ', parameters)
    print('tags = ', tags)
    # converting input  parameters and tags to json
    jParameters = write_json("parameters.json",parameters,"ParameterKey", "ParameterValue")
    jTags = write_json("tags.json",tags,"Key", "Value")

    # # validating template
    # uploading template into S# bucket for deploying and validating cf-template
    s3 = s3_bucket(args.s3)
    print(dir(s3))
    print(s3._s3_bucket__s3)
    print(s3.__s3)

    s3.del_obj(args.cloud_formation_key)
    s3.upload_obj(args.s3, args.cloud_formation, args.cloud_formation_key)
    object_url = s3.get_obj_url(args.s3, args.cloud_formation_key)

    cf_client = boto3.client('cloudformation')
    # validate template via boto3 by passing s3 bucket obj_url
    print('ec2.yaml validate = ', cf_client.validate_template(TemplateURL=object_url))
    # validate template via awscli
    print('stdout = ', run("aws cloudformation validate-template --template-body file://ec2.yaml"))

    # # Lets do it
    ec2 = boto3.resource('ec2')
    # ec2_client = ec2.meta.client
    # ec2_client = boto3.client('ec2')

    # if action CREATE - create stack by awscli
    if args.action == "CREATE":
        cmd = "aws cloudformation create-stack --stack-name " + args.stack + \
              " --template-body file://ec2.yaml --parameters file://parameters.json --tags file://tags.json"
        print('Creating STACK = ', run(cmd))
    # if action UPDATE - create stack by awscli
    if args.action == "UPDATE":
        cmd = "aws cloudformation update-stack --stack-name " + args.stack + \
              " --template-body file://ec2.yaml --parameters file://parameters.json --tags file://tags.json"
        print('stdout = ', run(cmd))
    # if action BOTO - create or update stack by boto
    if args.action == "BOTO":
        if stack_exists(cf_client, args.stack, ''):
            print('Updating {}'.format(args.stack))
            response = cf_client.update_stack(StackName=args.stack, TemplateURL=object_url, Parameters=jParameters, Tags=jTags)
            waiter = cf_client.get_waiter('stack_update_complete')
        else:
            print('Creating {}'.format(args.stack))
            response = cf_client.create_stack(StackName=args.stack, TemplateURL=object_url, Parameters=jParameters, Tags=jTags)
            waiter = cf_client.get_waiter('stack_create_complete')
        waiter.wait(StackName=args.stack)
        print('ec2.yaml create = ', response)
    # if action VERIFY - verify stack by boto
    if args.action == "VERIFY":
        result_stack = stack_exists(cf_client, args.stack, ['CREATE_COMPLETE','UPDATE_COMPLETE'])
        if not result_stack :
            print('stack not ready')
        result_ec2 = check_run_and_ready(ec2, args.stack, 4)
        if not result_ec2 :
            exit('instances not ready')
        TomcatIpAddress = get_ec2_IP(ec2, args.stack, 'Tomcat', 'PublicIpAddress', 'running')
        result_app_port = check_opened_port(TomcatIpAddress, 8080)
        if not result_app_port :
            exit('application not ready')
        print(TomcatIpAddress)
        exit()

    ## Checkins created/updated STACK and EC2 instances status and prepare SSH to CM BackEnd
    # check finish initializing 4 pcs EC2 instances
    check_run_and_ready(ec2, args.stack, 4)

    # gathering info (public and privet IP) to prepare connection to BackEnd
    PublicIpAddress = get_ec2_IP(ec2, args.stack, 'NATGW', 'PublicIpAddress', 'running')
    BackEndIpAddress = get_ec2_IP(ec2, args.stack, 'BackEnd', 'PrivateIpAddress', 'running')

    # # ssh ProxyJump via NAT gateway to BackEnd
    # jinja2 https://keyboardinterrupt.org/rendering-html-with-jinja2-in-python-3-6/?doing_wp_cron=1560335950.6937348842620849609375
    template_filename = "config.j2"
    rendered_filename = "config"
    render_vars = {
        "PublicIP": PublicIpAddress,
        "PrivatIP": BackEndIpAddress
    }

    script_path = os.path.dirname(os.path.abspath(__file__))
    # template_file_path = os.path.join(script_path, template_filename)
    rendered_file_path = os.path.join(script_path, rendered_filename)

    environment = jinja2.Environment(loader=jinja2.FileSystemLoader(script_path))
    output_text = environment.get_template(template_filename).render(render_vars)
    print(output_text)
    with open(rendered_file_path, "w") as result_file:
        result_file.write(output_text)

    # all done lets run next step

if __name__ == "__main__":
    # execute only if run as a script
    main()

# ./config
# ### jump server ###
# Host bastion
#     HostName 35.180.159.10
#     Port 22
#     User ec2-user
#     StrictHostKeyChecking no
#     ForwardAgent yes

# Host db
#     HostName 10.200.11.103
#     ProxyJump bastion
#     Port 22
#     User ec2-user
#     StrictHostKeyChecking no
#     ForwardAgent yes

# # inventory
# [gate]
# bastion
# [backend]
# db
# [all:vars]
# ansible_ssh_user=ec2-user
# ansible_ssh_common_args='-F config'

# ansible -i hosts db -m ping
# ssh -F config db

# 1. first way to connectg via SSH to BackEnd
# ssh_tunnel = 'ssh -o "StrictHostKeyChecking no" -f -N -L 12345:' + \
#     BackEndIpAddress + ':22 ec2-user@' + PublicIpAddress
# # ssh_tunnel1 = 'ssh -i id_rsa -o "StrictHostKeyChecking no" -p12345 ec2-user@' + PublicIpAddress
# print(ssh_tunnel)


# Jenkinsfile-create
# Jenkinsfile-deploy
# Jenkinsfile-destroy