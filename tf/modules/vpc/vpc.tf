terraform {
    required_version = ">= 0.8"
}

provider "aws" {
    region = "${var.aws_region}"
}

resource "aws_vpc" "main" {
    cidr_block = "${var.VPCBlock}"

    tags = {
        Name     = "${var.Environment}-vpc"
    }
}
# Internet Gateway
resource "aws_internet_gateway" "igw" {
    vpc_id = "${aws_vpc.main.id}"

    tags = {
        Name     = "${var.Environment}-IGW"
    }
}
#==================================================== Public Subnet =========
resource "aws_subnet" "public_subnet" {
    vpc_id     = "${aws_vpc.main.id}"
    cidr_block = "${var.PublicSubnetCIDR}"

    tags = {
        Name = "${var.Environment}-public_subnet"
    }
}
#====== Public RouteTables ========= Routes for Public Subnet RouteTables with IGW =========
resource "aws_route_table" "public_route" {
    vpc_id = "${aws_vpc.main.id}"
    tags = {
        Name = "${var.Environment}-PublicRouteTables"
    }

    route {
        cidr_block = "0.0.0.0/0"
        gateway_id = "${aws_internet_gateway.igw.id}"
    }
}
resource "aws_route_table_association" "public_route_assoc" {
    subnet_id = "${aws_subnet.public_subnet.id}"
    route_table_id = "${aws_route_table.public_route.id}"
}
#==================================================== Privat Subnet =========
resource "aws_subnet" "privat_subnet" {
    vpc_id     = "${aws_vpc.main.id}"
    cidr_block = "${var.PrivatSubnetCIDR}"

    tags = {
        Name = "${var.Environment}-privat_subnet"
    }
}
#====== Privat RouteTables ========= Routes for Privat Subnet RouteTables with NATGW =========
resource "aws_default_route_table" "privat_route" {
    default_route_table_id = "${aws_vpc.main.default_route_table_id}"
    tags = {
        Name = "${var.Environment}-PrivatRouteTables"
    }

    route {
        cidr_block = "0.0.0.0/0"
        # gateway_id = "${aws_internet_gateway.igw.id}"
        instance_id = "${aws_instance.NATGWInstance.id}"
    }
    depends_on = ["aws_instance.NATGWInstance"]
}
resource "aws_route_table_association" "privat_route_assoc" {
    subnet_id = "${aws_subnet.privat_subnet.id}"
    route_table_id = "${aws_default_route_table.privat_route.id}"
}
#====== NAT GW SecurityGroup
resource "aws_default_security_group" "NATGW_sg" {
    # aws_default_security_group
    # name = "natgw_sg"
    tags = {
        Name = "${var.Environment}-natgw_sg"
    }
    # description = "Connections for the nat instance"
    vpc_id = "${aws_vpc.main.id}"
    ingress {
        from_port   = "0"
        to_port     = "0"
        protocol    = "-1"
        cidr_blocks = ["${var.VPCBlock}"]
    }
    ingress {
        from_port   = "22"
        to_port     = "22"
        protocol    = "TCP"
        cidr_blocks = ["0.0.0.0/0"]
    }
    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }
}
#====== NAT GW instance
resource "aws_instance" "NATGWInstance" {
    ami = "${var.NATGW_ami}"
    instance_type = "${var.NATGW_type}"
    associate_public_ip_address = "true"
    key_name = "${var.KeyName}"

    subnet_id = "${aws_subnet.public_subnet.id}"
    vpc_security_group_ids = ["${aws_default_security_group.NATGW_sg.id}"]
    source_dest_check = "false"
    user_data = <<-EOF
                #!/bin/bash -xe
                #sed -i "s/net.ipv4.ip_forward = 0/net.ipv4.ip_forward = 1/" /etc/sysctl.conf
                echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.conf
                sysctl -p
                echo "iptables -t nat -A POSTROUTING -s ${var.VPCBlock} -j MASQUERADE" >> /etc/rc.local
                iptables -t nat -A POSTROUTING -s ${var.VPCBlock} -j MASQUERADE
                EOF
    tags = {
        STACK = "${var.STACK}"
        Name = "${var.Environment}-NATGW"
        VM = "NATGW"
    }
}
#====== Public SecurityGroup
resource "aws_security_group" "public_sg" {
    name = "public_sg"
    tags = {
        Name = "${var.Environment}-public_sg"
    }
    description = "Connections for the nat instance"
    vpc_id = "${aws_vpc.main.id}"
    ingress {
        from_port   = "80"
        to_port     = "80"
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }
    ingress {
        from_port   = "8080"
        to_port     = "8080"
        protocol    = "TCP"
        cidr_blocks = ["0.0.0.0/0"]
    }
    ingress {
        from_port   = "1050"
        to_port     = "1052"
        protocol    = "TCP"
        cidr_blocks = ["0.0.0.0/0"]
    }
    ingress {
        from_port   = "12345"
        to_port     = "12345"
        protocol    = "TCP"
        cidr_blocks = ["0.0.0.0/0"]
    }
    ingress {
        from_port   = "0"
        to_port     = "0"
        protocol    = "-1"
        cidr_blocks = ["${var.VPCBlock}"]
    }
    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }
}
