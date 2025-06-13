provider "aws" {
  region = "eu-west-1"
  profile = "sandbox"
}
data "template_file" "user_data" {
  template = file("${path.module}/user_data.sh")
  vars = {
    db_name     = "catalog"
    db_user     = "admin"
    db_password = "admin123"
    db_url = "mysql+pymysql://admin:admin123@mysql-container:3306/catalog"
  }
}


resource "aws_instance" "catalog_server" {
  ami = "ami-028727bd3039c5a1f"
  subnet_id = aws_subnet.catalog_subnet.id
  vpc_security_group_ids = [ aws_security_group.catalog_sg.id ]
  associate_public_ip_address = true
  instance_type = "t2.nano"
  user_data = data.template_file.user_data.rendered
}   

resource "aws_vpc" "catalog_vpc" {
    cidr_block = "10.0.0.0/24"
    enable_dns_hostnames = true
    enable_dns_support = true
  
}   

resource "aws_subnet" "catalog_subnet" {
  vpc_id = aws_vpc.catalog_vpc.id
  cidr_block = "10.0.0.0/25"
  availability_zone = "eu-west-1a"
  map_public_ip_on_launch = true
}

resource "aws_security_group" "catalog_sg" {
  name = "Catalog sg"
  description = "Catalog Sg"
  vpc_id = aws_vpc.catalog_vpc.id

  ingress {
    from_port = 80
    to_port = 80
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    "name" = "catalog sg"
  }
}

resource "aws_internet_gateway" "catalog_igw" {
  vpc_id = aws_vpc.catalog_vpc.id

  tags = {
    "name" = "catalog_igw"
  }
}

resource "aws_route_table" "catalog_route_table" {
  vpc_id = aws_vpc.catalog_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.catalog_igw.id
  }
}

resource "aws_route_table_association" "publc_subnet_association" {
  subnet_id = aws_subnet.catalog_subnet.id
  route_table_id = aws_route_table.catalog_route_table.id
}

output "instance_public_Ip" {
  value = "http://${aws_instance.catalog_server.public_ip}"
}