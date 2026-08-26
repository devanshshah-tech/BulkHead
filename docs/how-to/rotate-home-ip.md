# Rotate your home IP in the OCI security rules

The demo VM's firewall only allows SSH (22) and the k3s API (6443) from your current public IPv4. When your ISP changes your IP, `ssh ubuntu@<vm-ip>` starts timing out. Fix it without touching the VM.

## Steps

1. Find your new IP:

   ```bash
   curl -4 ifconfig.me
   ```

2. Edit `infra/terraform/terraform.tfvars`:

   ```hcl
   my_ip = "<new-ip>"
   ```

3. Reconcile — only the security list changes:

   ```bash
   cd infra/terraform && terraform apply
   ```

Done. If you use the one-command path, `mise run deploy:demo` applies this automatically before waiting on ArgoCD.

## Troubleshooting

- **Still locked out?** Your router may be behind CGNAT; confirm the IP you see matches what `terraform plan` shows diffing.
- **Need emergency access?** Use the OCI Console's Cloud Shell → instance serial console connection.
