from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework import serializers
from kanban_app.models import Board, User, Task

User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']

    def get_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class BoardListSerializer(serializers.ModelSerializer):
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
        fields = ['id', 'title', 'member_count', 'ticket_count',
                  'tasks_to_do_count', 'tasks_high_prio_count', 'owner_id', 'members']

    def create(self, validated_data):
        members = validated_data.pop('members', [])
        board = Board.objects.create(
            owner=self.context['request'].user, **validated_data)
        if members:
            board.members.add(*members)
        return board

    def get_member_count(self, obj):
        return obj.members.count()

    def get_ticket_count(self, obj):
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        return obj.tasks.filter(status='To-Do').count()

    def get_tasks_high_prio_count(self, obj):
        return obj.tasks.filter(status='High').count()


class TaskSerializerForBoardDetail(serializers.ModelSerializer):
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
    members = UserMiniSerializer(many=True)
    tasks = TaskSerializerForBoardDetail(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'title', 'owner_id', 'members', 'tasks']


class BoardUpdateSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all()
    )

    class Meta:
        model = Board
        fields = ['title', 'members']

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        if 'members' in validated_data:
            instance.members.set(validated_data['members'])
        instance.save()
        return instance


class TaskListSerializer(serializers.ModelSerializer):
    assignee_id = serializers.IntegerField(write_only=True)
    reviewer_id = serializers.IntegerField(write_only=True)

    assignee = UserMiniSerializer(read_only=True)
    reviewer = UserMiniSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id', 'board', 'title', 'description', 'status',
                  'priority', 'assignee_id', 'reviewer_id', 'assignee', 'reviewer', 'due_date', 'comments_count']

    def get_comments_count(self, obj):
        return obj.comments.count()

    def create(self, validated_data):
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)

        if assignee_id is not None:
            try:
                validated_data['assignee'] = User.objects.get(id=assignee_id)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {'assignee_id': 'User not found.'})

        if reviewer_id is not None:
            try:
                validated_data['reviewer'] = User.objects.get(id=reviewer_id)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {'reviewer_id': 'User not found.'})

        return Task.objects.create(**validated_data)
