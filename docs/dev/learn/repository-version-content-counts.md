# Repository-version content counts

Content-listing requests filtered by a completed repository version can use the
persisted repository-version summary for the pagination `count` value.

This applies when the request contains only repository-version selection and
pagination/field parameters:

- `repository_version`, `repository_version_added`, or `repository_version_removed`
- `limit`, `offset`, `ordering`, and `fields`

Requests with content filters use the normal exact database count. The response
format is unchanged.
