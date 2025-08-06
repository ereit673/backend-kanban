from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Board(models.Model):
    """
    Represents a Kanban board which contains tasks and has an owner and members.

    Attributes:
        title (str): The title of the board.
        owner (User): The user who owns the board.
        members (QuerySet[User]): Users who are members of the board and can collaborate on tasks.
    """
    title = models.CharField(max_length=255)
    owner = models.ForeignKey(
        User, related_name='owned_boards', on_delete=models.CASCADE)
    members = models.ManyToManyField(User, related_name='boards')

    def __str__(self):
        """
        Returns a string representation of the board, which is its title.
        """
        return self.title


class Task(models.Model):
    """
    Represents a task within a board.

    Attributes:
        title (str): Title of the task.
        description (str): Optional detailed description of the task.
        priority (str): Priority level of the task; choices are low, medium, high.
        status (str): Current status of the task; choices include to-do, in-progress, review, done.
        due_date (date): Optional due date for the task.
        board (Board): The board to which this task belongs.
        assignee (User): User assigned to complete the task (optional).
        reviewer (User): User assigned to review the task (optional).
        owner (User): User who created/owns the task.
    """
    PRIORITY_CHOICES = [
        ('low', 'low'),
        ('medium', 'medium'),
        ('high', 'high')
    ]

    STATUS_CHOICES = [
        ('to-do', 'to-do'),
        ('in-progress', 'in-progress'),
        ('review', 'review'),
        ('done', 'done'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='to-do')
    due_date = models.DateField(null=True, blank=True)
    board = models.ForeignKey(
        Board, related_name='tasks', on_delete=models.CASCADE)
    assignee = models.ForeignKey(
        User, related_name='assigned_tasks', null=True, blank=True, on_delete=models.SET_NULL)
    reviewer = models.ForeignKey(
        User, related_name='review_tasks', null=True, blank=True, on_delete=models.SET_NULL)
    owner = models.ForeignKey(
        User, related_name='owned_tasks', on_delete=models.CASCADE)

    def __str__(self):
        """
        Returns a string representation of the task, which is its title.
        """
        return self.title


class Comment(models.Model):
    """
    Represents a comment made by a user on a task.

    Attributes:
        task (Task): The task to which this comment belongs.
        author (User): The user who authored the comment.
        created_at (datetime): Timestamp when the comment was created.
        content (str): Text content of the comment.
    """
    task = models.ForeignKey(
        Task, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(
        User, related_name='comments', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

    def __str__(self):
        """
        Returns a string representation of the comment including author and task title.
        """
        return f"Comment by {self.author.username} on {self.task.title}"
