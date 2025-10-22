# Streamlit Cloud Setup Instructions

## Configuring Admin Password

The admin password is stored using Streamlit Secrets for security. Follow these steps to configure it on Streamlit Cloud:

### Step 1: Go to Your App Settings

1. Log in to [Streamlit Cloud](https://share.streamlit.io)
2. Navigate to your deployed app
3. Click the menu (three dots) → **Settings**

### Step 2: Add Secrets

1. In the Settings panel, find the **Secrets** section
2. Click on **Edit Secrets** or the pencil icon
3. Add the following configuration:

```toml
# Admin password hash (SHA256)
# Current hash is for password: vesaadmin1
admin_password_hash = "5c92f47698b144c721c98abbf36afbed62b3f7fb4da8e2d1f9da809d65fa5222"
```

4. Click **Save**

### Step 3: Restart the App

The app will automatically restart when you save the secrets.

## Changing the Admin Password

To change the admin password:

1. Generate a new SHA256 hash of your desired password:
   ```bash
   python3 -c "import hashlib; password = 'your_new_password'; print(hashlib.sha256(password.encode()).hexdigest())"
   ```

2. Update the `admin_password_hash` value in Streamlit Secrets with the new hash

3. Save and the app will restart with the new password

## Local Development

For local development, create a `.streamlit/secrets.toml` file in your project directory:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit the file with your password hash. This file is gitignored and won't be committed.

## Default Password

The default password (for local development without secrets configured) is: **vesaadmin1**

⚠️ **Important**: Make sure to configure proper secrets on Streamlit Cloud for production use!
