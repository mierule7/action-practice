variable "environment" {
  type        = string
  description = "dev, uat or prod"

  validation {
    condition     = contains(["dev", "uat", "prod"], var.environment)
    error_message = "environment must be dev, uat or prod."
  }
}

variable "build_id" {
  type        = string
  description = "Image tag to deploy, for example 12"
}

variable "image_repo" {
  type        = string
  description = "Image name without the tag"
  default     = "ghcr.io/<your-username>/action-practice"
}

variable "docker_host" {
  type        = string
  description = "Leave null to use the default Docker connection"
  default     = null
}