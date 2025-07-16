# Maintenance and Dependency Updates

This project uses **GitHub Dependabot** to automatically propose updates for
Python, JavaScript and GitHub Actions dependencies. Dependabot checks for new
releases weekly and opens pull requests.

## Reviewing updates

- Ensure CI passes and verify that regression tests cover the change.
- Apply code formatting with `pre-commit` before merging.
- Merge security fixes promptly after tests succeed.

## Manual updates

For urgent updates run the appropriate package manager commands and open a pull
request with accompanying regression tests.
