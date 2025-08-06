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
   git clone https://github.com/yourusername/yourrepo.git
   cd yourrepo

   ```

2. Create and activate a virtual environment
   python3 -m venv venv
   source venv/bin/activate # On Windows use: venv\Scripts\activate

3. Install dependencies
   pip install -r requirements.txt
