terraform {
  required_version = ">= 1.6.0"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {
  host = var.docker_host
}

locals {
  host_ports = {
    dev  = 8081
    uat  = 8082
    prod = 8083
  }
}

resource "docker_image" "app" {
  name         = "${var.image_repo}:${var.build_id}"
  keep_locally = true
}

resource "docker_container" "app" {
  name    = "calc-${var.environment}"
  image   = docker_image.app.image_id
  env     = ["APP_ENV=${var.environment}"]
  restart = "unless-stopped"

  ports {
    internal = 8000
    external = local.host_ports[var.environment]
  }
}