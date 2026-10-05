# Acme CLI exit codes

## EXIT CODE 7: Authentication rejected

The command exits with code 7 when the remote service rejects the supplied credentials. The operator must replace or refresh the credential before running the command again. Retrying the identical credential is not recommended because the condition is persistent until credentials change.
