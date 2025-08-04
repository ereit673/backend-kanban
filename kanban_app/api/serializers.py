from rest_framework import generics
from rest_framework import serializers
from kanban_app.models import Board, User, Task


class BoardListSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField(read_only=True)
    ticket_count = serializers.SerializerMethodField(read_only=True)
    tasks_to_do_count = serializers.SerializerMethodField(read_only=True)
    tasks_high_prio_count = serializers.SerializerMethodField(read_only=True)
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'title', 'member_count', 'ticket_count',
                  'tasks_to_do_count', 'tasks_high_prio_count', 'owner_id']

    def get_member_count(self, obj):
        return obj.members.count()

    def get_ticket_count(self, obj):
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        return obj.tasks.filter(status='To-Do').count()

    def get_tasks_high_prio_count(self, obj):
        return obj.tasks.filter(status='High').count()


class UserMiniSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']

    def get_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


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
    # owner_id = serializers.IntegerField(source='owner.id')

    class Meta:
        model = Board
        fields = ['id', 'title', 'owner_id', 'members', 'tasks']
