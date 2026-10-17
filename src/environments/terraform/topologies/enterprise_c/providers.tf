terraform {
  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "1.54.1"
    }
  }
}

# Password auth (username/password/project) or application credential auth
# (id/secret) must be provided. Application credentials take precedence.
variable "project_name" {
  type        = string
  description = "Openstack project"
  default     = null
}

variable "openstack_username" {
  type        = string
  description = "Openstack username"
  default     = null
}

variable "openstack_password" {
  type        = string
  description = "Openstack password"
  default     = null
  sensitive   = true
}

variable "application_credential_id" {
  type        = string
  description = "Openstack application credential ID"
  default     = null
}

variable "application_credential_secret" {
  type        = string
  description = "Openstack application credential secret"
  default     = null
  sensitive   = true
}

variable "openstack_auth_url" {
  type        = string
  description = "Openstack auth url"
}

variable "openstack_region" {
  type        = string
  description = "Openstack region"
}

variable "perry_key_name" {
  type        = string
  description = "Name of the keypair to use for the Perry instance"
}

variable "host_flavor" {
  type        = string
  description = "Flavor for target hosts"
  default     = "p2.tiny"
}

variable "manage_flavor" {
  type        = string
  description = "Flavor for the management host"
  default     = "m1.small"
}

variable "attacker_flavor" {
  type        = string
  description = "Flavor for the attacker host"
  default     = "m1.small"
}

variable "external_network" {
  type        = string
  description = "Name of the provider network used for the router gateway and floating IPs"
  default     = "external"
}

locals {
  use_app_cred = var.application_credential_id != null
}

# Configure the OpenStack Provider
provider "openstack" {
  user_name                     = local.use_app_cred ? null : var.openstack_username
  tenant_name                   = local.use_app_cred ? null : var.project_name
  password                      = local.use_app_cred ? null : var.openstack_password
  application_credential_id     = var.application_credential_id
  application_credential_secret = var.application_credential_secret
  auth_url                      = var.openstack_auth_url
  region                        = var.openstack_region
  insecure                      = "true"
}
