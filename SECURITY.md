# Security policy

## Supported versions

This is a prototype with no tagged releases. Only the latest commit on
`main` receives fixes.

## Reporting a vulnerability

Please do not open a public issue for a security problem. Email
tahmidbintaslimrafi@gmail.com with:

- A description of the issue and its impact
- Steps to reproduce, or a proof of concept
- The commit you tested

There is no fixed response time for this small project. Once an issue is
confirmed, the fix lands on `main`.

## Known weak points by design

The stack is meant to run on one machine, and the README says so. These are
known and documented, so they are not vulnerabilities on their own:

- PostgreSQL uses the placeholder login `user` / `password`.
- The chat page and the sensor API have no authentication.
- In Docker Compose, every host port is bound to `127.0.0.1`. Started
  directly with `python -m`, the API and the chat page listen on `0.0.0.0`,
  so keep them behind a firewall.

Reports that show one of these exposed beyond localhost by the default
configuration, or any leak of the Azure OpenAI key, are in scope.
