# Contributing to Helix Sequencer

Thank you for your interest in contributing to the Helix Sequencer! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project adheres to the Contributor Covenant [Code of Conduct](./CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.11 or 3.12
- Git
- Familiarity with xLights and audio sequencing (helpful but not required)

### Setup Development Environment

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/helix-sequencer.git
   cd helix-sequencer
   ```

2. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Install dependencies:**
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements-dev.txt
   ```

4. **Run tests to verify setup:**
   ```bash
   python -m pytest -q
   ```

## Making Changes

### Code Style

- Follow [PEP 8](https://pep8.org/) guidelines
- Use 4 spaces for indentation
- Line length: 100 characters (prefer readability over strict limits)
- Type hints are encouraged (Python 3.11+)

### Commit Messages

- Use clear, descriptive commit messages
- Start with a verb: "Add", "Fix", "Refactor", "Update", etc.
- Reference issues when relevant: `Fix #123`
- Keep first line under 50 characters; add details in body if needed

### Testing

- Write tests for new features
- Ensure all tests pass locally:
  ```bash
  python -m pytest -q
  ```
- Tests should be in the `tests/` directory
- Use descriptive test names: `test_<function>_<scenario>`

### Documentation

- Update README.md if you change user-facing behavior
- Add docstrings to new functions and classes
- Use Google-style docstrings:
  ```python
  def example(arg: str) -> int:
      """Short description.
      
      Longer description if needed.
      
      Args:
          arg: Description of arg.
      
      Returns:
          Description of return value.
      
      Raises:
          ValueError: When something is wrong.
      """
  ```

## Submitting Changes

### Pull Request Process

1. **Ensure tests pass:**
   ```bash
   python -m pytest -q
   ```

2. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Open a Pull Request on GitHub:**
   - Use a clear title describing the change
   - Reference any related issues: "Closes #123"
   - Describe what changed and why
   - Include any testing notes

4. **Address review feedback:**
   - Respond to comments and suggestions
   - Make requested changes in new commits
   - Avoid force-pushing unless specifically asked

### PR Requirements

- ✅ All CI checks pass (tests, linting, type checks)
- ✅ Code follows project style guidelines
- ✅ New features include tests
- ✅ Documentation is updated if needed
- ✅ Commit messages are clear and descriptive

## Reporting Issues

When reporting bugs:

1. **Check existing issues** to avoid duplicates
2. **Use a clear title** describing the problem
3. **Include reproduction steps:**
   - What you did
   - What you expected
   - What actually happened
4. **Provide context:**
   - OS and Python version
   - xLights version
   - Relevant files or snippets
   - Contents of `run_manifest.json` from a failed run (helpful for diagnostics)

## Feature Requests

1. **Describe the use case:** Why is this feature needed?
2. **Provide examples:** How would users interact with it?
3. **Discuss alternatives:** Are there other ways to solve this?
4. **Check the roadmap:** Is this already planned? See [ROADMAP_BETA_TODO.md](./ROADMAP_BETA_TODO.md)

## Questions?

- **Discussions:** Use [GitHub Discussions](https://github.com/ryankorkowski-boop/helix-sequencer/discussions) for questions
- **Issues:** Use [GitHub Issues](https://github.com/ryankorkowski-boop/helix-sequencer/issues) for bugs and features
- **Read the docs:** Check [docs/](./docs/) for architecture and design decisions

## Licensing

New contributions are intended to be offered under the [PolyForm Noncommercial License 1.0.0](./LICENSE), subject to contributor authorization and any separately documented rights. Contributors should confirm they have authority to license their work under these terms. Commercial licensing rights for contributed material require appropriate authorization; see [commercial licensing](./COMMERCIAL_LICENSING.md).

---

Thank you for contributing to make Helix Sequencer better! 🎵✨
