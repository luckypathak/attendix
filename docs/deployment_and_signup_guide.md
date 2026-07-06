# Deployment and New User Registration Guide

This guide outlines:
1. How to deploy the Pulseix Workforce OS frontend, backend, and PostgreSQL database for **free**.
2. How to implement a new User/Company registration (Sign Up) flow.

---

## Part 1: Free Deployment Guide

We will use a modern, reliable, and completely free hosting stack:
* **Database**: [Neon.tech](https://neon.tech/) (Free Serverless PostgreSQL)
* **Backend (Django)**: [Render.com](https://render.com/) (Free Web Service)
* **Frontend (React/Vite)**: [Vercel](https://vercel.com/) or [Netlify](https://www.netlify.com/) (Free Static Hosting)

### 1. Database Setup (Neon PostgreSQL)
1. Go to [Neon.tech](https://neon.tech/) and create a free account.
2. Create a new project named `pulseix-db`.
3. Copy your connection string from the dashboard. It will look like this:
   `postgresql://neondb_owner:password@ep-cool-snowflake-12345.aws.neon.tech/neondb?sslmode=require`

### 2. Backend Deployment (Render.com)

#### Step A: Code adjustments for Production
1. In `backend/requirements.txt`, ensure you have Gunicorn and dj-database-url:
   ```txt
   gunicorn==21.2.0
   dj-database-url==2.1.0
   psycopg2-binary==2.9.9
   ```
2. In `backend/pulseix/settings.py`, modify database settings to parse the database URL dynamically:
   ```python
   import dj_database_url
   import os

   DATABASES = {
       'default': dj_database_url.config(
           default='sqlite:///db.sqlite3',
           conn_max_age=600,
           ssl_require=True if os.environ.get('DATABASE_URL') else False
       )
   }
   ```
3. Update `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` to allow your Render backend URL and Vercel frontend URL:
   ```python
   ALLOWED_HOSTS = [os.environ.get('RENDER_HOSTNAME', 'localhost'), '127.0.0.1']
   CORS_ALLOWED_ORIGINS = [
       os.environ.get('FRONTEND_URL', 'http://localhost:5173')
   ]
   ```

#### Step B: Deploy on Render
1. Go to [Render.com](https://render.com/) and create a free account.
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository containing the backend code.
4. Set the following settings:
   * **Language**: `Python`
   * **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --no-input`
   * **Start Command**: `gunicorn pulseix.wsgi:application --bind 0.0.0.0:$PORT`
   * **Instance Type**: `Free`
5. Under **Environment Variables**, add:
   * `DATABASE_URL`: `postgresql://neondb_owner:password@ep-aws.neon.tech/neondb?sslmode=require` (your Neon URL)
   * `SECRET_KEY`: `your-production-secret-key`
   * `DEBUG`: `False`
   * `FRONTEND_URL`: `https://your-frontend-app.vercel.app`
6. Click **Deploy Web Service**. Render will build and start your server. Run database migrations by using the Render Shell or by appending `python manage.py migrate` to the Build Command!

---

### 3. Frontend Deployment (Vercel)
1. Go to [Vercel.com](https://vercel.com/) and connect your GitHub account.
2. Click **Add New** > **Project** and select your repository.
3. Configure the settings:
   * **Framework Preset**: `Vite`
   * **Root Directory**: `frontend`
4. Under **Environment Variables**, add:
   * `VITE_API_URL`: `https://your-backend-app.onrender.com/api/v1` (your Render backend URL)
5. Click **Deploy**. Vercel will build and host your frontend globally.

---

## Part 2: Implementing New User/Company Registration

Currently, users are created by admins. To build a public self-registration/signup page for new companies:

### 1. Backend View & Endpoint
Create a registration view that receives the company name, user's email, username, and password, creates the `Company` record, and sets up the user as the `COMPANY_ADMIN`.

#### Step A: Register Serializer
Create `backend/pulseix/apps/authentication/serializers.py` (or add to it):
```python
from rest_framework import serializers
from django.contrib.auth import get_user_model
from pulseix.apps.company.models import Company

User = get_user_model()

class CompanyRegistrationSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=100)
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)

    def create(self, validated_data):
        # 1. Create the Company
        company = Company.objects.create(name=validated_data['company_name'])
        
        # 2. Create the Company Admin User
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role='COMPANY_ADMIN',
            company=company
        )
        return user
```

#### Step B: Register View
In `backend/pulseix/apps/authentication/views.py`:
```python
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .serializers import CompanyRegistrationSerializer

class RegisterCompanyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CompanyRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "detail": "Company and Admin registered successfully. Please log in.",
                "user": user.username
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

#### Step C: Wire URLs
In `backend/pulseix/apps/authentication/urls.py`:
```python
from django.urls import path
from .views import RegisterCompanyView

urlpatterns = [
    # ... existing token routes ...
    path('register/', RegisterCompanyView.as_view(), name='register-company'),
]
```

---

### 2. Frontend Signup Page
Create a registration view on the React frontend.

#### Step A: Create `frontend/src/pages/Register.jsx`
```jsx
import React, { useState } from 'react';
import { Box, Card, CardContent, TextField, Button, Typography, Alert } from '@mui/material';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';

export default function Register() {
  const [companyName, setCompanyName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setError(null);
    setMsg(null);
    try {
      await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/auth/register/`, {
        company_name: companyName,
        username,
        email,
        password
      });
      setMsg("Registration successful! Redirecting to login...");
      setTimeout(() => navigate('/login'), 2000);
    } catch (err) {
      setError(err.response?.data || { detail: "Registration failed." });
    }
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', alignItems: 'center', justifyContent: 'center', p: 3 }}>
      <Card sx={{ maxWidth: 400, width: '100%' }}>
        <CardContent>
          <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>Register Company</Typography>
          {msg && <Alert severity="success" sx={{ mb: 2 }}>{msg}</Alert>}
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error.detail || JSON.stringify(error)}</Alert>}
          
          <form onSubmit={handleRegister}>
            <TextField fullWidth label="Company Name" value={companyName} onChange={e => setCompanyName(e.target.value)} sx={{ mb: 2 }} required />
            <TextField fullWidth label="Username" value={username} onChange={e => setUsername(e.target.value)} sx={{ mb: 2 }} required />
            <TextField fullWidth type="email" label="Email Address" value={email} onChange={e => setEmail(e.target.value)} sx={{ mb: 2 }} required />
            <TextField fullWidth type="password" label="Password" value={password} onChange={e => setPassword(e.target.value)} sx={{ mb: 3 }} required />
            
            <Button type="submit" variant="contained" fullWidth>Sign Up</Button>
          </form>
          
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Link to="/login" style={{ fontSize: '0.9rem', color: '#888' }}>Already have an account? Login</Link>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
```

#### Step B: Register the Route
Add `/register` to the router configuration inside `frontend/src/App.jsx`.
