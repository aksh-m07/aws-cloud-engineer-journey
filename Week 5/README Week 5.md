# Week 5: Custom VPC, Public/Private Subnets, NAT Gateway, Bastion Host

![VPC diagram](vpc-diagram.png)

## Goal

Build a custom VPC by hand in the console, then reach an EC2 instance that has **no public IP** by going through a bastion host, and confirm that instance can still reach the internet outbound through a NAT Gateway.

## What I built (region us-east-2)

| Resource | Name | Details |
|---|---|---|
| VPC | `training-vpc` | `10.0.0.0/16` |
| Public subnet 1 | `training-subnet-public1-us-east-2a` | `10.0.0.0/20` |
| Public subnet 2 | `training-subnet-public2-us-east-2b` | `10.0.16.0/20` (unused) |
| Private subnet 1 | `training-subnet-private1-us-east-2a` | `10.0.128.0/20` (unused) |
| Private subnet 2 | `training-subnet-private2-us-east-2b` | `10.0.144.0/20` |
| Internet Gateway | `training-igw` | Attached to `training-vpc` |
| NAT Gateway | `training-nat` | Zonal, in public subnet 1, with an Elastic IP |
| Bastion host | `bastion` | t3.micro, public subnet 1, private IP `10.0.0.232` + auto-assigned public IP |
| Private instance | `private-server` | t3.micro, private subnet 2, private IP `10.0.154.238`, no public IP |
| S3 gateway endpoint | (wizard default) | Lets private subnets reach S3 without the internet |

### Route tables

| Route table | Destination | Target |
|---|---|---|
| `training-rtb-public` (both public subnets) | `10.0.0.0/16` | `local` |
| | `0.0.0.0/0` | Internet Gateway |
| `training-rtb-private1-us-east-2a` | `10.0.0.0/16` | `local` |
| | `0.0.0.0/0` | NAT Gateway |
| | S3 prefix list | S3 gateway endpoint |
| `training-rtb-private2-us-east-2b` | `10.0.0.0/16` | `local` |
| | `0.0.0.0/0` | NAT Gateway |
| | S3 prefix list | S3 gateway endpoint |

### Security groups

| Security group | Attached to | Inbound rule |
|---|---|---|
| `bastion-sg` | bastion | SSH (22) from **My IP** (`/32`) only |
| `private-sg` | private-server | SSH (22) from **`bastion-sg`** (a security group reference, not an IP) |

## Traffic path: laptop to private instance

Commands, run from my Mac:

```bash
ssh-add ~/.ssh/week5.pem                                   # load key into the SSH agent
ssh -A -i ~/.ssh/week5.pem ec2-user@<bastion-public-ip>    # hop 1
ssh ec2-user@10.0.154.238                                  # hop 2, run inside the bastion
```

### Hop 1: laptop → bastion

1. My laptop sends an SSH connection (TCP port 22) over the internet to the bastion's **public IP**.
2. The traffic enters the VPC through the **Internet Gateway**, which maps the bastion's public IP to its private IP `10.0.0.232`.
3. The packet is delivered inside public subnet 1. That subnet is "public" only because `training-rtb-public` has `0.0.0.0/0 → IGW`, which is also the route the bastion's replies use to get back to my laptop.
4. **`bastion-sg`** checks the source: port 22 from my IP? Allowed. Any other IP is silently dropped.
5. The bastion verifies my identity with the `week5` key pair, and I get a shell on `ip-10-0-0-232`.

### Hop 2: bastion → private instance

6. From the bastion I SSH to `10.0.154.238`. That address is inside `10.0.0.0/16`, so the **`local` route** delivers it directly within the VPC. It never touches the Internet Gateway or the NAT Gateway.
7. **`private-sg`** checks the source: is it coming from an instance in `bastion-sg`? Yes, so it's allowed. Anything else is dropped.
8. The private instance asks for my key. Because I connected with `ssh -A` (**agent forwarding**), the bastion passes that challenge back to my laptop's SSH agent, which answers it. The private key file never leaves my Mac and is never copied onto the bastion.
9. I get a shell on `ip-10-0-154-238`.

### Why I can't SSH to the private instance directly

The private instance has no public IP, and `10.0.x.x` addresses are not routable on the public internet. Its route table also has no inbound path from the Internet Gateway. Running `ssh -i ~/.ssh/week5.pem ec2-user@10.0.154.238` from my laptop times out, which is the expected result.

## Traffic path: private instance to the internet (outbound only)

1. The private instance sends a request to a public address (for example `aws.amazon.com`).
2. `training-rtb-private2-us-east-2b` matches `0.0.0.0/0 → NAT Gateway`.
3. The NAT Gateway (in public subnet 1) replaces the source address `10.0.154.238` with its own **Elastic IP**.
4. `training-rtb-public` sends it on via `0.0.0.0/0 → IGW` to the internet.
5. The response comes back to the NAT's Elastic IP, and the NAT forwards it to the private instance.

Connections can only **start** from inside. Nobody on the internet can open a connection to the private instance through the NAT.

## Verification

| Check | Command | Result |
|---|---|---|
| Landed on the private instance | (shell prompt) | `[ec2-user@ip-10-0-154-238 ~]$` |
| Outbound internet via NAT | `curl -m 10 -I https://aws.amazon.com` | `HTTP/2 200` |
| Private instance unreachable directly | `ssh` from laptop to `10.0.154.238` | Times out (expected) |

## Issues I hit and how I fixed them

**1. SSH to the bastion timed out**

- **Cause:** the first bastion was launched into `training-subnet-private2-us-east-2b`. It had a public IP, but that subnet's route table has no route to the Internet Gateway, so traffic had no way in.
- **Fix:** terminated it and relaunched in `training-subnet-public1-us-east-2a`, with auto-assign public IP **enabled** and the existing `bastion-sg` reused (so `private-sg`'s rule still pointed at the right group).
- **Gotchas found while relaunching:** the launch wizard defaults to the **default VPC** (`172.31.0.0/16`), and switching to `training-vpc` reset auto-assign public IP back to **Disable**.
- **Lesson:** a public IP alone does not make an instance reachable. The subnet's route table must have `0.0.0.0/0 → IGW`.

**2. `curl` from the private instance timed out**

- **Cause:** no NAT Gateway existed, and the private route tables had no `0.0.0.0/0` route at all (only `local` and the S3 endpoint).
- **Fix:** created a **zonal** NAT Gateway (`training-nat`) in public subnet 1 with an Elastic IP, then added `0.0.0.0/0 → nat-...` to both private route tables. `curl` then returned `HTTP/2 200`.
- **Lesson:** the NAT must live in a **public** subnet, and it does nothing until a route table points traffic at it.

## Key takeaways

- A subnet is public or private purely because of its **route table**, not a setting on the subnet.
- **Internet Gateway** = two-way door for resources with public IPs. **NAT Gateway** = outbound-only door for private resources.
- Security group rules that reference **another security group** are more robust than IP rules, because they keep working if the bastion is replaced or its IP changes.
- **Agent forwarding (`ssh -A`)** is safer than copying a private key onto the bastion.
- In production: one NAT Gateway per AZ for high availability, and teams often replace bastions with **SSM Session Manager** or **EC2 Instance Connect Endpoint** so no port 22 is open at all.

## Cleanup (NAT Gateway bills hourly)

1. Terminate `bastion` and `private-server`
2. VPC → NAT gateways → delete `training-nat`
3. VPC → Elastic IPs → release the NAT's Elastic IP (an unattached Elastic IP also costs money)
4. Optional: delete `training-vpc` if it won't be reused next week
