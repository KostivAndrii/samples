variable "aws_region" {
  description = "AWS Region"
}
variable "Environment" {
  description = "VPC CIDR block parameter must be in the form x.x.x.x/16-28"
}
variable "STACK" {
  description = "STACK TAG to describe project"
}
variable "KeyName" {
  description = "Optional key pair of the ec2-user to establish a SSH connection to the EC2 instance."
}
variable "NATGW_type" {
  description = "Instance Type for NAT GateWay."
}
variable "NATGW_ami" {
  description = "Instance AMI for NAT GateWay in aws_region eu-west-3"
}
variable "server_type" {
  description = "Instance Type for NAT GateWay."
}
variable "server_ami" {
  description = "Instance AMI for NAT GateWay in aws_region eu-west-3"
}
variable "VPCBlock" {
  description = "VPC CIDR block parameter must be in the form x.x.x.x/16-28"
}
variable "PublicSubnetCIDR" {
  description = "Public Subnet CIDR"
}
variable "PrivatSubnetCIDR" {
  description = "Privat Subnet CIDR"
}
