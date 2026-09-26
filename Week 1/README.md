
The root user is the owner of my AWS account, tied to the email I signed up
with, and it has unlimited power that no policy can restrict.

An IAM user is an identity I created inside the account (Aksh-admin), and it can
only do what the policies attached to it allow

The Shared Responsibility Model splits security between AWS and me: AWS secures
the cloud itself such as  the physical data centers, hardware, network, and the
virtualization layer. I am responsible for security in the cloud, meaning who
can log in, what permissions they have, my data, and how I configure services,
