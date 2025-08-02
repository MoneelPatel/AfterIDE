# Authentication Troubleshooting Guide

## Issue: "Invalid token" or "401 Unauthorized" errors

If you're experiencing authentication issues when trying to access the review page or other protected features, follow these steps:

### Quick Fix

1. **Clear your authentication data:**
   - Look for a red "Reset Auth" button in the bottom-right corner of the screen
   - Click it and confirm to clear your authentication
   - You'll be redirected to the login page

2. **Log in again:**
   - Use your username and password to log in
   - If you don't remember your credentials, you can create a new account

### Manual Fix (if the button isn't visible)

1. **Open your browser's developer tools:**
   - Press F12 or right-click and select "Inspect"
   - Go to the "Console" tab

2. **Run this command in the console:**
   ```javascript
   localStorage.removeItem('authToken');
   window.location.href = '/login';
   ```

3. **Log in again** with your credentials

## Issue: "Mixed Content" errors

If you see errors about mixed content (HTTP vs HTTPS), this is automatically handled by the application. The system will:

1. **Automatically convert HTTP URLs to HTTPS** when needed
2. **Show a warning in the console** if mixed content is detected
3. **Continue to work normally** after the conversion

### If you continue to see mixed content errors:

1. **Clear your browser cache** and reload the page
2. **Check your Railway environment variables** to ensure `VITE_API_URL` is set to HTTPS
3. **Contact support** if the issue persists

### Common Causes

- **Token Expiration:** Authentication tokens expire after 7 days for security
- **Browser Storage Issues:** Local storage might be corrupted or cleared
- **Network Issues:** Temporary connectivity problems with the backend
- **Environment Configuration:** Incorrect API URL configuration in production

### Prevention

- **Regular Logins:** Log in regularly to keep your token fresh
- **Stable Connection:** Ensure you have a stable internet connection
- **Browser Updates:** Keep your browser updated
- **Clear Cache:** Periodically clear your browser cache

### Still Having Issues?

If you continue to experience problems:

1. Try using a different browser
2. Clear your browser cache and cookies
3. Check if the backend service is running properly
4. Contact support if the issue persists

### Default Test Credentials

For testing purposes, you can use:
- **Username:** `admin`
- **Password:** `password`

---

**Note:** This troubleshooting guide is specifically for the AfterIDE application. If you're experiencing issues with other applications, please refer to their respective documentation. 