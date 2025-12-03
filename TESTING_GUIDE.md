# Testing Guide - Using Swagger UI (FastAPI Docs)

## 🚀 Quick Start

1. **Start the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Open Swagger UI in your browser:**
   ```
   http://localhost:8000/docs
   ```

---

## 📋 Step-by-Step Testing Guide

### Step 1: Open Swagger UI

Navigate to `http://localhost:8000/docs` in your browser.

You'll see:
- All available API endpoints
- Request/response schemas
- Try it out buttons
- Authentication options

---

### Step 2: Test User Registration (Signup)

**Endpoint:** `POST /api/signup`

1. **Find the endpoint** in the Swagger UI (under "Authentication" section)

2. **Click "Try it out"** button

3. **Fill in the request body:**
   ```json
   {
     "username": "testuser",
     "email": "test@example.com",
     "password": "testpassword123"
   }
   ```

4. **Click "Execute"**

5. **Check the response:**
   - Status: `201 Created`
   - Response body will contain:
     ```json
     {
       "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
       "token_type": "bearer"
     }
     ```

6. **Copy the `access_token`** - you'll need it for protected endpoints!

---

### Step 3: Authenticate (Login)

**Endpoint:** `POST /api/login`

**Alternative to signup** - if you already have a user:

1. Click "Try it out"

2. Enter credentials:
   ```json
   {
     "username": "testuser",
     "password": "testpassword123"
   }
   ```

3. Click "Execute"

4. Copy the `access_token` from response

---

### Step 4: Authorize Swagger UI

**Important:** You need to authorize Swagger UI to access protected endpoints!

1. **Click the green "Authorize" button** 🔒 at the top right of Swagger UI
   - Look for the lock icon next to the API title

2. **A popup window will appear** - find the "Value" field

3. **Paste your access token** in this exact format:
   ```
   Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
   **Critical:** 
   - Must include the word `Bearer` followed by a **space**
   - Then paste your full token
   - Format: `Bearer <your-token>`
   
   **Example with your token:**
   ```
   Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTc2NDYwODM0MX0.G2f1JC_mCdqZTniF67QWDYk_fdX9XZV5dx8nSfACQE0
   ```

4. **Click "Authorize"** button in the popup

5. **Click "Close"** to close the popup

6. **Verify:** You should see a green lock icon 🔒 next to protected endpoints

Now all protected endpoints will automatically include your token! ✅

**See `SWAGGER_AUTH_GUIDE.md` for detailed visual guide and troubleshooting.**

---

### Step 5: Create Content (with AI Processing)

**Endpoint:** `POST /api/contents`

1. **Find the endpoint** (under "Content Management" section)

2. **Click "Try it out"**

3. **Enter text content:**
   ```json
   {
     "text": "I absolutely love this new product! It's amazing and works perfectly. The quality is outstanding and I would definitely recommend it to everyone!"
   }
   ```

4. **Click "Execute"**

5. **Check the response:**
   - Status: `201 Created`
   - Response includes:
     - `id`: Content ID
     - `text`: Your original text
     - `summary`: `null` (will be populated by AI in background)
     - `sentiment`: `null` (will be populated by AI in background)
     - `created_at`: Timestamp

**Note:** Summary and sentiment are processed asynchronously. Check back in a few seconds!

---

### Step 6: Get All Your Content

**Endpoint:** `GET /api/contents`

1. **Click "Try it out"**

2. **Optional parameters:**
   - `skip`: Number of records to skip (for pagination)
   - `limit`: Maximum records to return (default: 100)

3. **Click "Execute"**

4. **Check the response:**
   ```json
   {
     "contents": [
       {
         "id": 1,
         "text": "...",
         "summary": "User expresses positive sentiment...",
         "sentiment": "Positive",
         "created_at": "2024-01-15T10:30:00Z",
         "updated_at": "2024-01-15T10:30:05Z"
       }
     ],
     "total": 1
   }
   ```

**Note:** If AI processing completed, you'll see `summary` and `sentiment` populated!

---

### Step 7: Get Specific Content

**Endpoint:** `GET /api/contents/{id}`

1. **Click "Try it out"**

2. **Enter the content ID** (from previous step, e.g., `1`)

3. **Click "Execute"**

4. **Check the response:**
   - Full content details
   - AI-generated summary
   - Sentiment analysis

---

### Step 8: Delete Content

**Endpoint:** `DELETE /api/contents/{id}`

1. **Click "Try it out"**

2. **Enter the content ID** to delete

3. **Click "Execute"**

4. **Check the response:**
   - Status: `204 No Content` (successful deletion)

5. **Verify deletion:** Try `GET /api/contents/{id}` - should return `404 Not Found`

---

## 🎯 Complete Test Flow Example

Here's a complete flow to test everything:

### 1. Register New User
```json
POST /api/signup
{
  "username": "demo_user",
  "email": "demo@example.com",
  "password": "securepass123"
}
```
**Copy the access_token!**

### 2. Authorize Swagger UI
- Click "Authorize" button
- Paste: `Bearer <your-access-token>`
- Click "Authorize" and "Close"

### 3. Create Content
```json
POST /api/contents
{
  "text": "This is a fantastic day! The weather is perfect and I'm feeling great about everything."
}
```
**Note the content ID from response**

### 4. Wait 2-3 seconds
(AI processing happens in background)

### 5. Get Content
```
GET /api/contents/{id}
```
**Check if summary and sentiment are populated**

### 6. Get All Contents
```
GET /api/contents
```
**See all your content**

### 7. Delete Content
```
DELETE /api/contents/{id}
```

---

## 🔍 Testing Different Scenarios

### Test Positive Sentiment
```json
{
  "text": "I'm so happy! This is the best day ever! Everything is going perfectly!"
}
```
**Expected sentiment:** `Positive`

### Test Negative Sentiment
```json
{
  "text": "I'm really disappointed. This product doesn't work at all. Very poor quality."
}
```
**Expected sentiment:** `Negative`

### Test Neutral Sentiment
```json
{
  "text": "The meeting is scheduled for tomorrow at 3 PM. Please bring your notes."
}
```
**Expected sentiment:** `Neutral`

### Test Error Cases

**1. Duplicate Username:**
```json
POST /api/signup
{
  "username": "testuser",  // Already exists
  "email": "new@example.com",
  "password": "pass123"
}
```
**Expected:** `400 Bad Request` - "Username already registered"

**2. Invalid Credentials:**
```json
POST /api/login
{
  "username": "testuser",
  "password": "wrongpassword"
}
```
**Expected:** `401 Unauthorized` - "Incorrect username or password"

**3. Unauthorized Access:**
- Don't authorize Swagger UI
- Try `GET /api/contents`
**Expected:** `401 Unauthorized`

**4. Access Other User's Content:**
- Create content with User A
- Login as User B
- Try to access User A's content ID
**Expected:** `404 Not Found` (security - users can't see others' content)

---

## 🛠️ Troubleshooting

### Problem: "401 Unauthorized" on protected endpoints

**Solution:**
1. Make sure you clicked "Authorize" button
2. Format: `Bearer <your-token>` (include "Bearer" and space)
3. Token might be expired (default: 30 minutes)
4. Login again to get a new token

### Problem: Summary/Sentiment is null

**Possible reasons:**
1. AI processing is still running (wait a few seconds)
2. HuggingFace API key not configured in `.env`
3. AI API is down or rate-limited
4. Check server logs for errors

**Solution:**
- Wait 5-10 seconds and refresh
- Check `.env` file has `HUGGINGFACE_API_KEY`
- Check server console for error messages

### Problem: "422 Unprocessable Entity"

**Solution:**
- Check request body format matches the schema
- Required fields are present
- Email format is valid
- Text field is not empty

### Problem: Can't see endpoints

**Solution:**
- Make sure server is running (`uvicorn app.main:app --reload`)
- Check URL is correct: `http://localhost:8000/docs`
- Try refreshing the page

