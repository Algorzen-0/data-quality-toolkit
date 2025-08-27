# 🤝 **Contributing to Algorzen Data Quality Toolkit**

Thank you for your interest in contributing to the Algorzen Data Quality Toolkit! This document provides guidelines and information for contributors.

## 🎯 **How Can I Contribute?**

### **🐛 Bug Reports**
- Use the [GitHub Issues](https://github.com/algorzen/data-quality-toolkit/issues) page
- Include detailed steps to reproduce the bug
- Provide system information and error logs
- Use the bug report template

### **💡 Feature Requests**
- Submit feature requests through [GitHub Issues](https://github.com/algorzen/data-quality-toolkit/issues)
- Describe the use case and expected behavior
- Consider the impact on existing functionality
- Use the feature request template

### **📝 Documentation**
- Improve README files and documentation
- Add code examples and tutorials
- Fix typos and clarify unclear sections
- Translate documentation to other languages

### **🔧 Code Contributions**
- Fix bugs and implement features
- Improve performance and add tests
- Enhance the CLI and API
- Add new quality check types

## 🚀 **Getting Started**

### **1. Fork and Clone**
```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/data-quality-toolkit.git
cd data-quality-toolkit

# Add the upstream remote
git remote add upstream https://github.com/algorzen/data-quality-toolkit.git
```

### **2. Setup Development Environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install React dependencies
cd frontend/algorzen-dashboard
npm install
cd ../..
```

### **3. Create a Branch**
```bash
# Create a feature branch
git checkout -b feature/amazing-feature

# Or create a bug fix branch
git checkout -b fix/bug-description
```

## 📋 **Development Guidelines**

### **Python Code Standards**
- **Style**: Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) guidelines
- **Formatting**: Use [Black](https://black.readthedocs.io/) for code formatting
- **Linting**: Use [Flake8](https://flake8.pycqa.org/) for linting
- **Type Hints**: Use type annotations throughout the codebase
- **Docstrings**: Follow [Google Style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)

### **React/TypeScript Standards**
- **Style**: Follow the existing code style and patterns
- **Components**: Use functional components with hooks
- **Types**: Define proper TypeScript interfaces
- **Testing**: Add tests for new components

### **Testing Requirements**
- **Coverage**: Maintain high test coverage (>90%)
- **Unit Tests**: Write tests for all new functionality
- **Integration Tests**: Test API endpoints and CLI commands
- **Frontend Tests**: Test React components and interactions

### **Commit Message Format**
```bash
# Use conventional commit format
feat: add new quality check type
fix: resolve memory leak in data processing
docs: update API documentation
style: format code with black
refactor: restructure quality check engine
test: add tests for outlier detection
chore: update dependencies
```

## 🔧 **Development Workflow**

### **1. Make Changes**
- Write your code following the standards
- Add tests for new functionality
- Update documentation as needed

### **2. Run Tests**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=algorzen_dqt

# Run specific test files
pytest tests/test_quality_checks.py

# Run frontend tests
cd frontend/algorzen-dashboard
npm test
```

### **3. Code Quality Checks**
```bash
# Format code
black algorzen_dqt/
black tests/

# Lint code
flake8 algorzen_dqt/
flake8 tests/

# Type checking
mypy algorzen_dqt/

# Frontend linting
cd frontend/algorzen-dashboard
npm run lint
```

### **4. Commit and Push**
```bash
# Stage changes
git add .

# Commit with conventional format
git commit -m "feat: add new quality check type"

# Push to your fork
git push origin feature/amazing-feature
```

### **5. Create Pull Request**
- Go to your fork on GitHub
- Click "New Pull Request"
- Select the upstream repository and your branch
- Commit with conventional format
- Request review from maintainers

## 📚 **Project Structure**

```
algorzen_dqt/
├── api/                    # FastAPI endpoints
├── checks/                 # Quality check implementations
├── cli/                    # Command-line interface
├── core/                   # Core engine and logic
├── connectors/             # Data source connectors
├── processors/             # Data processors
├── reporting/              # Report generation
├── utils/                  # Utility functions
└── tests/                  # Test suite

frontend/
└── algorzen-dashboard/     # React frontend
    ├── src/
    ├── public/
    └── package.json
```

## 🧪 **Testing Guidelines**

### **Python Tests**
- Use [pytest](https://pytest.org/) as the testing framework
- Place tests in the `tests/` directory
- Use descriptive test names and docstrings
- Mock external dependencies
- Test both success and failure cases

### **Frontend Tests**
- Use [Jest](https://jestjs.io/) and [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- Test component rendering and interactions
- Mock API calls and external services
- Test user workflows and edge cases

### **API Tests**
- Test all API endpoints
- Verify request/response schemas
- Test authentication and authorization
- Test error handling and edge cases

## 📝 **Documentation Standards**

### **Code Documentation**
- Use clear, concise docstrings
- Include examples for complex functions
- Document parameters, return values, and exceptions
- Keep documentation up-to-date with code changes

### **User Documentation**
- Write clear, step-by-step instructions
- Include screenshots and examples
- Use consistent formatting and terminology
- Keep documentation organized and searchable

## 🔍 **Review Process**

### **Pull Request Review**
- All PRs require at least one review
- Maintainers will review for:
  - Code quality and standards
  - Test coverage and quality
  - Documentation updates
  - Performance implications
  - Security considerations

### **Review Checklist**
- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No breaking changes (unless documented)
- [ ] Performance impact is considered
- [ ] Security implications are addressed

## 🚨 **Security Guidelines**

### **Reporting Security Issues**
- **DO NOT** create public issues for security vulnerabilities
- Email security issues to: security@algorzen.com
- Include detailed description and reproduction steps
- Allow time for security team to respond

### **Security Best Practices**
- Never commit sensitive information (API keys, passwords)
- Use environment variables for configuration
- Validate and sanitize all inputs
- Follow OWASP security guidelines

## 🏷️ **Labels and Milestones**

### **Issue Labels**
- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `priority: high`: High priority issues
- `priority: low`: Low priority issues

### **Pull Request Labels**
- `ready for review`: Ready for maintainer review
- `work in progress`: Still being developed
- `needs review`: Requires code review
- `tests needed`: Missing test coverage
- `documentation needed`: Missing documentation

## 🎉 **Recognition**

### **Contributor Recognition**
- All contributors are listed in the [Contributors](https://github.com/algorzen/data-quality-toolkit/graphs/contributors) section
- Significant contributions are acknowledged in release notes
- Contributors may be invited to join the core team

### **Contributor Types**
- **Contributor**: Anyone who submits a PR or issue
- **Reviewer**: Contributors who review PRs
- **Maintainer**: Core team members with merge access
- **Owner**: Project founders and leaders

## 📞 **Getting Help**

### **Community Support**
- [GitHub Discussions](https://github.com/algorzen/data-quality-toolkit/discussions)
- [GitHub Issues](https://github.com/algorzen/data-quality-toolkit/issues)
- [Documentation](https://github.com/algorzen/data-quality-toolkit#documentation)

### **Direct Contact**
- **General Questions**: contact@algorzen.com
- **Security Issues**: security@algorzen.com
- **Contributor Support**: contributors@algorzen.com

## 🙏 **Thank You**

Thank you for contributing to the Algorzen Data Quality Toolkit! Your contributions help make this project better for everyone in the data quality community.

---

**Happy coding! 🚀**
