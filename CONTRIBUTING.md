# Contributing

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the full test suite (`python -m pytest`)
5. Commit with a clear message
6. Push and open a Pull Request

## Guidelines

- All code must be pure stdlib Python — no third-party runtime dependencies
- Every function must have type hints
- Follow PEP 8 (line length 100)
- All tests must pass before a PR is merged
- New features must include tests
- Plugin contributions go in the `plugins/` directory
- Keep the SPEC.md in sync with any behavioral changes

## Code of Conduct

Be respectful and constructive.