---

## 📊 Understanding Responses

### Success Responses

- **200 OK**: Request successful (GET, POST login)
- **201 Created**: Resource created successfully (POST signup, POST contents)
- **204 No Content**: Deletion successful (DELETE)

### Error Responses

- **400 Bad Request**: Invalid input (duplicate username, empty text)
- **401 Unauthorized**: Not authenticated or invalid token
- **404 Not Found**: Resource doesn't exist or doesn't belong to user
- **422 Unprocessable Entity**: Validation error (invalid email format, etc.)

---

## 💡 Pro Tips

1. **Keep Swagger UI Open**: It auto-updates when you change code (if using `--reload`)

2. **Use Multiple Tabs**: 
   - Tab 1: Swagger UI
   - Tab 2: ReDoc (`http://localhost:8000/redoc`) - Alternative documentation

3. **Check Server Logs**: 
   - Watch the terminal where uvicorn is running
   - See AI processing logs
   - See any errors

4. **Test Edge Cases**:
   - Very long text
   - Empty text (should fail)
   - Special characters
   - Unicode characters

5. **Monitor Database**:
   - Use DB Browser for SQLite to view `Emo_Energy.db`
   - See actual data stored
   - Verify relationships

---

## 🎓 Interview Talking Points

When demonstrating:

1. **Show Swagger UI**: "FastAPI automatically generates interactive API documentation"

2. **Demonstrate Authentication**: "JWT tokens secure all content endpoints"

3. **Show AI Processing**: "Content is saved immediately, AI processes asynchronously in background"

4. **Show Security**: "Users can only access their own content - try accessing another user's ID"

5. **Show Error Handling**: "Invalid inputs are automatically validated and rejected"

---

## ✅ Checklist

- [ ] Server running (`uvicorn app.main:app --reload`)
- [ ] Swagger UI accessible (`http://localhost:8000/docs`)
- [ ] User registered successfully
- [ ] Token copied and authorized in Swagger UI
- [ ] Content created successfully
- [ ] AI processing completed (summary/sentiment populated)
- [ ] All endpoints tested (GET, POST, DELETE)
- [ ] Error cases tested (unauthorized, invalid input)
- [ ] Different sentiment types tested

---

**Happy Testing! 🚀**

For more details, check:
- `README.md` - Full API documentation
- `CODE_EXPLANATION.md` - Code walkthrough
- Server logs - Real-time debugging info

