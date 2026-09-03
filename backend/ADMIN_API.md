# Admin setup and API checks

Apply `migrations/001_add_user_role.sql`, then set private values in `.env`:

```env
ADMIN_NAME=ResearchMind Admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=replace_with_a_strong_password
```

Do not commit `.env`. On startup, the backend creates the configured admin if
needed. If it already exists as an admin, its name and changed password are
synchronized. Startup stops if the email belongs to a regular user.

## Postman requests

Use `{{baseUrl}} = http://127.0.0.1:5000`.

### Log in

`POST {{baseUrl}}/api/auth/login`

```json
{
  "email": "admin@example.com",
  "password": "replace_with_a_strong_password"
}
```

Expected `200`: an `access_token`, `token_type`, and a user object whose role is
`admin`. Save the token as `{{adminToken}}`.

### Current account

`GET {{baseUrl}}/api/auth/me` with header
`Authorization: Bearer {{adminToken}}`.

Expected `200`: id, name, email, role, and created_at; no password field.

### List regular users

`GET {{baseUrl}}/api/admin/users` with header
`Authorization: Bearer {{adminToken}}`.

Expected `200`: a newest-first array containing id, name, email, role, and
created_at. With a regular-user token, expect `403` and
`{"message":"Admin access required"}`. With no/invalid token, expect `401`.

### Delete a regular user

`DELETE {{baseUrl}}/api/admin/users/{{userId}}` with header
`Authorization: Bearer {{adminToken}}`.

Expected `200`: `{"message":"User deleted successfully"}`. A missing user
returns `404`, an invalid ID returns `400`, and an admin target returns `403`.

### Existing admin-owned document and chat routes

Use `Authorization: Bearer {{adminToken}}` with the existing requests:

- `POST /api/documents/upload` (`form-data`, key `file`, PDF value)
- `GET /api/documents`
- `DELETE /api/documents/{{documentId}}`
- `POST /api/chat` with `{"question":"Summarize my paper"}`
- `GET /api/chat/sessions`
- `GET /api/chat/sessions/{{sessionId}}`
- `DELETE /api/chat/sessions/{{sessionId}}`

These routes continue to use the JWT user ID, so the admin sees only the
admin's own PDFs, vector chunks, messages, and sessions.

## Data flow

The startup seed hashes the configured password and stores the admin as a normal
user row with role `admin`. Login reads that role from MySQL and signs it into
the JWT. Admin routes first authenticate the JWT, then confirm both its role and
the current MySQL role. User deletion removes each document from ChromaDB/BM25
through the existing Python endpoint, validates and removes each exact PDF path,
then deletes messages, sessions, documents, and the regular user in one MySQL
transaction. A cleanup failure is surfaced and the database rows are retained.
