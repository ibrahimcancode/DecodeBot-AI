def levenshtein(a: str, b: str) -> int:
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return dp[m][n]


def fuzzy_suggest(normalized_text: str) -> str | None:
    best_match = None
    best_distance = 3
    known_commands = ["help", "about", "version", "exit", "bye", "history", "stats", "reset", "clear", "settings", "quit"]
    for cmd in known_commands:
        d = levenshtein(normalized_text, cmd)
        if d <= 2 and d < best_distance:
            best_match = cmd
            best_distance = d
    return best_match
