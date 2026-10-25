# Week 4 Decision Guide: AWS Storage and Database Options

| Service | Type | Best for | Use this when... |
|---|---|---|---|
| S3 | Object storage | Files, backups, logs, static assets, data lakes | You need cheap, durable storage for files or objects that are accessed over HTTP or the API, not mounted as a disk. |
| EBS | Block storage | Boot volumes, databases running on EC2 | You need a fast disk attached to a single EC2 instance, like an OS volume or a self-managed database. |
| EFS | Shared file system (NFS) | Content shared across servers | You need many EC2 instances to read and write the same files at once through a mounted file system. |
| RDS | Managed relational database | Structured data with SQL, joins, transactions | Your data is relational and you need SQL, joins, and ACID transactions without managing the database server yourself. |
| DynamoDB | Managed NoSQL key-value store | Key-based lookups at huge scale | You need single-digit millisecond lookups by key at any scale, with a predictable access pattern and no servers to manage. |

## Quick decision rules

- Storing files or objects? Use **S3**.
- Need a disk for one server? Use **EBS**.
- Need a disk shared by many servers? Use **EFS**.
- Need SQL and relationships between tables? Use **RDS**.
- Need massive scale with simple key-based access? Use **DynamoDB**.
