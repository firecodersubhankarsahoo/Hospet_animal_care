import secrets

# Generate a 32-byte secret key (or adjust the size as needed)
secret_key = secrets.token_hex(32)
print(secret_key)
