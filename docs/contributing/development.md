<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
SPDX-License-Identifier: CC-BY-SA-4.0
-->
# Development

Guidelines and workflow for contributing code to CommonGraph.

## Project Structure

```
commongraph/
├── backend/              # FastAPI backend
│   ├── api/              # API endpoints
│   ├── db/               # Database models
│   ├── models/           # Data models
│   ├── utils/            # Utilities
│   ├── main.py           # Entry point
│   └── tests/            # Backend tests
├── frontend/             # Vue.js frontend
│   ├── src/
│   │   ├── components/   # Vue components
│   │   ├── views/        # Page components
│   │   ├── stores/       # State management
│   │   └── main.js       # Entry point
│   └── tests/            # Frontend tests
├── docs/                 # Documentation (mkdocs)
├── config/               # Platform configurations
├── docker-compose.yaml   # Docker configuration
└── README.md             # Project overview
```

## Backend Development

### Setup

```bash
cd backend
pip install -r requirements-dev.txt
```

### Running

```bash
uvicorn main:app --reload
```

Visits http://localhost:8000

### Code Style

- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Keep functions focused and testable

### Testing

```bash
pytest
```

Run specific test:
```bash
pytest test_models.py::TestUser
```

With coverage:
```bash
pytest --cov=backend
```

## Frontend Development

### Setup

```bash
cd frontend
npm install
```

### Running

```bash
npm run dev
```

Visits http://localhost:5173

### Code Style

- Use ES6+ syntax
- Follow Vue 3 composition API patterns
- Meaningful variable and component names
- Comments for complex logic

### Testing

```bash
npm run test
```

### Linting

```bash
npm run lint
```

## Commit Messages

Write clear, descriptive commit messages:

```
Type: Brief summary (50 chars max)

Detailed explanation of the change (72 chars per line)

Related to: #issue_number
```

Types:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Test additions
- `refactor:` Code refactoring
- `chore:` Build, deps, etc.

## Pull Request Process

1. Create feature branch from `dev`
2. Make focused, atomic commits
3. Write clear PR description
4. Reference related issues
5. Ensure tests pass
6. Request review
7. Address feedback
8. Merge when approved

## Before Submitting

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] No linting errors
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No unrelated changes included

## Questions?

- Check existing issues and PRs
- Ask in GitHub discussions
- Email [contact@comodelling.org](mailto:contact@comodelling.org)

## Thank You

We appreciate your contributions to making CommonGraph better!
