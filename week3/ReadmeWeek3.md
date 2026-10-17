# Week 3 Runbook: EC2

This week I put PropertyLite (my little Flask API from Week 0) on a real EC2 server, took a snapshot of its disk, and then tore it all down. Here's how it went, including the part where it broke.

## Quick vocab so the rest makes sense

- **AMI**: the starting image the server boots from. I used Amazon Linux 2023.
- **Instance type**: how big the machine is. t3.micro is the Free Tier one.
- **Security group**: a firewall attached to the instance. It's stateful, so if a request is allowed in, the reply is allowed back out without me adding a rule for it.
- **NACL**: also a firewall, but it sits on the subnet and is stateless, so you have to allow traffic in both directions.
- **EBS volume**: the instance's hard drive. It's its own thing, separate from the instance.
- **User data**: a script AWS runs once, as root, the first time the instance boots. Only once. Remember that, it comes back later.

## Lab 3.1: Get PropertyLite running

### Launching it

1. In the EC2 console I hit **Launch instance** and named it `property-api-01`.
2. AMI: Amazon Linux 2023. Instance type: t3.micro.
3. Key pair: made a new one called `training-key` (RSA, `.pem`). I downloaded it immediately and moved it to `~/.ssh/training-key.pem`, because AWS won't give it to me a second time.
4. For the security group I made two inbound rules:
   - SSH on port 22, source **My IP**. Never "Anywhere" for SSH.
   - Custom TCP on port **8080**, source Anywhere. That's the port PropertyLite listens on, not port 80.
5. Under Advanced details, in **User data**, I pasted the bootstrap script. It updates the OS, installs Python and Flask 3.0.3, writes `app.py` and the sample CSV into `/opt/property-api`, and starts the app in the background with logs going to `/var/log/property-api.log`.
6. Launched it and waited for the state to say **running** and the status checks to pass.

### Connecting

```bash
chmod 400 ~/.ssh/training-key.pem
ssh -i ~/.ssh/training-key.pem ec2-user@3.135.238.134
```

If you skip the `chmod 400`, SSH refuses the key and complains the permissions are too open.

### What broke

The app wasn't running after the first boot. I looked at `/opt/property-api/app.py` on the server and it was literally just the comment `# ... (same app.py content from Week 0) ...`. I had pasted the script with the placeholder still in it instead of my real code. So the server wrote a one-line file, Python ran it, it ended immediately, and nothing was ever listening on 8080.

I also spotted that two install lines got stuck together when I copied them from the PDF (`python3-pippip3 install ...`), so copying from a PDF is not something I'll trust blindly again.

### How I fixed it

1. Checked `app.py` on the server to confirm it was only the comment.
2. From my Mac, copied the real file up:

```bash
scp -i ~/.ssh/training-key.pem propertylite/app.py ec2-user@3.135.238.134:/tmp/app.py
```

3. In the SSH tab, moved it into place and started it:

```bash
sudo cp /tmp/app.py /opt/property-api/app.py
ls /opt/property-api
sudo bash -c 'cd /opt/property-api && nohup python3 app.py > /var/log/property-api.log 2>&1 &'
curl http://localhost:8080/health
```

`ls` showed both `app.py` and `rets_property_sample.csv`, and the localhost curl gave me `{"status":"ok"}`.

**What I took from this:** user data only runs once, on first boot. Fixing the script in the console afterward does nothing for an instance that already booted. I had to fix this one by hand over SSH, and a brand new instance launched from the same broken script would fail the exact same way.

### Proving it works from outside

My first curls were run inside the SSH tab, which only proves the server can talk to itself. The real test is from my laptop, because that shows the security group actually lets the internet reach port 8080. So from my Mac terminal:

```bash
curl http://3.135.238.134:8080/health
curl http://3.135.238.134:8080/properties/R100234
```

What I got back:

```
{"status":"ok"}
{"LM_Dec_3":"2.0","LM_Int2_3":"1450","L_City":"Sacramento","L_Keyword2":"3","L_ListingID":"R100234","L_Status":"Active","L_SystemPrice":"450000"}
```

Screenshot of both working:

![Working curl responses from PropertyLite](curl-responses.png)

### So what is AWS actually doing here?

Honestly, not much. AWS gives me a computer, a public address, and a firewall. PropertyLite is just a program I started on that computer, the same way I ran `python3 app.py` on my Mac. If the process dies or the server reboots, it stays dead, because nothing is set up to restart it.

### If it ever fails again

- `cat /var/log/property-api.log` on the server shows app errors.
- `sudo cat /var/log/cloud-init-output.log` shows errors from the user data script.
- Make sure `app.py` binds to `0.0.0.0` on port 8080. If it only binds to `127.0.0.1`, the security group can be perfect and it still won't work from outside.

### Mistakes to avoid

- Forgetting `chmod 400` on the key.
- Using Anywhere instead of My IP for SSH.
- Losing the `.pem`. It's gone for good.
- Opening port 80 when the app uses 8080.

## Lab 3.2: EBS snapshot

1. EC2, then **Volumes**, and select the root volume of `property-api-01`.
2. Actions, then **Create snapshot**.
3. Wait for the status to say **completed**, and check that it shows up under **Snapshots**.

If I made a new volume from that snapshot, I'd get a copy of the disk exactly as it was when I took the snapshot. I kept the instance running until the snapshot finished.

How it went: (fill in)

## Debug Lab 3.3: SSH suddenly times out

The symptom is that `ssh` just hangs and then times out, even though it worked yesterday. Two things to check:

1. Is the instance still in the **running** state?
2. Did my laptop's public IP change? I compare `curl ifconfig.me` against the source on the SSH rule in the security group. "My IP" gets locked in when I create the rule, so if my IP changes, I'm blocked from my own server.

How it went: (fill in)

## Cleanup: terminating the instance

1. EC2, then **Instances**, and select `property-api-01`.
2. **Instance state**, then **Terminate (delete) instance**. The pop-up warns that the root volume gets deleted by default and that this can't be undone. Termination protection was off and I left Skip OS shutdown unchecked.
3. Click **Terminate (delete)**.
4. Then check the disk is really gone. This tripped me up: Volumes is not a tab on the instance page. It's in the left sidebar under **Elastic Block Store**, then **Volumes**. I made sure the region was **us-east-2** (Ohio) and refreshed. The root volume should vanish within a minute or so.
5. If a volume from this instance is still there marked **Available**, it didn't get deleted with the instance. I'd select it, then Actions, then **Delete volume**.
6. The snapshot from Lab 3.2 is separate and does not get deleted when the instance does. I'll delete it too if I don't need it, so it doesn't keep costing money.


