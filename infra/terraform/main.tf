# Remote state on Terraform Cloud free tier.
# Prerequisite: `terraform login` once on this machine (stores API token).
terraform {
  cloud {
    organization = "BulkHead"
    workspaces {
      name = "bulkhead-demo"
    }
  }
}

terraform {
  required_version = ">= 1.9"
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

provider "oci" {
  # reads ~/.oci/config by default — no secrets in this file
}

variable "compartment_id" {
  description = "OCID of the compartment to deploy into (tenancy root OCID is fine for a solo project)"
  type        = string
}

variable "my_ip" {
  description = "Your public IPv4 — SSH/k3s-API ingress is restricted to it"
  type        = string
}

variable "ssh_public_key_path" {
  default = "~/.ssh/id_ed25519.pub"
}

variable "instance_ocpus" {
  default = 4
}

variable "instance_memory_gbs" {
  # Always Free cap: 4 OCPU + 24 GB total across all A1 instances
  default = 24
}

resource "oci_core_vcn" "main" {
  compartment_id = var.compartment_id
  cidr_blocks    = ["10.0.0.0/16"]
  display_name   = "bulkhead-vcn"
}

resource "oci_core_internet_gateway" "main" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.main.id
  display_name   = "bulkhead-igw"
}

resource "oci_core_route_table" "main" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.main.id
  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_internet_gateway.main.id
  }
}

# No public 443 needed: Cloudflare Tunnel connects outbound from the VM,
# so the demo URL works without any inbound web ports.
resource "oci_core_security_list" "main" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.main.id

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "${var.my_ip}/32"
    tcp_options {
      min = 22
      max = 22
    } # SSH
  }
  ingress_security_rules {
    protocol = "6"
    source   = "${var.my_ip}/32"
    tcp_options {
      min = 6443
      max = 6443
    } # k3s API (remote kubeconfig)
  }
  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }
}

resource "oci_core_subnet" "main" {
  compartment_id             = var.compartment_id
  vcn_id                     = oci_core_vcn.main.id
  cidr_block                 = "10.0.1.0/24"
  route_table_id             = oci_core_route_table.main.id
  security_list_ids          = [oci_core_security_list.main.id]
  display_name               = "bulkhead-subnet"
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}

data "oci_core_images" "ubuntu" {
  compartment_id           = var.compartment_id
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "24.04"
  shape                    = "VM.Standard.A1.Flex"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

resource "oci_core_instance" "vm" {
  compartment_id      = var.compartment_id
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  shape               = "VM.Standard.A1.Flex"

  shape_config {
    ocpus         = var.instance_ocpus
    memory_in_gbs = var.instance_memory_gbs
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.main.id
    assign_public_ip = true
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.ubuntu.images[0].id
  }

  metadata = {
    ssh_authorized_keys = file(pathexpand(var.ssh_public_key_path))
  }

  display_name = "bulkhead-demo"
}

output "instance_public_ip" {
  value = oci_core_instance.vm.public_ip
}
