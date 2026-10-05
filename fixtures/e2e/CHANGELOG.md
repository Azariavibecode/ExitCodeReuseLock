# Changelog

## Version 2.0

Breaking CLI contract: exit code 7 now means that the local configuration file is missing. Authentication rejection moved from exit code 7 to exit code 19. Automation that branches on status 7 must be updated.
