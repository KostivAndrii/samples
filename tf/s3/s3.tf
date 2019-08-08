terraform {
    required_version = ">= 0.8"
}

provider "aws" {
    region = "eu-west-3"
}
resource "aws_s3_bucket" "terraform-state-storage-s3" {
    bucket = "tfstate-aws-s3-bucket"
    versioning {
      enabled = true
    }
    lifecycle {
      prevent_destroy = true
    }
    tags = {
      Name = "S3 Remote Terraform State Store"
    }
}
resource "aws_dynamodb_table" "dynamodb-terraform-state-lock" {
  name           = "terraform-state-lock-dynamo"
  read_capacity  = 1
  write_capacity = 1
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
  tags = {
    Name = "DynamoDB Terraform State Lock Table"
  }

}
