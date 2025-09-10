import jwt

# Your secret from .env
secret = "2e0c7e427da6a1c852ff3f1a66706fad995c6e4606458c3f0d8402749a862633"

# Simple payload — no 'aud', no 'exp'
payload = {
    "sub": "tester",
    "iss": "your-app"
}

# Encode the token
token = jwt.encode(payload, secret, algorithm="HS256")

print(f"\n Copy this JWT token below:\n\n{token}\n")
print("You can now export it in your terminal like this:")
print(f"\nexport JWT='{token}'\n")

