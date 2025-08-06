# Kanban Board Project

## Overview

This project is a Kanban Board application built with Django and Django REST Framework. It allows users to create boards, manage tasks with different statuses and priorities, assign tasks to members, and comment on tasks. The system includes fine-grained permissions for owners, members, and task assignees.

## Features

- User authentication and authorization
- Boards with owners and members
- Task management with priority and status
- Task assignment and review
- Commenting system on tasks
- Permissions to restrict actions based on roles

## Installation & Setup

### Prerequisites

- Python 3.8+
- pip
- virtualenv (recommended)
- Git

### Steps

1. Clone the repository

   ```bash
   git clone https://github.com/ereit673/backend-kanban.git
   cd backend-kanban

   ```

2. Create and activate a virtual environment

   ```bash
   python3 -m venv venv
   source venv/bin/activate # On Windows use: venv\Scripts\activate
   ```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Set up environment variables
   Create a .env file (or configure your environment) with necessary settings such as:

   - SECRET_KEY

   - DATABASE_URL or configure settings.py database section accordingly

5. Apply migrations

```bash
python manage.py migrate
```

6. Create a superuser

```bash
python manage.py createsuperuser
```

7. Run the development server

```bash
python manage.py runserver
```

8. Access the app

- API Root: http://localhost:8000/api/
- Admin panel: http://localhost:8000/admin/

## Usage

- Register users or create users via admin panel.

- Create boards and add members.

- Create tasks within boards and assign users.

- Use API endpoints with authentication to manage boards, tasks, and comments.

## Important Notes

- Permissions are strictly enforced:

- Only owners can delete boards.

- Only board members can create and update tasks.

- Comments can be created and deleted only by board members, and deletion is restricted to comment authors.

- Task updates cannot change the associated board.

- The project uses custom permissions classes for fine control over access.

- All API views require authentication.

- Serializer context includes the request for dynamic fields or permissions.
