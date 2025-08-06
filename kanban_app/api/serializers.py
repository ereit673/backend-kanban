from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied

from kanban_app.models import Board, Task, Comment

from user_auth_app.api.serializers import UserMiniSerializer

User = get_user_model()


class BoardRelatedField(serializers.PrimaryKeyRelatedField):
    """
    Custom PrimaryKeyRelatedField to handle Board lookups.
    Raises NotFound exception if board does not exist.
    """

    def to_internal_value(self, data):
        """
        Convert input data to internal Board instance or raise NotFound.
        """
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError:
            raise NotFound("Board not found")


class BoardListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing Board instances with counts and member management.
    """

    member_count = serializers.SerializerMethodField(read_only=True)
    ticket_count = serializers.SerializerMethodField(read_only=True)
    tasks_to_do_count = serializers.SerializerMethodField(read_only=True)
    tasks_high_prio_count = serializers.SerializerMethodField(read_only=True)
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Board
        fields = [
            'id', 'title', 'member_count', 'ticket_count',
            'tasks_to_do_count', 'tasks_high_prio_count', 'owner_id', 'members'
        ]

    def create(self, validated_data):
        """
        Create a new Board instance, assign owner and members.
        """
        members = validated_data.pop('members', [])
        board = Board.objects.create(
            owner=self.context['request'].user, **validated_data)
        if members:
            board.members.add(*members)
        return board

    def get_member_count(self, obj):
        """
        Return count of members assigned to the board.
        """
        return obj.members.count()

    def get_ticket_count(self, obj):
        """
        Return total number of tasks (tickets) on the board.
        """
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        """
        Return count of tasks with status 'To-Do' on the board.
        """
        return obj.tasks.filter(status='To-Do').count()

    def get_tasks_high_prio_count(self, obj):
        """
        Return count of tasks with priority 'High' on the board.
        """
        return obj.tasks.filter(status='High').count()


class TaskSerializerForBoardDetail(serializers.ModelSerializer):
    """
    Serializer for task details in the context of a board detail view.
    Includes nested user serializers for assignee and reviewer, and comments count.
    """

    assignee = UserMiniSerializer()
    reviewer = UserMiniSerializer()
    comments_count = serializers.IntegerField(
        source='comments.count', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'assignee', 'reviewer', 'due_date', 'comments_count'
        ]


class BoardDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed Board view including members and nested tasks.
    """

    members = UserMiniSerializer(many=True)
    tasks = TaskSerializerForBoardDetail(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'title', 'owner_id', 'members', 'tasks']


class BoardUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating Board title and members.
    """

    members = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all()
    )

    class Meta:
        model = Board
        fields = ['title', 'members']

    def update(self, instance, validated_data):
        """
        Update board's title and member list.
        """
        instance.title = validated_data.get('title', instance.title)
        if 'members' in validated_data:
            instance.members.set(validated_data['members'])
        instance.save()
        return instance


class TaskListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing and creating Tasks with assignee and reviewer fields.
    Validates user permissions for board membership.
    """

    assignee_id = serializers.IntegerField(write_only=True)
    reviewer_id = serializers.IntegerField(write_only=True)
    board = BoardRelatedField(queryset=Board.objects.all())
    assignee = UserMiniSerializer(read_only=True)
    reviewer = UserMiniSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'board', 'title', 'description', 'status',
            'priority', 'assignee_id', 'reviewer_id', 'assignee',
            'reviewer', 'due_date', 'comments_count'
        ]

    def get_comments_count(self, obj):
        """
        Return count of comments related to the task.
        """
        return obj.comments.count()

    def create(self, validated_data):
        """
        Create a new Task after resolving assignee and reviewer from IDs.
        """
        validated_data['assignee'] = self.resolve_user(
            validated_data.pop('assignee_id', None), 'assignee_id'
        )
        validated_data['reviewer'] = self.resolve_user(
            validated_data.pop('reviewer_id', None), 'reviewer_id'
        )
        return Task.objects.create(**validated_data)

    def resolve_user(self, user_id, field_name):
        """
        Resolve User instance by ID or raise validation error.
        """
        if user_id is not None:
            try:
                return User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {field_name: 'User not found.'})
        return None

    def validate(self, data):
        """
        Validate that the user creating the task is board owner or member.
        """
        request = self.context['request']
        user = request.user
        board = data.get('board')

        if user != board.owner and user not in board.members.all():
            raise PermissionDenied(
                "You are not allowed to create tasks for this board.")

        return data

    def validate_assignee_id(self, value):
        """
        Validate that assignee is a member or owner of the board.
        """
        board_id = self.initial_data.get('board')
        board = Board.objects.filter(pk=board_id).first()

        if not board:
            raise NotFound("Board not found.")

        try:
            user = User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Assignee not found.")

        if user != board.owner and user not in board.members.all():
            raise PermissionDenied("Assignee must be a member of the board.")

        return value

    def validate_reviewer_id(self, value):
        """
        Validate that reviewer is a member or owner of the board.
        """
        board = self.initial_data.get('board')
        board = Board.objects.filter(pk=board).first()

        if not board:
            raise NotFound("Board not found.")

        try:
            user = User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Reviewer not found.")

        if user != board.owner and user not in board.members.all():
            raise PermissionDenied("Reviewer must be a member of the board.")

        return value


class TaskDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed Task views and updates with assignee and reviewer management.
    """

    assignee_id = serializers.IntegerField(write_only=True)
    reviewer_id = serializers.IntegerField(write_only=True)

    assignee = UserMiniSerializer(read_only=True)
    reviewer = UserMiniSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'assignee_id', 'reviewer_id', 'assignee', 'reviewer', 'due_date'
        ]

    def update(self, instance, validated_data):
        """
        Update Task fields including assignee and reviewer by ID.
        """
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)

        if assignee_id is not None:
            try:
                instance.assignee = User.objects.get(id=assignee_id)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {'assignee_id': 'User not found.'})

        if reviewer_id is not None:
            try:
                instance.reviewer = User.objects.get(id=reviewer_id)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {'reviewer_id': 'User not found.'})

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class CommentListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing Comments with author name.
    """

    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'created_at', 'author', 'content']
        read_only_fields = ['id', 'created_at', 'author']

    def get_author(self, obj):
        """
        Return the full name of the comment author or fallback to string representation.
        """
        first_name = getattr(obj.author, 'first_name', '')
        last_name = getattr(obj.author, 'last_name', '')
        fullname = f"{first_name} {last_name}".strip()
        return fullname if fullname else str(obj.author)
