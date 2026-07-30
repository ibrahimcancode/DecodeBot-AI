# Changelog

## [1.0.0] - 2026-07-30

### Added
- Core conversation loop with input normalization
- Greeting detection (15+ patterns, 8+ response variants)
- Exit detection (10+ patterns, negation-safe)
- Unknown input fallback with escalation and fuzzy suggestions
- Help, About, Version commands with aliases
- Session history (bounded to 100 turns)
- Runtime statistics (message count, duration, intent breakdown)
- Personalization (set/forget name)
- Hidden easter eggs and commands
- Plugin auto-discovery system
- Config file support (JSON) with fallback to defaults
- Rotating file logging with configurable log levels
- Error handling (KeyboardInterrupt, EOFError, circuit breaker)
- CLI animations (typewriter effect, thinking indicator)
- Levenshtein-based fuzzy command suggestions
- Cross-platform terminal utilities (clear screen, width detection)
- Comprehensive test suite (219+ tests)
