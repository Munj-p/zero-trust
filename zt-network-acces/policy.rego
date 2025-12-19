package zero_trust

default allow := false
default session_duration := 0

# Rule: Allow if method is login and credentials match
allow if{
    input.method == "login"
    input.user == "dev_user"
    input.password == "securePass123"
}

# Rule: Set session duration to 300 seconds (5 mins) if allowed
session_duration = 300 if {
    allow
}
