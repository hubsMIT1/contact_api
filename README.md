# Project Name

## Setup

1. Setup the project locally and to go the project directory.

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   venv\Scripts\activate  # On linux, use `source venv/bin/activate`
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.sample` and update the values.

5. Run migrations:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

6. Create a superuser:
   ```
   python manage.py createsuperuser
   ```


7. Run the development server:
   ```
   python manage.py runserver
   ```


## Usage

- Access the admin interface at `http://localhost:8000/admin/`
- API endpoints are available at `http://localhost:8000/api/`
- Obtain JWT tokens at `http://localhost:8000/api/token/`
- Refresh JWT tokens at `http://localhost:8000/api/token/refresh/`

## API Endpoints

All endpoints require authentication. Use Basic Auth or Session Auth for testing purposes.

### User Registration and Profile

- `POST /api/users/register`: Register a new user
  - Required fields: `name`, `phone_number`, `password`
  - Optional fields: `email`

- `GET | PUT | PATCH | DELETE /api/users/profile/`: for current user's profile


### Contacts

- `GET /api/contacts/`: List user's contacts (paginated)
- `POST /api/contacts/`: Add a new contact
  - Required fields: `name`, `phone_number`
  - Optional fields: `email`
- `GET /api/contacts/{id}/`: Get a specific contact
- `PUT /api/contacts/{id}/`: Update a specific contact
- `DELETE /api/contacts/{id}/`: Delete a specific contact

### Spam Reports

- `GET /api/spam-reports/`: List user's spam reports
- `POST /api/spam-reports/`: Report a number as spam
  - Required field: `phone_number`
- `DELETE /api/spam-reports/{id}/`: Remove a spam report

### Search

- `GET /api/search/by_name/?name={query}`: Search for a person by name
  - Returns: `name`, `phone_number`, `spam_likelihood` for each result
  - Results are paginated and sorted by relevance

- `GET /api/search/by_phone/?phone_number={query}`: Search for a person by phone number `+=p or -=m for phone number in query`
  - Returns: `name`, `phone_number`, `spam_likelihood`, `email` (if applicable) for each result
  - Results are paginated

  - `GET /api/search/{phone_number}/details/`:

  
