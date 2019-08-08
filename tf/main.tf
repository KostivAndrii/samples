terraform {
    required_version = ">= 0.8"
}

provider "aws" {
    region = "${var.aws_region}"
}
module "vpc" {
    source                              = "./modules/vpc"
    aws_region     	                    = "${var.aws_region}"
    STACK                               = "${var.STACK}"
    Environment                         = "${var.Environment}"
    KeyName                             = "${var.KeyName}"
    NATGW_type                          = "${var.NATGW_type}"
    NATGW_ami                           = "${var.NATGW_ami}"
    VPCBlock                            = "${var.VPCBlock}"
    PublicSubnetCIDR                    = "${var.PublicSubnetCIDR}"
    PrivatSubnetCIDR                    = "${var.PrivatSubnetCIDR}"
    # enable_dns_support                  = "true"
    #Internet-GateWay
    # enable_internet_gateway             = "true"
    #NAT
    # enable_nat_gateway                  = "false"
}
#====== S3 backend tfstate
terraform {
    backend "s3" {
        encrypt = true
        bucket = "tfstate-aws-s3-bucket"
        region = "eu-west-3"
        key = "natgw/terraform.tfstate"
        dynamodb_table = "terraform-state-lock-dynamo"
    }
}

#====== BackEnd instance
resource "aws_instance" "BackEndInstance" {
    ami = "${var.server_ami}"
    instance_type = "${var.server_type}"
    key_name = "${var.KeyName}"

    subnet_id = "${module.vpc.privat_subnet_id}"
    vpc_security_group_ids = ["${module.vpc.privat_security_group_id}"]
    tags = {
        STACK = "${var.STACK}"
        Name = "${var.Environment}-BackEnd"
        VM = "BackEnd"
    }
}
#====== Public Servers ====== Tomcat instance
resource "aws_instance" "TomcatInstance" {
    ami = "${var.server_ami}"
    instance_type = "${var.server_type}"
    associate_public_ip_address = "true"
    key_name = "${var.KeyName}"

    subnet_id = "${module.vpc.public_subnet_id}"
    vpc_security_group_ids = ["${module.vpc.public_security_group_id}"]
    tags = {
        STACK = "${var.STACK}"
        Name = "${var.Environment}-Tomcat"
        VM = "Tomcat"
    }
}
#====== Tomcat instance
resource "aws_instance" "ZabbixInstance" {
    ami = "${var.server_ami}"
    instance_type = "${var.server_type}"
    associate_public_ip_address = "true"
    key_name = "${var.KeyName}"

    subnet_id = "${module.vpc.public_subnet_id}"
    vpc_security_group_ids = ["${module.vpc.public_security_group_id}"]
    tags = {
        STACK = "${var.STACK}"
        Name = "${var.Environment}-Zabbix"
        VM = "Zabbix"
    }
}
# terraform apply -var-file=vpc.tfvars
