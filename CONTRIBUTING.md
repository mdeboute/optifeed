# Contributing to the Project

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new Pull Request.

## Coding Rules

To ensure consistency throughout the source code, keep these rules in mind as you are working:

* All features or bug fixes **must be tested** by one or more specs (unit-tests).
* All public API methods **must be documented**.
* Don't push code that are not working, that are not tested or that are in comments.

## Commit Message Format

*This specification is inspired by and supersedes the [AngularJS commit message format](https://docs.google.com/document/d/1QrDFcIiPjSLDn3EL15IJygNPiHORgU1_OOAqWjiDU5Y/edit#).*

We have very precise rules over how our Git commit messages must be formatted.
This format leads to **easier to read commit history**.

Each commit message consists of a **header**.

The `header` must conform to the [Commit Message Header](#commit-message-header) format below.

Any line of the commit message cannot be longer than 100 characters.

### Commit Message Header

```txt
<type>(<scope>): <short summary> #<issue>
  |       |            |             |
  |       |            |             └─⫸ Issue number. No period at the end.
  │       │            │
  │       │            └─⫸ Summary in present tense. Not capitalized. No period at the end.
  │       │
  │       └─⫸ Commit Scope: db|algo||instances|tests|utils|...
  │
  └─⫸ Commit Type: docs|feat|fix|perf|refactor|test|...
```

The `<type>` and `<summary>` fields are mandatory, the `(<scope>)` field is optional.
