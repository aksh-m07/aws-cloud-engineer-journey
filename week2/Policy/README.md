# IAM Policy Types

A policy is a JSON document that says which actions are allowed or denied on which resources.

## Identity-based vs resource-based

### Identity-based policy

Attached to a user, group, or role. It answers what can this identity do?

### Resource-based policy

Attached to a resource, such as an S3 bucket. It answers: who can use this resource? It has a `Principal` field that names who the rule applies to.


## Managed vs inline

### AWS managed policy

Created and maintained by AWS, for example `AmazonS3ReadOnlyAccess`.

### Customer managed policy

Written by us. It can be attached to many users, groups, or roles, and it keeps version history.

### Inline policy

Written directly inside one user, group, or role. It belongs to that identity only, cannot be reused, and is deleted with the user

## How they combine

A single policy has one answer from each group. For example, `S3UploaderOnly-Aksh` is a customer managed, identity-based policy.

## Evaluation order

1. Everything starts as denied (default deny).
2. If any matching policy has an explicit Deny, the request is denied.
3. Otherwise, if a matching policy has an Allow, the request is allowed.
4. If nothing matches, it stays denied.
