variable "aws_region" {
  description   = "AWS Region"
  default       = "eu-west-3"
}
variable "Environment" {
  description   = "VPC CIDR block parameter must be in the form x.x.x.x/16-28"
  default       = "PROD"
}
variable "STACK" {
  description   = "STACK TAG to describe project"
  default       = "NATGW"
}
variable "KeyName" {
  description   = "Optional key pair of the ec2-user to establish a SSH connection to the EC2 instance."
  default       = "aws-test-oregon"
}
variable "NATGW_type" {
  description   = "Instance Type for NAT GateWay."
  default       = "t2.micro"
}
variable "NATGW_ami" {
  description   = "Instance AMI for NAT GateWay in aws_region eu-west-3"
  default       = "ami-0ebb3a801d5fb8b9b"
}
variable "VPCBlock" {
  description   = "VPC CIDR block parameter must be in the form x.x.x.x/16-28"
  default       = "10.0.0.0/16"
}
variable "PublicSubnetCIDR" {
  description   = "Public Subnet CIDR"
  default       = "10.0.10.0/24"
}
variable "PrivatSubnetCIDR" {
  description   = "Privat Subnet CIDR"
  default       = "10.0.11.0/24"
}