output "vpc_id" {
    description = ""
    value       = "${aws_vpc.main.id}"
}
output "privat_security_group_id" {
    description = ""
    value       = "${aws_default_security_group.NATGW_sg.id}"
}       
output "public_security_group_id" {
    description = ""
    value       = "${aws_security_group.public_sg.id}"
}       
output "public_subnet_id" {
    description = ""
  value = "${aws_subnet.public_subnet.id}"
}
output "privat_subnet_id" {
  value = "${aws_subnet.privat_subnet.id}"
}
output "NATGW_IP" {
  value = "${aws_instance.NATGWInstance.*.public_ip}"
}