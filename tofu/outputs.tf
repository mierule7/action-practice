output "url" {
  value = "http://localhost:${local.host_ports[var.environment]}"
}

output "host_port" {
  value = local.host_ports[var.environment]
}