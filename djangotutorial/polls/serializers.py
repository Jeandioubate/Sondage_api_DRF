from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import Question, Choice


# --- Visiteur : sondages et choix, sans les votes ---
class ChoicePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'choice_text']


class QuestionPublicSerializer(serializers.ModelSerializer):
    choices = ChoicePublicSerializer(many=True, read_only=True, source='choice_set')

    class Meta:
        model = Question
        fields = ['id', 'question_text', 'pub_date', 'choices']


# --- Utilisateur enregistré : lecture avec votes + création ---
class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'choice_text', 'votes']
        read_only_fields = ['id', 'votes']   # impossible de fixer les votes à la création


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, source='choice_set')
    pub_date = serializers.DateTimeField(required=False)   # défaut : maintenant

    class Meta:
        model = Question
        fields = ['id', 'question_text', 'pub_date', 'choices']

    def validate_choices(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Un sondage doit avoir au moins 2 choix.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        # avec source='choice_set', la clé validée est 'choice_set'
        choices_data = validated_data.pop('choice_set')
        validated_data.setdefault('pub_date', timezone.now())
        question = Question.objects.create(**validated_data)
        for choice_data in choices_data:
            Choice.objects.create(question=question, **choice_data)
        return question