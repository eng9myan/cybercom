variable "compartment_id" {
  description = "OCID of the OCI compartment to provision into. Account-specific -- no sensible default."
  type        = string
}

variable "availability_domain" {
  description = "OCI availability domain name (e.g. \"abCD:AP-SINGAPORE-1-AD-1\"), as shown by `oci iam availability-domain list`."
  type        = string
}

variable "subnet_id" {
  description = "OCID of an existing subnet with internet access (a NAT/internet gateway already attached) for the instance's VNIC."
  type        = string
}

variable "image_id" {
  description = "OCID of the boot image (an Ubuntu 22.04 or later OCI platform image for the chosen shape's architecture)."
  type        = string
}

variable "shape" {
  description = "OCI compute shape."
  type        = string
  default     = "VM.Standard.A1.Flex"
}

variable "shape_ocpus" {
  description = "OCPUs, only used for Flex shapes."
  type        = number
  default     = 2
}

variable "shape_memory_gbs" {
  description = "Memory in GB, only used for Flex shapes."
  type        = number
  default     = 12
}

variable "ssh_public_key" {
  description = "SSH public key installed for the default (ubuntu) user."
  type        = string
}

variable "environment_name" {
  description = "Short, unique name for this ephemeral environment (e.g. a branch slug or tenant slug: \"pr-482\", \"acme-staging\"). Used to name/tag every resource -- keep it DNS-safe (lowercase, digits, hyphens)."
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{0,40}$", var.environment_name))
    error_message = "environment_name must be lowercase alphanumeric/hyphens, starting with a letter or digit, max 41 chars."
  }
}

variable "app" {
  description = "Which app this environment runs: cymed or cycom. Selects the Dockerfile/compose file the bootstrap script deploys."
  type        = string
  validation {
    condition     = contains(["cymed", "cycom"], var.app)
    error_message = "app must be \"cymed\" or \"cycom\"."
  }
}

variable "git_ref" {
  description = "Git ref (branch, tag or commit SHA) the bootstrap script checks out and deploys."
  type        = string
  default     = "develop"
}

variable "repo_url" {
  description = "Git remote the bootstrap script clones. Defaults to the public GitHub remote; override for a private fork or an SSH deploy-key URL."
  type        = string
  default     = "https://github.com/eng9myan/cybercom.git"
}
