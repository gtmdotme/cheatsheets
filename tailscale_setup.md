# Oracle Cloud Free Tier + Tailscale Exit Node Setup

> **IMPORTANT:** When signing up for Oracle Cloud, **select `Mumbai` as your region**. This CANNOT be changed later.

## What You'll Do

1. Sign up for a **free Oracle Cloud** account
2. Launch a **Ubuntu VM** under the Always Free Tier
3. SSH into the VM
4. Install **Tailscale** and configure it as an **exit node**
5. Connect your **laptop and Android** to route traffic via this node
6. (Optional) Lock down SSH access for better security

---

## 1. Sign Up for Oracle Cloud

- Go to: [https://www.oracle.com/cloud/free/](https://www.oracle.com/cloud/free/)
- Use a valid (personal) email and credit card (for verification only — **no charges**). If you're a student at a US university, then use the US address and a US credit card.
- **Select `Mumbai` as your region** during signup (even though you had put a US address)
- Complete verification and login

---

## 2. Create an Ubuntu VM

1. Navigate to **Compute > Instances** → Click **Create Instance**
2. Name: `tailscale-exit-node` (or anything of your choice)
3. Compartment: default is fine
4. Under "Image and Shape":
   - Image: **Canonical Ubuntu** (e.g., Ubuntu 20.04)
   - Shape: Choose **Always Free-eligible**: `VM.Standard.A1.Flex` or `VM.Standard.E2.1.Micro`
5. Networking:
   - Leave VCN defaults, i.e., either create VCN and subnets if first time, or use existing ones
   - Ensure "Assign public IPv4 address" is enabled
6. SSH Key:
   - Generate/upload SSH key pair
   - Save both **private** and **public** keys securely
7. Click **Create** and wait for provisioning

---

## 3. SSH into the VM

### macOS/Linux:
```bash
chmod 400 path/to/private_key.pem
ssh -i path/to/private_key.pem ubuntu@<your_vm_public_ip>
```

### Windows:
- Convert `.pem` to `.ppk` using **PuTTYgen**
- In **PuTTY**:
  - Host: `ubuntu@<your_vm_public_ip>`
  - Auth > Private key: select `.ppk` file
  - Connect and accept any warnings

---

## 4. Install & Configure Tailscale on the VM

### Install:
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```
- Log in via the URL shown in the terminal

### Advertise as Exit Node:
```bash
sudo tailscale set --advertise-exit-node
```

### Enable IP Forwarding:
```bash
echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf
```

- In [Tailscale Admin Console](https://login.tailscale.com/admin/machines), find your VM and **enable "Use as Exit Node"**

---

## 5. Setup Tailscale on Laptop

1. Download and install Tailscale client for your OS: [https://tailscale.com/download](https://tailscale.com/download)
2. Log in with the **same account** as the VM
3. In the Tailscale menu:
   - Choose **Exit Node** → select your Oracle VM

---

## 6. Setup Tailscale on Android

1. Install the Tailscale app from Google Play Store
2. Log in with the same account
3. Open app menu → **Exit Node** → select your Oracle VM

---

## 7. (Bonus) Restrict SSH Access to Tailscale

1. On VM, get your Tailscale IP:
```bash
tailscale ip -4
```

2. In Oracle Console:
   - Go to **Virtual Cloud Network > Security Lists**
   - Edit the default Security List
   - Add a new ingress rule:
     - Source CIDR: `100.x.x.x/32` (your Tailscale IP)
     - Protocol: TCP
     - Port Range: 22

3. Delete the existing SSH rule for `0.0.0.0/0`

Now, only you (via Tailscale) can SSH into the VM.

## 8. Re-authenticate upon key expiry

We can periodically re-authenticate the tailscale setup on the servers by SSH-ing into them and typing:
```bash
tailscale up --force-reauth --advertise-exit-node
```
One may also choose to 'Disable Key Expiry' through admin console in tailscale for trusted devices.

---

## ✅ Done!
You now have a secure, free, and private exit node using Oracle and Tailscale.

Enjoy! 🔒🚀
