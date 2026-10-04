output "instance_id" {
  value       = oci_core_instance.this.id
  description = "OCID of the provisioned instance — pass to `terraform destroy -target` or record for teardown."
}

output "public_ip" {
  value       = oci_core_instance.this.public_ip
  description = "Public IP of the ephemeral environment. The app is reachable at http://<public_ip>:8000/ once cloud-init finishes (first boot takes several minutes — Docker install + image build)."
}

output "environment_name" {
  value = local.env_name
}
